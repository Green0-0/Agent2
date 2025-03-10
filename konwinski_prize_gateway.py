"""Gateway notebook for https://www.kaggle.com/competitions/konwinski-prize"""

import concurrent.futures
import dataclasses
import enum
import io
import os

import shutil
import subprocess
import tempfile


from pathlib import Path

import polars as pl

import kaggle_evaluation.core.base_gateway
import kaggle_evaluation.core.templates
from kaggle_evaluation.core.base_gateway import GatewayRuntimeError, GatewayRuntimeErrorType

COMPETITION_DIR = "/kaggle/input/konwinski-prize/"


def _install_kprize():
    setup_dir = os.path.join(os.path.dirname(__file__), '..', 'kprize_setup')
    whl_file = "kprize-1.1.1-py3-none-any.whl"
    wheel_path = os.path.join(setup_dir, whl_file)
    runner_wheel_path = os.path.join(COMPETITION_DIR, 'kprize_setup', whl_file)
    if os.path.exists(wheel_path):
        pass
    elif os.path.exists(runner_wheel_path):
        wheel_path = runner_wheel_path
    else:
        raise GatewayRuntimeError(
            GatewayRuntimeErrorType.GATEWAY_RAISED_EXCEPTION,
            whl_file
        )

    running_on_kaggle = len([i for i in os.environ if i.lower().startswith('kaggle')]) > 4
    if running_on_kaggle:
        # Install command that works without internet but makes assumptions about existing installed packages.
        subprocess.run(
            f"pip install {wheel_path} -q --no-index --find-links {os.path.join(setup_dir, 'pip_packages/kprize')}",
            shell=True,
            check=True
        )
    else:
        # Install command that requires internet.
        subprocess.run(f"pip install {wheel_path} -q", shell=True, check=True)

try:
    from swebench.harness.test_spec import (SWEbenchInstance, TestSpec)
except ImportError:
    _install_kprize()
    from swebench.harness.test_spec import (SWEbenchInstance, TestSpec)

import unidiff

from kprize.constants import (
    KEY_TEST_PATCH, KEY_INSTANCE_ID,
)
from kprize.dataclass_utils import asdict_factory
from kprize.evaluation.kprize_env_handler import KprizeEnvHandler
from kprize.evaluation.utils import (
    get_kprize_eval_report,
    run_commands,
)
from kprize.harness.pip_env_manager import (
    PipEnvManager,
    PipEnvManagerType,
)
from kprize.harness.pytest_log_parser import TestStatus
from kprize.harness.test_spec_creator import TestSpecCreator
from kprize.collection.configs.repo_config import RepoConfig

# We need a competition-specific string that can map to null.
# Kaggle's metric orchestrator does not allow submission files to contain nulls.
# This includes strings that Pandas/Polars will parse as null, such as N/A.
NULL_FOR_SUBMISSION = "null_replacement"


class UnitTestOutcome(enum.Enum):
    UNKNOWN = "unknown"
    PASSED = "passed"
    FAILED = "failed"


class PredictOutcome(enum.Enum):
    SKIP = "skip"
    ATTEMPT = "attempt"


class RowType(enum.Enum):
    PATCH = "patch"
    UNIT_TEST = "unit_test"
    RAW_PYTEST_OUTPUT = "raw_pytest_output"


def is_valid_patch_format(patch: str) -> bool:
    """
    A quick check to confirm if a patch could be valid.
    """
    if not(isinstance(patch, str)):
        return False
    try:
        patch_set = unidiff.PatchSet(patch)
        if len(patch_set) == 0:
            return False
    except Exception:
        return False
    return True


def patch_dry_run_succeeds(patch_path: Path, repo_path: Path, timeout: int=60) -> bool:
    """
    A robust check if the patch will proceed without any errors.
    Should be run after `is_valid_patch_format()`: the patch
    command can hang if the inputs are sufficiently invalid.

    Args:
        patch_path: Path to a file containing the patch.
        repo_path: Path to the directory to be patched.
        timeout: Number of seconds before the dry run will be cancelled.
    """
    cmd = f"patch --quiet --dry-run -p1 -i {patch_path} -d {repo_path}"
    try:
        subprocess.run(cmd, shell=True, check=True, timeout=timeout)
        return True
    except subprocess.CalledProcessError:
        return False


@dataclasses.dataclass
class SubmissionRow:
    row_id: str = dataclasses.field(init=False)
    instance_id: str
    test_name: str | None
    row_type: RowType
    unit_test_outcome: UnitTestOutcome | None
    predict_outcome: PredictOutcome | None
    patch: str | None
    fail_description: str | None
    test_output: str | None

    def __post_init__(self):
        self.row_id = f"{self.instance_id}_{self.row_type.value}_{self.test_name}"

    def to_dict(self):
        return dataclasses.asdict(self, dict_factory=asdict_factory)

    @staticmethod
    def schema():
        return {
            "row_id": pl.Utf8,
            "instance_id": pl.Utf8,
            "test_name": pl.Utf8,
            "row_type": pl.Utf8,
            "unit_test_outcome": pl.Utf8,
            "predict_outcome": pl.Utf8,
            "patch": pl.Utf8,
            "fail_description": pl.Utf8,
            "test_output": pl.Utf8,
        }


class KPrizeGateway(kaggle_evaluation.core.templates.Gateway):
    APPLICABLE_TEST_STATUSES = {TestStatus.FAILED, TestStatus.ERROR, TestStatus.PASSED, None}

    def __init__(self, data_paths: tuple[str, str] | None = None, file_share_dir: str=None, use_concurrency=True):
        super().__init__(data_paths, file_share_dir)
        self.set_response_timeout_seconds(30 * 60)
        self._verbose = False
        self.use_concurrency = use_concurrency

    def validate_prediction_batch(
            self,
            patch: str,
            row_ids: pl.Series=None
    ):
        # This competition is unusual in accepting null predictions.
        if not isinstance(patch, str) and patch is not None:
            raise GatewayRuntimeError(GatewayRuntimeErrorType.INVALID_SUBMISSION,
                f"Invalid patch type: {type(patch)}. The patch should be a string."
                " If you want to skip the instance, use an empty string or None."
            )

    def unpack_data_paths(self):
        if self.data_paths:
            self.input_dir, self.temp_dir = self.data_paths
        else:
            self.input_dir = COMPETITION_DIR
            self.temp_dir = "/kaggle/tmp/konwinski-prize/"
        temp_data_dir = os.path.join(self.temp_dir, 'data')
        if os.path.exists(temp_data_dir):
            shutil.rmtree(temp_data_dir)
        os.makedirs(self.temp_dir, exist_ok=True)
        self._kprize_env_handler = KprizeEnvHandler(self.input_dir, self.temp_dir, verbose=self._verbose)

        shutil.unpack_archive(
            os.path.join(self.input_dir, 'data.a_zip'),
            self.temp_dir,
            format='zip'
        )

        self.metadata_path = os.path.join(temp_data_dir, 'data.parquet')
        self.pip_packages_dir = os.path.join(temp_data_dir, 'pip_packages')
        self.repo_config_dir = os.path.join(temp_data_dir, 'repo_configs')
        self.repo_dir = os.path.join(temp_data_dir, 'repos')

        self._pip_env_manager = PipEnvManager(
            manager=PipEnvManagerType.UV,
            python_version="3.11"
        )
        self._kprize_env_handler.setup_uv()
        self._kprize_env_handler.setup_python311()

    def _prepare_evaluation_env(
        self,
        env_commands: list[str],
        repo_commands: list[str],
    ) -> None:
        """Create and activate the evaluation environment."""
        run_commands(env_commands)
        run_commands(repo_commands)

    def _map_test_status_to_outcome(self, test_status: TestStatus | None) -> UnitTestOutcome:
        match test_status:
            case TestStatus.PASSED:
                return UnitTestOutcome.PASSED
            case TestStatus.FAILED | TestStatus.ERROR | None:
                return UnitTestOutcome.FAILED
            case TestStatus.SKIPPED | TestStatus.XFAIL:
                return UnitTestOutcome.UNKNOWN
            case _:
                raise GatewayRuntimeError(GatewayRuntimeErrorType.GATEWAY_RAISED_EXCEPTION, f"Invalid test status: {test_status}")

    def _get_repo_config_path(self, instance_id: str) -> str:
        return os.path.join(self.repo_config_dir, RepoConfig.map_instance_id_to_repo_stem(instance_id) + '.json')

    def _run_tests(self, instance: SWEbenchInstance, test_spec: TestSpec) -> list[SubmissionRow]:
        """Run unit tests and return the results, including any errors and error messages."""
        instance_id = instance["instance_id"]
        eval_commands = test_spec.eval_script_list
        test_output_path = self._kprize_env_handler.get_test_output_path(instance_id)

        run_commands(eval_commands, filepath=test_output_path)

        unit_tests_info = get_kprize_eval_report(
            test_output_path=test_output_path,
            repo_config_path=self._get_repo_config_path(instance[KEY_INSTANCE_ID]),
        )

        if unit_tests_info is None:
            return []

        results = []
        for test_name, test_info in unit_tests_info.test_info_map.items():
            if test_info.status not in self.APPLICABLE_TEST_STATUSES:
                continue
            results.append(SubmissionRow(
                instance_id=instance_id,
                test_name=test_name,
                row_type=RowType.UNIT_TEST,
                unit_test_outcome=self._map_test_status_to_outcome(test_info.status),
                predict_outcome=PredictOutcome.ATTEMPT,
                patch=None,
                fail_description=test_info.failed_description,
                test_output=test_info.test_output,
            ))
        return results

    def _tear_down_env(self) -> None:
        """Restore the base environment."""
        if self._verbose:
            print("Tearing down instance environment...")
        run_commands(
            [
                f"rm -rf {self._kprize_env_handler.get_test_bed_path()}",
            ]
            + self._pip_env_manager.global_env_remove_cmds,
        )

    def _get_instance_test_output_row(self, instance_id: str) -> SubmissionRow:
        row = SubmissionRow(
            instance_id=instance_id,
            test_name=None,
            row_type=RowType.RAW_PYTEST_OUTPUT,
            unit_test_outcome=None,
            predict_outcome=None,
            patch=None,
            fail_description=None,
            test_output=None,
        )

        test_output_path = self._kprize_env_handler.get_test_output_path(instance_id)
        if test_output_path.exists():
            row.test_output = test_output_path.read_text()

        return row

    def _is_patch_dry_run_successful(self, instance_id: str, patch_path: Path) -> bool:
        repo_path = Path(self.repo_dir) / f"repo__{instance_id}"
        return patch_dry_run_succeeds(patch_path, repo_path)

    def _evaluate_instance(self, instance: dict, patch: str) -> list[SubmissionRow]:
        swe_bench_instance = SWEbenchInstance(**instance)
        instance_id = instance["instance_id"]

        # Write test patch to file
        test_patch_path = self._kprize_env_handler.get_test_patch_path(instance_id)
        test_patch_path.parent.mkdir(parents=True, exist_ok=True)
        test_patch_path.write_text(instance[KEY_TEST_PATCH])

        # Write model patch to file
        model_patch_path = self._kprize_env_handler.get_model_patch_path(instance_id)
        model_patch_path.parent.mkdir(parents=True, exist_ok=True)
        model_patch_path.write_text(patch)

        if not self._is_patch_dry_run_successful(instance_id, model_patch_path):
            return [
                SubmissionRow(
                    instance_id=instance_id,
                    test_name="invalid_patch",
                    row_type=RowType.UNIT_TEST,
                    predict_outcome=PredictOutcome.ATTEMPT,
                    patch=None,
                    unit_test_outcome=UnitTestOutcome.FAILED,
                    fail_description=None,
                    test_output=None,
                )
            ]

        # create a dedicated manager to avoid any threading issues
        pip_env_manager = PipEnvManager(
            manager=self._pip_env_manager.manager,
            python_version=self._pip_env_manager.python_version,
            local_pip_packages_dir=self.pip_packages_dir,
        )

        test_spec_creator = TestSpecCreator(
            pip_env_manager=pip_env_manager,
            instance_repos_dir=self.repo_dir,
            repo_config_dir=self.repo_config_dir,
            disable_apt_install=True,
            reset_tests_after_eval=False,
        )

        test_spec = test_spec_creator.make_test_spec(
            swe_bench_instance,
            test_patch_path=test_patch_path,
            model_patch_path=model_patch_path,
        )

        self._prepare_evaluation_env(
            env_commands=test_spec.env_script_list,
            repo_commands=test_spec.repo_script_list,
        )
        rows = self._run_tests(
            instance=swe_bench_instance,
            test_spec=test_spec
        )

        instance_test_output_row = self._get_instance_test_output_row(instance_id)

        self._tear_down_env()

        return [instance_test_output_row, *rows]

    def get_number_of_instances(self, instance_count: int):
        ''' Send competitors the total number of instances they will receive so the can calibrate inference time.
        '''
        try:
            self.client.send('get_number_of_instances', instance_count)
        except Exception as e:
            self.handle_server_error(e, 'get_number_of_instances')

    def generate_data_batches(self):
        """ Yields an instance dict and the path to the relevant repo
        """
        df = pl.read_parquet(self.metadata_path)
        self.get_number_of_instances(df["instance_id"].n_unique())


        df = df.drop(['pull_number'])
        for idx in range(len(df)):
            # Extract a single row of the DataFrame as a dict
            instance = df.row(idx, named=True)
            repo_path = os.path.join(self.repo_dir, f"repo__{instance['instance_id']}")
            pip_packages_path = os.path.join(self.pip_packages_dir, instance['instance_id'])
            yield instance, repo_path, pip_packages_path

    def submission_rows_to_df(self, rows: SubmissionRow | list[SubmissionRow]) -> pl.DataFrame:
        if isinstance(rows, SubmissionRow):
            df = pl.DataFrame(rows.to_dict(), schema=SubmissionRow.schema())
        else:
            df = pl.DataFrame(
            map(SubmissionRow.to_dict, rows),
            schema=SubmissionRow.schema(),
            )
        for col in df.columns:
            # Nulls in the ID columns need to be retained to trigger the correct errors
            # and avoid misalignment with the solution.
            if col.endswith("id"):
                continue
            # polars.fill_null only works as intended if the fill value has the same type
            # as the existing column.
            df = df.with_columns(pl.col(col).cast(pl.Utf8).fill_null(NULL_FOR_SUBMISSION))
        return df



    def get_all_predictions(self):
        if self.use_concurrency:
            executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
            futures = []
        all_instance_ids = []
        all_predictions = []
        for instance, repo_path, pip_packages_path in self.generate_data_batches():
            # TODO: restore?
            # patch = self.predict(
            #     instance["problem_statement"],
            #     self.share_files([repo_path]),
            # )

            # Backup for share_files
            with tempfile.TemporaryDirectory() as tmpdir:
                # instance repo
                shutil.make_archive(os.path.join(tmpdir, 'a_repo'), 'tar', repo_path)
                with open(os.path.join(tmpdir, 'a_repo.tar'), 'rb') as f:
                    repo_buffer = io.BytesIO(f.read())
                # instance pip packages
                shutil.make_archive(os.path.join(tmpdir, 'a_pip_packages_dir'), 'tar', pip_packages_path)
                with open(os.path.join(tmpdir, 'a_pip_packages_dir.tar'), 'rb') as f:
                    pip_packages_buffer = io.BytesIO(f.read())

            # get env setup commands
            repo_config_path = self._get_repo_config_path(instance["instance_id"])
            env_setup_cmd_templates = self._kprize_env_handler.get_env_setup_cmds_templates(repo_config_path)

            patch = self.predict(
                instance["problem_statement"],
                repo_buffer,
                pip_packages_buffer,
                env_setup_cmd_templates
            )

            self.validate_prediction_batch(
                patch,
                pl.Series([instance["instance_id"]]),
            )

            if (isinstance(patch, str) and patch == "") or patch is None:
                patch = None  # Ensure fill_null will cover this instance later.
                predict_outcome = PredictOutcome.SKIP
            else:
                predict_outcome = PredictOutcome.ATTEMPT

            patch_row = SubmissionRow(
                instance_id=instance["instance_id"],
                test_name=None,
                row_type=RowType.PATCH,
                predict_outcome=predict_outcome,
                patch=patch,  # type: ignore (we validated it above)
                unit_test_outcome=None,
                fail_description=None,
                test_output=None,
            )
            patch_df = self.submission_rows_to_df(patch_row)
            rows = patch_df

            if predict_outcome == PredictOutcome.ATTEMPT:
                if is_valid_patch_format(patch):
                    if self.use_concurrency:
                        futures.append(executor.submit(self._evaluate_instance, instance, patch))
                    else:
                        unit_test_rows = self._evaluate_instance(
                            instance=instance,
                            patch=patch  # type: ignore (we validated it above)
                        )
                else:
                    unit_test_rows = SubmissionRow(
                        instance_id=instance["instance_id"],
                        test_name="invalid_patch",
                        row_type=RowType.UNIT_TEST,
                        predict_outcome=predict_outcome,
                        patch=None,
                        unit_test_outcome=UnitTestOutcome.FAILED,
                        fail_description=None,
                        test_output=None,
                    )

                if not self.use_concurrency or not is_valid_patch_format(patch):
                    unit_test_df = self.submission_rows_to_df(unit_test_rows)
                    rows = pl.concat([patch_df, unit_test_df], how="vertical_relaxed")

            all_predictions.append(rows)
            all_instance_ids.append(instance["instance_id"])

        if self.use_concurrency:
            executor.shutdown(wait=True)  # Block until all tasks are done
            unit_test_dfs = [self.submission_rows_to_df(i.result()) for i in futures]
            # An empty list can arise here in the skip all case
            if unit_test_dfs:
                rows = pl.concat(unit_test_dfs, how="vertical_relaxed")
                all_predictions.append(rows)

        return all_predictions, all_instance_ids

    def write_submission(self, predictions, row_ids):

        # This competition needs csv files instead of parquet.
        if isinstance(predictions, list):
            predictions = pl.concat(predictions, how='vertical_relaxed')
        predictions.write_csv('submission.csv')


if __name__ == "__main__":
    if os.getenv("KAGGLE_IS_COMPETITION_RERUN"):
        gateway = KPrizeGateway()
        # Relies on valid default data paths
        gateway.run()
    else:
        print("Skipping run for now")

import json
import os
import subprocess
from pathlib import Path

from kprize.evaluation.utils import run_commands
from kprize.harness.python_manager import PythonManager
from kprize.harness.uv_manager import UVManager
from kprize.constants import TESTBED_DIR


class KprizeEnvHandler:
    def __init__(self, input_dir, temp_dir: str, verbose: bool = False):
        self.output_dir = Path(os.path.join(temp_dir, 'output'))
        self._kprize_setup_assets_input_dir = Path(os.path.join(input_dir, 'kprize_setup'))
        # print(f"KprizeEnvHandler: kprize_setup_assets_input_dir: {self._kprize_setup_assets_input_dir}")
        self._verbose = verbose

    @staticmethod
    def is_running_on_kaggle():
        return len([i for i in os.environ if i.lower().startswith('kaggle')]) > 4

    def get_test_patch_path(self, instance_id: str) -> Path:
        return self.output_dir / f"test_patch_{instance_id}.diff"

    def get_model_patch_path(self, instance_id: str) -> Path:
        return self.output_dir / f"model_patch_{instance_id}.diff"

    def get_test_output_path(self, instance_id: str) -> Path:
        return self.output_dir / f"test_output_{instance_id}.txt"

    def get_test_bed_path(self) -> Path:
        """Get a full path for a test bed."""
        return Path(TESTBED_DIR)

    def setup_uv(self):
        uv_result = subprocess.run('which uv', shell=True, capture_output=True)
        if uv_result.returncode not in [0, 1]:
            raise ValueError(f"subprocess.run('which uv' returned unexpected exit code {uv_result.returncode}")
        is_uv_installed = (uv_result.stdout and uv_result.stdout.decode()) and not (uv_result.stderr and uv_result.stderr.decode())
        if is_uv_installed:
            print('Existing uv installation found. Skipping uv installation.')
            return None
        print('Installing uv...')
        uv_manager = UVManager(Path("/usr/local/bin"))
        run_commands(
            uv_manager.install_offline_cmds(self._kprize_setup_assets_input_dir / "uv", "uv*")
        )
        uv_result = subprocess.run('which uv', shell=True, capture_output=True)
        if uv_result.returncode != 0:
            print(f"WARNING: uv returned non-zero code. Installation may have failed. code: {uv_result.returncode}")
        if self._verbose:
            print("uv setup finished.")

    def setup_python311(self):
        python311_result = subprocess.run('which python3.11', shell=True, capture_output=True)
        if python311_result.returncode not in [0, 1]:
            raise ValueError(f"subprocess.run('which python3.11' returned unexpected exit code {python311_result.returncode}")
        is_python311_installed = (python311_result.stdout and python311_result.stdout.decode()) and not (python311_result.stderr and python311_result.stderr.decode())
        if is_python311_installed:
            # print('Existing Python 3.11 installation found. Skipping Python 3.11 installation.')
            return None
        print('Installing Python 3.11...')
        python_manager = PythonManager()
        ubuntu_version = python_manager.get_ubuntu_version()
        run_commands(
            python_manager.install_offline_cmds(self._kprize_setup_assets_input_dir / "python3.11", ubuntu_version)
        )
        # Skip verifying installation: uv installs Python 3.11 in a location not visible to `which`
        if self._verbose:
            print("Python 3.11 setup finished.")

    @staticmethod
    def get_env_setup_cmds_templates(repo_config_path: Path | str) -> list[str]:
        python_exec = "python3.11"
        uv_env_cmds = [
            f"uv venv --python {python_exec}",
            "source .venv/bin/activate"
        ]
        # default env setup commands in case of missing specs
        default_env_setup_cmds = uv_env_cmds + [
            "uv pip install --no-index --find-links={pip_packages_path} -e .",
        ]

        repo_config_path = Path(repo_config_path)
        if not repo_config_path.exists():
            # error: repo config does not exist
            return default_env_setup_cmds

        repo_config = json.loads(repo_config_path.read_text())
        specs = repo_config["specs"]

        if not specs.get("default", None):
            # error: no default install command in repo config
            return default_env_setup_cmds

        cmd_install = specs["default"]["install"]

        # add extra pip packages
        extra_pip_packages = specs["default"].get("pip_packages", None)
        if extra_pip_packages:
            cmd_install = f"{cmd_install} && pip install {' '.join(extra_pip_packages)}"

        # set env vars
        cmd_env_vars = specs["default"].get("env_vars", None)
        if cmd_env_vars:
            env_vars = ' '.join(list(cmd_env_vars))
            cmd_install = ' && '.join(map(lambda c: f"{env_vars} {c}", cmd_install.split(' && ')))

        # use uv pip instead of pip
        cmd_install = cmd_install.replace("pip install", "uv pip install --link-mode=symlink")
        # remove 'python -m'
        cmd_install = cmd_install.replace('python -m ', '')

        return uv_env_cmds + [
            cmd_install.replace(
            "pip install",
            "pip install --no-index --find-links={pip_packages_path}"
            )
        ]
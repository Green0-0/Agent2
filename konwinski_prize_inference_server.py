
import kaggle_evaluation.core.templates

import konwinski_prize_gateway


class KPrizeInferenceServer(kaggle_evaluation.core.templates.InferenceServer):
    def _get_gateway_for_test(self, data_paths: tuple[str]=None, file_share_dir: str=None, use_concurrency=True):
        return konwinski_prize_gateway.KPrizeGateway(data_paths, file_share_dir, use_concurrency)

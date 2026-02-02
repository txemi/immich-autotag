from typeguard import typechecked

from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper

from .asset_date_corrector import AssetDateCorrector
from .step_result import DateCorrectionStepResult


@typechecked
def correct_asset_date(
    asset_wrapper: AssetResponseWrapper, log_flag: bool = False
) -> DateCorrectionStepResult:
    """
    Main entry point for asset date correction logic.

    This function maintains backward compatibility by delegating to the AssetDateCorrector class.
    For more detailed diagnostics, use AssetDateCorrector directly.

    Args:
        asset_wrapper: The asset to correct
        log_flag: Optional logging flag (passed for compatibility)

    Returns:
        DateCorrectionStepResult indicating the outcome of the correction attempt.
    """
    corrector = AssetDateCorrector(asset_wrapper=asset_wrapper)
    return corrector.execute(log_flag=log_flag)

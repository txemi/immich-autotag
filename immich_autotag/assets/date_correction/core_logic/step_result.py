from enum import Enum, auto


# Enum for control flow in date correction steps
class DateCorrectionStepResult(Enum):

    CONTINUE = auto()  # Continue processing
    EXIT = auto()  # Stop processing, nothing to do
    FIXED = auto()  # Date was fixed, stop processing

    @staticmethod
    def should_exit(result: "DateCorrectionStepResult") -> bool:
        """Return True if the result means processing should exit (FIXED or EXIT)."""
        return result in (DateCorrectionStepResult.FIXED, DateCorrectionStepResult.EXIT)

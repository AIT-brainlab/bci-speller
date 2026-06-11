"""Configuration errors for the EEG visualizer package."""


class VisualizerConfigError(RuntimeError):
    """Raised when required visualizer settings are missing or invalid."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message

# aice_reco/__init__.py
from aice_reco.tracker import RecoTracker
from aice_reco.exceptions import (
    AiceRecoError,
    ConfigurationError,
    APIError,
    ConnectionError,
    ValidationError
)

__version__ = "1.0.0"
__all__ = [
    "RecoTracker",
    "AiceRecoError",
    "ConfigurationError",
    "APIError",
    "ConnectionError",
    "ValidationError"
]
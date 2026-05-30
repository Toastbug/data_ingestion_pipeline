# aice_reco/exceptions.py


class AiceRecoError(Exception):
    """Base exception for all Aice Reco SDK errors."""
    pass


class ConfigurationError(AiceRecoError):
    """
    Raised when the SDK is misconfigured.
    Examples:
    - api_key is missing
    - project_id is missing
    - api_url is invalid
    """
    pass


class APIError(AiceRecoError):
    """
    Raised when the API returns an error response.
    Examples:
    - 422 validation error
    - 500 server error
    """
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message     = message
        super().__init__(f"API error {status_code}: {message}")


class ConnectionError(AiceRecoError):
    """
    Raised when the SDK cannot reach the API.
    Examples:
    - API server is down
    - Wrong api_url
    - Network timeout
    """
    pass


class ValidationError(AiceRecoError):
    """
    Raised when an event has invalid fields
    before it is even sent to the API.
    Examples:
    - Invalid event_type
    - Invalid device
    - Missing required field
    """
    pass
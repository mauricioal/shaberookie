"""Custom exception hierarchy for shaberookie."""


class ShaberookieError(Exception):
    """Base exception for all shaberookie-specific errors."""


class ConfigurationError(ShaberookieError):
    """Raised when configuration loading or validation fails."""


class RenshuuAPIError(ShaberookieError):
    """Raised when the Renshuu API responds with an error."""


class AuthenticationError(RenshuuAPIError):
    """Raised for authentication or authorization issues with Renshuu."""


class RateLimitError(RenshuuAPIError):
    """Raised when hitting Renshuu API rate limits."""


class ProfileNotFoundError(ShaberookieError):
    """Raised when a user profile cannot be located or built."""


class LLMProviderError(ShaberookieError):
    """Raised when an LLM provider returns an error or unexpected payload."""


class ValidationFailure(ShaberookieError):
    """Raised when response validation detects non-conforming outputs."""
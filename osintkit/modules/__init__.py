"""osintkit OSINT modules."""


class ModuleError(Exception):
    """Base exception for module failures."""
    pass


class RateLimitError(ModuleError):
    """Raised when an API rate limit (429) is hit."""
    pass


class InvalidKeyError(ModuleError):
    """Raised when an API key is invalid or unauthorized (401/403)."""
    pass
"""Custom exceptions for tag operations."""


class TagNotFoundError(Exception):
    """Raised when a tag is not found in the collection or map."""

    def __init__(self, tag_name: str, message: str | None = None):
        self.tag_name = tag_name
        if message is None:
            message = f"Tag '{tag_name}' not found"
        super().__init__(message)

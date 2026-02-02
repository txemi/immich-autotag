from __future__ import annotations

from typing import Optional

import attrs


@attrs.define(auto_attribs=True, slots=True)
class AlbumApiExceptionInfo:
    """
    Encapsulates details about an API exception for album operations, including
    the exception object, status code, and message parsing logic.
    """

    exc: Exception
    status_code: Optional[int] = attrs.field(init=False)
    message: str = attrs.field(init=False)

    def _extract_status_code(self) -> Optional[int]:
        # Safely get status_code attribute if present
        status_code = self.exc.status_code if self.exc.status_code is not None else None  # type: ignore[attr-defined]
        if status_code is not None:
            return status_code
        # Fallback: parse from message
        try:
            msg = str(self.exc)
            if "status code: 400" in msg or "Unexpected status code: 400" in msg:
                return 400
            if "status code: 404" in msg or "Unexpected status code: 404" in msg:
                return 404
            # Add more status code patterns as needed
        except Exception:
            pass
        return None

    def __attrs_post_init__(self) -> None:
        self.status_code = self._extract_status_code()
        self.message = str(self.exc)

    def is_status(self, code: int) -> bool:
        return self.status_code == code

    def __str__(self) -> str:
        return (
            f"AlbumApiExceptionInfo(status_code={self.status_code}, "
            f"message={self.message!r})"
        )

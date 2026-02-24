from immich_autotag.albums.album.album_response_wrapper import AlbumResponseWrapper
from immich_autotag.api.immich_proxy.albums.delete_album import (
    proxy_delete_album,
)
from immich_autotag.api.immich_proxy.types import ImmichClient
from immich_autotag.logging.levels import LogLevel
from immich_autotag.logging.utils import log
from immich_autotag.report.modification_entry import ModificationEntry


def logging_delete_album(
    album_wrapper: "AlbumResponseWrapper", reason: str, client: "ImmichClient"
) -> "ModificationEntry":
    pass
    try:
        proxy_delete_album(album_id=album_wrapper.get_album_uuid(), client=client)
    except Exception as exc:
        msg = str(exc)
        # Try to give a more specific reason if possible
        err_reason = "Unknown error"
        from typing import Any, cast

        response = None
        code = None
        # Try to access response and status_code directly, fallback to None
        try:
            response = cast(Any, exc).response
            code = response.status_code if response is not None else None
        except Exception:
            response = None
            code = None
        if code is not None:
            if code == 404:
                err_reason = "Album not found (already deleted)"
            elif code == 400:
                err_reason = "Album not empty or bad request"
            elif code == 403:
                err_reason = "Permission denied"
            else:
                err_reason = f"HTTP {code}"
        else:
            if "not found" in msg.lower():
                err_reason = "Album not found (already deleted)"
            elif "not empty" in msg.lower():
                err_reason = "Album not empty"
            elif "permission" in msg.lower() or "forbidden" in msg.lower():
                err_reason = "Permission denied"
        log(
            f"Failed to delete album "
            f"'{album_wrapper.get_album_name()}' (id={album_wrapper.get_album_uuid()}). "
            f"Reason: {err_reason}. Exception: {msg}",
            level=LogLevel.WARNING,
        )
        if err_reason == "Album not found (already deleted)":
            # Album is already deleted, treat as success
            raise RuntimeError(
                f"Album '{album_wrapper.get_album_name()}' (id={album_wrapper.get_album_uuid()}) "
                "already deleted."
            )
        else:
            raise RuntimeError(
                f"Failed to delete album "
                f"'{album_wrapper.get_album_name()}' (id={album_wrapper.get_album_uuid()}). "
                f"Reason: {err_reason}."
            ) from exc
    from immich_autotag.report.modification_kind import ModificationKind

    # On success, err_reason is not set, so use a default
    from immich_autotag.report.modification_report import ModificationReport

    tag_mod_report = ModificationReport.get_instance()
    report_entry: ModificationEntry = tag_mod_report.add_album_modification(
        kind=ModificationKind.DELETE_ALBUM,
        album=album_wrapper,
        old_value=album_wrapper.get_album_name(),
        extra={"reason": f"{reason} (SUCCESS)"},
    )
    return report_entry

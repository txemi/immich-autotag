from __future__ import annotations

import datetime
from typing import Any, Optional, Union
from urllib.parse import ParseResult
from uuid import UUID

import attrs

from immich_autotag.tags.modification_kind import ModificationKind


@attrs.define(auto_attribs=True, slots=True, frozen=True)
class ModificationEntry:
    datetime: str
    kind: ModificationKind
    asset_id: Optional[UUID] = None
    asset_name: Optional[str] = None
    tag_name: Optional[str] = None
    album_id: Optional[UUID] = None
    album_name: Optional[str] = None
    old_name: Optional[str] = None
    new_name: Optional[str] = None
    user: Optional[str] = None
    link: Optional[str] = None
    extra: Optional[dict[str, Any]] = None


# TODO: la siguiente clase es mas generiga que tag, requiere refactorizar nombre y ubicacion


@attrs.define(auto_attribs=True, slots=True)
class TagModificationReport:

    _instance = None  # Singleton instance
    _instance_created = False  # Class-level flag

    import datetime as dt
    import os

    log_dir: str = attrs.field(
        default="logs", validator=attrs.validators.instance_of(str)
    )
    report_path: str = attrs.field(
        default=f"logs/tag_modification_report_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.getpid()}.txt",
        validator=attrs.validators.instance_of(str),
    )
    batch_size: int = attrs.field(
        default=1, validator=attrs.validators.instance_of(int)
    )
    modifications: list[ModificationEntry] = attrs.field(  # type: ignore
        factory=list, init=False
    )
    _since_last_flush: int = attrs.field(
        default=0, init=False, validator=attrs.validators.instance_of(int)
    )
    _cleared_report: bool = attrs.field(
        default=False,
        init=False,
        repr=False,
        validator=attrs.validators.instance_of(bool),
    )

    def __attrs_post_init__(self):
        cls = self.__class__
        if getattr(cls, "_instance_created", False):
            raise RuntimeError(
                "TagModificationReport instance already exists. Use TagModificationReport.get_instance() instead of creating a new one."
            )
        cls._instance_created = True
        cls._instance = self

    @staticmethod
    def get_instance(*args, **kwargs) -> "TagModificationReport":
        if TagModificationReport._instance is None:
            TagModificationReport(*args, **kwargs)
        return TagModificationReport._instance

    from typeguard import typechecked

    @typechecked
    def add_modification(
        self,
        kind: Union[ModificationKind, str],
        asset_id: Optional[UUID] = None,
        asset_name: Optional[str] = None,
        tag_name: Optional[str] = None,
        album_id: Optional[UUID] = None,
        album_name: Optional[str] = None,
        old_name: Optional[str] = None,
        new_name: Optional[str] = None,
        user: Optional[str] = None,
        extra: Optional[dict[str, Any]] = None,
    ) -> None:
        """
        Registers a modification for any entity (tag, album, assignment, etc.).
        Maintains compatibility with previous usage.
        """
        if not self._cleared_report:
            import os

            try:
                os.makedirs(os.path.dirname(self.report_path), exist_ok=True)
                with open(self.report_path, "w", encoding="utf-8") as f:
                    pass  # Truncate the file
            except Exception as e:
                print(f"[WARN] Could not clear the tag modification report: {e}")
            self._cleared_report = True

        # Permitir str para facilitar migración, pero convertir a Enum
        if isinstance(kind, str):
            kind = ModificationKind[kind]

        # Build link (asset or album)
        link = self._build_link(kind, asset_id, album_id)

        entry = ModificationEntry(
            datetime=datetime.datetime.now().isoformat(),
            kind=kind,
            asset_id=asset_id,
            asset_name=asset_name,
            tag_name=tag_name,
            album_id=album_id,
            album_name=album_name,
            old_name=old_name,
            new_name=new_name,
            user=user,
            link=link,
            extra=extra,
        )
        self.modifications.append(entry)
        self._since_last_flush += 1
        if self._since_last_flush >= self.batch_size:
            self.flush()

    # Métodos específicos para cada tipo de acción
    @typechecked
    def add_tag_modification(
        self,
        kind: ModificationKind,
        asset_id: UUID,
        asset_name: str,
        tag_name: str,
        user: Optional[str] = None,
    ) -> None:
        assert kind in {
            ModificationKind.ADD_TAG_TO_ASSET,
            ModificationKind.REMOVE_TAG_FROM_ASSET,
            ModificationKind.REMOVE_TAG_GLOBALLY,
        }
        self.add_modification(
            kind=kind,
            asset_id=asset_id,
            asset_name=asset_name,
            tag_name=tag_name,
            user=user,
        )

    @typechecked
    def add_album_modification(
        self,
        kind: ModificationKind,
        album_id: UUID,
        album_name: Optional[str] = None,
        old_name: Optional[str] = None,
        new_name: Optional[str] = None,
        user: Optional[str] = None,
    ) -> None:
        assert kind in {
            ModificationKind.CREATE_ALBUM,
            ModificationKind.DELETE_ALBUM,
            ModificationKind.RENAME_ALBUM,
        }
        self.add_modification(
            kind=kind,
            album_id=album_id,
            album_name=album_name,
            old_name=old_name,
            new_name=new_name,
            user=user,
        )

    @typechecked
    def add_assignment_modification(
        self,
        kind: ModificationKind,
        asset_id: UUID,
        asset_name: str,
        album_id: UUID,
        album_name: Optional[str] = None,
        user: Optional[str] = None,
    ) -> None:
        assert kind in {
            ModificationKind.ASSIGN_ASSET_TO_ALBUM,
            ModificationKind.REMOVE_ASSET_FROM_ALBUM,
        }
        self.add_modification(
            kind=kind,
            asset_id=asset_id,
            asset_name=asset_name,
            album_id=album_id,
            album_name=album_name,
            user=user,
        )

    @typechecked
    def flush(self) -> None:
        """Flushes the report to file (append)."""
        if not self.modifications or self._since_last_flush == 0:
            return
        import os

        os.makedirs(os.path.dirname(self.report_path), exist_ok=True)
        with open(self.report_path, "a", encoding="utf-8") as f:
            for entry in self.modifications[-self._since_last_flush :]:
                f.write(self._format_modification_entry(entry) + "\n")
        self._since_last_flush = 0

    @typechecked
    def print_summary(self) -> None:
        print("\n[SUMMARY] Modifications:")
        for entry in self.modifications:
            print(self._format_modification_entry(entry))
        print(f"Total modifications: {len(self.modifications)}")

    @typechecked
    def _build_link(
        self, kind: ModificationKind, asset_id: Optional[UUID], album_id: Optional[UUID]
    ) -> Optional[ParseResult]:
        """
        Build a link for the modification entry based on kind and ids.
        """
        from immich_autotag.utils.helpers import get_immich_photo_url

        if (
            kind
            in {
                ModificationKind.ADD_TAG_TO_ASSET,
                ModificationKind.REMOVE_TAG_FROM_ASSET,
                ModificationKind.REMOVE_TAG_GLOBALLY,
                ModificationKind.ASSIGN_ASSET_TO_ALBUM,
                ModificationKind.REMOVE_ASSET_FROM_ALBUM,
            }
            and asset_id
        ):
            return get_immich_photo_url(asset_id)
        elif (
            kind
            in {
                ModificationKind.CREATE_ALBUM,
                ModificationKind.DELETE_ALBUM,
                ModificationKind.RENAME_ALBUM,
            }
            and album_id
        ):
            return f"/albums/{album_id}"
        return None

    @typechecked
    def _format_modification_entry(self, entry: ModificationEntry) -> str:
        parts = [f"{entry.datetime}"]
        # Always include the operation/enum (kind)
        parts.append(
            f"kind={entry.kind.name if hasattr(entry.kind, 'name') else entry.kind}"
        )
        # Removed 'entity' and 'action' as they are not attributes of ModificationEntry
        if entry.asset_id:
            parts.append(f"asset_id={entry.asset_id}")
        if entry.asset_name:
            parts.append(f"name={entry.asset_name}")
        if entry.tag_name:
            parts.append(f"tag={entry.tag_name}")
        if entry.album_id:
            parts.append(f"album_id={entry.album_id}")
        if entry.album_name:
            parts.append(f"album_name={entry.album_name}")
        if entry.old_name:
            parts.append(f"old_name={entry.old_name}")
        if entry.new_name:
            parts.append(f"new_name={entry.new_name}")
        if entry.link:
            parts.append(f"link={entry.link}")
        if entry.user:
            parts.append(f"user={entry.user}")
        return " | ".join(parts)

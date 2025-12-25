from __future__ import annotations

import datetime

import attrs

from immich_autotag.config.internal_config import IMMICH_WEB_BASE_URL
from typing import Optional

@attrs.define(auto_attribs=True, slots=True, frozen=True)
class ModificationEntry:
    datetime: str
    entity: str
    action: str
    asset_id: Optional[str] = None
    asset_name: Optional[str] = None
    tag_name: Optional[str] = None
    album_id: Optional[str] = None
    album_name: Optional[str] = None
    old_name: Optional[str] = None
    new_name: Optional[str] = None
    user: Optional[str] = None
    link: Optional[str] = None
    extra: Optional[dict] = None

# TODO: la siguiente clase es mas generiga que tag, requiere refactorizar nombre y ubicacion

@attrs.define(auto_attribs=True, slots=True)
class TagModificationReport:
    _instance_created = False  # Class-level flag


    import os, datetime as dt

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
    modifications: list[ModificationEntry] = attrs.field(
        factory=list, init=False, validator=attrs.validators.instance_of(list)
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
        if getattr(cls, '_instance_created', False):
            raise RuntimeError("TagModificationReport instance already exists. Use the existing instance instead of creating a new one.")
        cls._instance_created = True

    from typeguard import typechecked
    @typechecked
    def add_modification(
        self,
        action: str,
        entity: str = "tag",
        asset_id: Optional[str] = None,
        asset_name: Optional[str] = None,
        tag_name: Optional[str] = None,
        album_id: Optional[str] = None,
        album_name: Optional[str] = None,
        old_name: Optional[str] = None,
        new_name: Optional[str] = None,
        user: Optional[str] = None,
        extra: Optional[dict] = None,
    ) -> None:
        """
        Registers a modification for any entity (tag, album, assignment, etc.).
        Maintains compatibility with previous usage.
        """
        if not self._cleared_report:
            try:
                with open(self.report_path, "w", encoding="utf-8") as f:
                    pass  # Truncate the file
            except Exception as e:
                print(f"[WARN] Could not clear the tag modification report: {e}")
            self._cleared_report = True

        # Build link (asset or album)
        link = None
        if entity == "tag" and asset_id:
            link = f"{IMMICH_WEB_BASE_URL}/photos/{asset_id}"
        elif entity == "album" and album_id:
            link = f"{IMMICH_WEB_BASE_URL}/albums/{album_id}"
        elif entity == "assignment" and asset_id:
            link = f"{IMMICH_WEB_BASE_URL}/photos/{asset_id}"

        entry = ModificationEntry(
            datetime=datetime.datetime.now().isoformat(),
            entity=entity,
            action=action,
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
        asset_id: str,
        asset_name: str,
        action: str,
        tag_name: str,
        user: Optional[str] = None,
    ) -> None:
        self.add_modification(
            action=action,
            entity="tag",
            asset_id=asset_id,
            asset_name=asset_name,
            tag_name=tag_name,
            user=user,
        )

    @typechecked
    def add_album_modification(
        self,
        action: str,
        album_id: str,
        album_name: Optional[str] = None,
        old_name: Optional[str] = None,
        new_name: Optional[str] = None,
        user: Optional[str] = None,
    ) -> None:
        self.add_modification(
            action=action,
            entity="album",
            album_id=album_id,
            album_name=album_name,
            old_name=old_name,
            new_name=new_name,
            user=user,
        )

    @typechecked
    def add_assignment_modification(
        self,
        action: str,
        asset_id: str,
        asset_name: str,
        album_id: str,
        album_name: Optional[str] = None,
        user: Optional[str] = None,
    ) -> None:
        self.add_modification(
            action=action,
            entity="assignment",
            asset_id=asset_id,
            asset_name=asset_name,
            album_id=album_id,
            album_name=album_name,
            user=user,
        )

    def flush(self) -> None:
        """Flushes the report to file (append)."""
        if not self.modifications or self._since_last_flush == 0:
            return
        with open(self.report_path, "a", encoding="utf-8") as f:
            for entry in self.modifications[-self._since_last_flush :]:
                # Flexible log line
                parts = [f"{entry.datetime}"]
                if entry.entity:
                    parts.append(f"entity={entry.entity}")
                if entry.action:
                    parts.append(f"action={entry.action}")
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
                f.write(" | ".join(parts) + "\n")
        self._since_last_flush = 0

    def print_summary(self) -> None:
        print("\n[SUMMARY] Modifications:")
        for entry in self.modifications:
            parts = [f"{entry.datetime}"]
            if entry.entity:
                parts.append(f"entity={entry.entity}")
            if entry.action:
                parts.append(f"action={entry.action}")
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
            print(" | ".join(parts))
        print(f"Total modifications: {len(self.modifications)}")

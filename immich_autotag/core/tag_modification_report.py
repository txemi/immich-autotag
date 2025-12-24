from __future__ import annotations

import datetime

import attrs
import os
import datetime as dt

from main import IMMICH_WEB_BASE_URL




@attrs.define(auto_attribs=True, slots=True)
class TagModificationReport:
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
    modifications: list = attrs.field(
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

    def add_modification(
        self,
        asset_id: str,
        asset_name: str,
        action: str,
        tag_name: str,
        user: str = None,
    ) -> None:
        """
        Registers a tag modification (add/remove) for an asset.
        """
        if not self._cleared_report:
            try:
                with open(self.report_path, "w", encoding="utf-8") as f:
                    pass  # Truncate the file
            except Exception as e:
                print(f"[WARN] Could not clear the tag modification report: {e}")
            self._cleared_report = True
        # Build photo link
        photo_link = f"{IMMICH_WEB_BASE_URL}/photos/{asset_id}"
        entry = {
            "datetime": datetime.datetime.now().isoformat(),
            "asset_id": asset_id,
            "asset_name": asset_name,
            "action": action,  # 'add' or 'remove'
            "tag_name": tag_name,
            "user": user,
            "photo_link": photo_link,
        }
        self.modifications.append(entry)
        self._since_last_flush += 1
        if self._since_last_flush >= self.batch_size:
            self.flush()

    def flush(self) -> None:
        """Flushes the report to file (append)."""
        if not self.modifications or self._since_last_flush == 0:
            return
        with open(self.report_path, "a", encoding="utf-8") as f:
            for entry in self.modifications[-self._since_last_flush :]:
                f.write(
                    f"{entry['datetime']} | asset_id={entry['asset_id']} | name={entry['asset_name']} | action={entry['action']} | tag={entry['tag_name']} | link={entry['photo_link']}"
                )
                if entry["user"]:
                    f.write(f" | user={entry['user']}")
                f.write("\n")
        self._since_last_flush = 0

    def print_summary(self) -> None:
        print("\n[SUMMARY] Tag modifications:")
        for entry in self.modifications:
            print(
                f"{entry['datetime']} | asset_id={entry['asset_id']} | name={entry['asset_name']} | action={entry['action']} | tag={entry['tag_name']} | link={entry['photo_link']}"
                + (f" | user={entry['user']}" if entry["user"] else "")
            )
        print(f"Total modifications: {len(self.modifications)}")

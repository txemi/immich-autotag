"""Duplicate album conflict: one verdict per duplicate group, whichever copy runs.

Measured on a real run over 14,950 assets (Immich 3.3.5): 5 assets had the
duplicate album conflict tag added and removed on alternate steps. Each copy
judged the conflict from its own point of view (the other copies' albums plus its
own folder), so two copies of the same group disagreed and kept undoing each
other's tag.
"""

from unittest.mock import MagicMock

import pytest

from immich_autotag.assets.albums import folder_album_detection as fad
from immich_autotag.assets.albums.album_decision import AlbumDecision
from immich_autotag.assets.albums.analyze_and_assign_album import (
    _handle_duplicate_conflicts as mod,
)
from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper
from immich_autotag.classification import classification_rule_set as crs
from immich_autotag.report.modification_entries_list import ModificationEntriesList
from immich_autotag.types.uuid_wrappers import DuplicateUUID

GROUP = DuplicateUUID.random()


class _AllAlbumsMatch:
    def matches_album(self, album: str) -> bool:
        return not album.startswith("ignored")


@pytest.fixture(autouse=True)
def rule_set(monkeypatch):
    monkeypatch.setattr(
        crs.ClassificationRuleSet,
        "get_rule_set_from_config_manager",
        staticmethod(lambda: _AllAlbumsMatch()),
    )
    # The other copies' folder album, read without side effects.
    monkeypatch.setattr(fad, "folder_album_of", lambda w: w.folder_album)


def copy(albums: list[str], folder: str | None) -> MagicMock:
    w = MagicMock(spec=AssetResponseWrapper)
    w.get_album_names.return_value = albums
    w.folder_album = folder
    w.get_duplicate_id_as_uuid.return_value = GROUP
    w.ensure_autotag_duplicate_album_conflict.return_value = None
    return w


def run_from(current: MagicMock, others: list[MagicMock]) -> None:
    decision = MagicMock(spec=AlbumDecision)
    decision.album_from_folder = current.folder_album
    decision.duplicates_info.get_details.return_value = {
        i: o for i, o in enumerate(others)
    }
    result = mod.handle_duplicate_conflicts(current, decision)
    assert isinstance(result, ModificationEntriesList)


def verdicts(*copies: MagicMock) -> set[bool]:
    return {
        c.ensure_autotag_duplicate_album_conflict.call_args.kwargs["conflict"]
        for c in copies
    }


def test_same_verdict_whichever_copy_runs():
    # a: folder says "trip", no album. b: in album "party", no folder album.
    # Per copy, a saw {party, trip} (conflict) and b saw {} (none): the tag flipped.
    a, b = copy([], "trip"), copy(["party"], None)
    run_from(a, [b])
    assert verdicts(a, b) == {True}
    a2, b2 = copy([], "trip"), copy(["party"], None)
    run_from(b2, [a2])
    assert verdicts(a2, b2) == {True}


def test_own_albums_count():
    # Each copy in a different album, no folder albums: a real conflict that the
    # per-copy view missed (each copy only looked at the other one).
    a, b = copy(["trip"], None), copy(["party"], None)
    run_from(a, [b])
    assert verdicts(a, b) == {True}


def test_same_album_everywhere_is_no_conflict():
    a, b = copy(["trip"], "trip"), copy(["trip"], None)
    run_from(a, [b])
    assert verdicts(a, b) == {False}


def test_albums_outside_the_rules_do_not_count():
    a, b = copy(["trip"], None), copy(["ignored-x"], None)
    run_from(b, [a])
    assert verdicts(a, b) == {False}


def test_no_duplicate_id_does_nothing():
    a = copy(["trip"], "party")
    a.get_duplicate_id_as_uuid.return_value = None
    run_from(a, [])
    a.ensure_autotag_duplicate_album_conflict.assert_not_called()


def test_a_group_of_one_is_no_duplicate_conflict():
    # One copy in two albums is a classification conflict, not a duplicate one.
    a = copy(["trip", "party"], None)
    run_from(a, [])
    assert verdicts(a) == {False}


def test_other_copies_are_not_written_while_judging():
    # Judging the group must not run the folder detection that writes tags.
    a, b = copy([], "trip"), copy(["party"], None)
    run_from(a, [b])
    b.try_detect_album_from_folders.assert_not_called()

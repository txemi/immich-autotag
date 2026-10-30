"""Date correction: an asset's own filename date wins, and dates go out in local time.

An asset's own filename date wins over its duplicates' dates. Duplicates in Immich are
visually similar assets, not copies of one file: three screenshots of the same screen
taken hours apart form a duplicate group, and each keeps its own time (txemi, Q1678).
"""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock
from zoneinfo import ZoneInfo

import pytest

from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper
from immich_autotag.assets.date_correction.asset_date_candidate import (
    AssetDateCandidate,
)
from immich_autotag.assets.date_correction.asset_date_candidates import (
    AssetDateCandidates,
)
from immich_autotag.assets.date_correction.asset_date_sources_list import (
    AssetDateSourcesList,
)
from immich_autotag.assets.date_correction.core_logic import _helpers
from immich_autotag.assets.date_correction.core_logic.step_result import (
    DateCorrectionStepResult,
)
from immich_autotag.assets.date_correction.date_source_kind import DateSourceKind


def wrapper(asset_id: str) -> MagicMock:
    w = MagicMock(spec=AssetResponseWrapper)
    w.get_id.return_value = asset_id
    return w


def candidate_set(w: MagicMock, *dates: tuple[DateSourceKind, datetime]):
    cs = AssetDateCandidates(w)
    for kind, date in dates:
        cs.add(AssetDateCandidate(w, kind, date))
    return cs


def sources(main: MagicMock, *sets: AssetDateCandidates) -> AssetDateSourcesList:
    return AssetDateSourcesList(main, list(sets))


@pytest.fixture
def quiet(monkeypatch):
    """No config, no logging: the helpers only need a timezone setting."""
    monkeypatch.setattr(_helpers, "log", lambda *a, **k: None)
    monkeypatch.setattr(_helpers, "is_log_level_enabled", lambda *a, **k: False)


def set_timezone(monkeypatch, tz_name):
    date_correction = SimpleNamespace(extraction_timezone=tz_name)
    config = SimpleNamespace(
        duplicate_processing=SimpleNamespace(date_correction=date_correction)
    )
    manager = SimpleNamespace(get_config=lambda: config)
    from immich_autotag.config.manager import ConfigManager

    monkeypatch.setattr(ConfigManager, "get_instance", staticmethod(lambda: manager))


def test_own_candidates_by_kinds_ignores_duplicates():
    main, dup = wrapper("main"), wrapper("dup")
    own = datetime(2026, 5, 3, 11, 1, tzinfo=UTC)
    older = datetime(2026, 5, 3, 8, 0, tzinfo=UTC)
    sl = sources(
        main,
        candidate_set(main, (DateSourceKind.FILENAME, own)),
        candidate_set(dup, (DateSourceKind.FILENAME, older)),
    )
    got = sl.own_candidates_by_kinds([DateSourceKind.FILENAME])
    assert [c.get_aware_date() for c in got] == [own]
    assert len(sl.candidates_by_kinds([DateSourceKind.FILENAME])) == 2


def test_own_filename_date_wins_over_older_duplicate(quiet, monkeypatch):
    set_timezone(monkeypatch, None)
    main, dup = wrapper("main"), wrapper("dup")
    own = datetime(2026, 5, 3, 11, 1, tzinfo=UTC)
    older_dup = datetime(2026, 5, 1, 8, 0, tzinfo=UTC)
    immich_date = own + timedelta(days=5)
    sl = sources(
        main,
        candidate_set(main, (DateSourceKind.FILENAME, own)),
        candidate_set(dup, (DateSourceKind.FILENAME, older_dup)),
    )
    result = _helpers.check_filename_candidate_and_fix(main, sl, immich_date)
    assert result == DateCorrectionStepResult.FIXED
    main.update_date.assert_called_once_with(new_date=own)


def test_own_date_already_right_exits_without_looking_at_duplicates(quiet, monkeypatch):
    set_timezone(monkeypatch, None)
    main, dup = wrapper("main"), wrapper("dup")
    own = datetime(2026, 5, 3, 11, 1, tzinfo=UTC)
    sl = sources(
        main,
        candidate_set(main, (DateSourceKind.WHATSAPP_FILENAME, own)),
        candidate_set(dup, (DateSourceKind.FILENAME, own - timedelta(days=30))),
    )
    result = _helpers.check_filename_candidate_and_fix(main, sl, own)
    assert result == DateCorrectionStepResult.EXIT
    main.update_date.assert_not_called()


def test_own_date_newer_than_immich_exits_without_writing(quiet, monkeypatch):
    set_timezone(monkeypatch, None)
    main, dup = wrapper("main"), wrapper("dup")
    immich_date = datetime(2026, 5, 3, 11, 1, tzinfo=UTC)
    sl = sources(
        main,
        candidate_set(main, (DateSourceKind.FILENAME, immich_date + timedelta(days=3))),
        candidate_set(dup, (DateSourceKind.FILENAME, immich_date - timedelta(days=9))),
    )
    result = _helpers.check_filename_candidate_and_fix(main, sl, immich_date)
    assert result == DateCorrectionStepResult.EXIT
    main.update_date.assert_not_called()


def test_without_own_date_takes_oldest_of_group(quiet, monkeypatch):
    set_timezone(monkeypatch, None)
    main, dup = wrapper("main"), wrapper("dup")
    immich_main = datetime(2026, 5, 10, 9, 0, tzinfo=UTC)
    oldest = datetime(2026, 5, 1, 8, 0, tzinfo=UTC)
    sl = sources(
        main,
        candidate_set(main, (DateSourceKind.IMMICH, immich_main)),
        candidate_set(dup, (DateSourceKind.FILENAME, oldest)),
    )
    result = _helpers.check_filename_candidate_and_fix(main, sl, immich_main)
    assert result == DateCorrectionStepResult.FIXED
    main.update_date.assert_called_once_with(new_date=oldest)


def test_date_is_sent_in_extraction_timezone(quiet, monkeypatch):
    set_timezone(monkeypatch, "Europe/Madrid")
    main = wrapper("main")
    taken = datetime(2026, 5, 3, 9, 1, tzinfo=UTC)  # 11:01 in Madrid
    sl = sources(main, candidate_set(main, (DateSourceKind.FILENAME, taken)))
    _helpers.check_filename_candidate_and_fix(main, sl, taken + timedelta(days=5))
    sent = main.update_date.call_args.kwargs["new_date"]
    assert sent == taken
    assert (sent.hour, sent.minute) == (11, 1)
    assert sent.utcoffset() == timedelta(hours=2)


@pytest.mark.parametrize("tz_name", [None, "", "Not/AZone", "Europe"])
def test_to_extraction_timezone_falls_back_unchanged(quiet, monkeypatch, tz_name):
    set_timezone(monkeypatch, tz_name)
    dt = datetime(2026, 5, 3, 9, 1, tzinfo=UTC)
    out = _helpers.to_extraction_timezone(dt)
    assert out == dt and out.utcoffset() == timedelta(0)


def test_to_extraction_timezone_keeps_the_instant(monkeypatch):
    set_timezone(monkeypatch, "Europe/Madrid")
    dt = datetime(2026, 1, 3, 9, 1, tzinfo=UTC)
    out = _helpers.to_extraction_timezone(dt)
    assert out == dt
    assert out.tzinfo == ZoneInfo("Europe/Madrid") and out.hour == 10


@pytest.mark.parametrize("missing", ["duplicate_processing", "date_correction"])
def test_to_extraction_timezone_without_config_section(monkeypatch, missing):
    if missing == "duplicate_processing":
        config = SimpleNamespace(duplicate_processing=None)
    else:
        config = SimpleNamespace(
            duplicate_processing=SimpleNamespace(date_correction=None)
        )
    manager = SimpleNamespace(get_config=lambda: config)
    from immich_autotag.config.manager import ConfigManager

    monkeypatch.setattr(ConfigManager, "get_instance", staticmethod(lambda: manager))
    dt = datetime(2026, 5, 3, 9, 1, tzinfo=UTC)
    assert _helpers.to_extraction_timezone(dt) is dt

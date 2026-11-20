"""Duplicates and tag writes: no write ping-pong, no repeated writes.

Measured on a real run over 14,950 assets (Immich 3.3.5):
- 181 assets had the meme tag removed and re-added at consecutive steps. A MOVE
  conversion had taken the tag off one duplicate and put it in the album; the
  duplicate comparison looked at tags only, saw a difference and put the tag back
  on the other copy, run after run.
- 8 assets got the same tag added ~20 times in one step, and 44 got the same tag
  removed twice: after a write the asset kept its old state, so `has_tag` kept
  giving the old answer.
"""

from unittest.mock import MagicMock

from immich_autotag.assets import asset_cache_entry as ace
from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper
from immich_autotag.assets.duplicate_tag_logic import (
    __compare_classification_tags as cmp_mod,
)
from immich_autotag.assets.duplicate_tag_logic import (
    _classification_tag_comparison_result as result_mod,
)

ClassificationTagComparisonResult = result_mod.ClassificationTagComparisonResult


def wrapper(tags: list[str]) -> MagicMock:
    w = MagicMock(spec=AssetResponseWrapper)
    w.get_classification_tags.return_value = tags
    return w


def test_same_rule_by_tag_and_by_album_is_equal(monkeypatch):
    # One copy matches the meme rule through its tag, the other through the album.
    with_tag, in_album = wrapper(["autotag_input_meme"]), wrapper([])
    keys = {id(with_tag): frozenset({7}), id(in_album): frozenset({7})}
    monkeypatch.setattr(cmp_mod, "_matched_rule_keys", lambda a: keys[id(a)])
    res = cmp_mod.compare_classification_tags(with_tag, in_album)
    assert res.result == ClassificationTagComparisonResult.EQUAL
    res = cmp_mod.compare_classification_tags(in_album, with_tag)
    assert res.result == ClassificationTagComparisonResult.EQUAL


def test_different_rules_still_autofix(monkeypatch):
    # Only one copy is classified at all: the tag is still copied over, as before.
    classified, unclassified = wrapper(["autotag_input_meme"]), wrapper([])
    keys = {id(classified): frozenset({7}), id(unclassified): frozenset()}
    monkeypatch.setattr(cmp_mod, "_matched_rule_keys", lambda a: keys[id(a)])
    res = cmp_mod.compare_classification_tags(classified, unclassified)
    assert res.result == ClassificationTagComparisonResult.AUTOFIX_OTHER
    assert res.tag_info == "autotag_input_meme"


def test_unclassified_pair_is_not_equal_by_rules(monkeypatch):
    # Two copies matching no rule fall back to the tag comparison (equal tags → EQUAL).
    a, b = wrapper([]), wrapper([])
    monkeypatch.setattr(cmp_mod, "_matched_rule_keys", lambda a: frozenset())
    res = cmp_mod.compare_classification_tags(a, b)
    assert res.result == ClassificationTagComparisonResult.EQUAL


def test_refresh_after_write_bypasses_caches_and_saves(monkeypatch):
    calls = {}
    fresh_state = MagicMock(spec=ace.AssetDtoState)
    fresh_state.to_cache_dict.return_value = {"id": "x"}
    old_state = MagicMock(spec=ace.AssetDtoState)
    old_state.get_uuid.return_value = "asset-1"

    def fake_get(asset_id, client, use_cache=True):
        calls["use_cache"] = use_cache
        return object()

    saver = MagicMock()
    monkeypatch.setattr(
        "immich_autotag.api.logging_proxy.assets.get_asset_info.proxy_get_asset_info",
        fake_get,
    )
    monkeypatch.setattr(ace.AssetDtoState, "from_dto", lambda dto, kind: fresh_state)
    monkeypatch.setattr(ace.ApiCacheManager, "create", lambda cache_type: saver)

    entry = object.__new__(ace.AssetCacheEntry)
    object.__setattr__(entry, "_state", old_state)
    entry.refresh_after_write(MagicMock())

    assert calls["use_cache"] is False
    saver.save.assert_called_once_with("asset-1", {"id": "x"})
    assert entry._state is fresh_state

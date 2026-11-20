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


def test_unclassified_pair_falls_back_to_tags(monkeypatch):
    # Two copies matching no rule fall back to the tag comparison (equal tags → EQUAL).
    first, second = wrapper([]), wrapper([])
    monkeypatch.setattr(cmp_mod, "_matched_rule_keys", lambda asset: frozenset())
    res = cmp_mod.compare_classification_tags(first, second)
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


def test_matched_rule_keys_uses_the_configured_rule_object(monkeypatch):
    # The key is the configured rule itself, stable across rule-set rebuilds;
    # rules that did not match are left out.
    from immich_autotag.classification import classification_rule_set as rs_mod

    meme_rule, other_rule = object(), object()

    def match(rule, matched):
        m = MagicMock()
        m.rule.return_value.rule = rule
        m.has_match.return_value = matched
        return m

    fake_set = MagicMock()
    fake_set.matching_rules.return_value.rules.return_value = [
        match(meme_rule, True),
        match(other_rule, False),
    ]
    monkeypatch.setattr(
        rs_mod.ClassificationRuleSet,
        "get_rule_set_from_config_manager",
        staticmethod(lambda: fake_set),
    )
    assert cmp_mod._matched_rule_keys(wrapper([])) == frozenset({id(meme_rule)})


def entries_of(*kinds: str) -> MagicMock:
    entries = MagicMock()
    entries.__bool__.return_value = bool(kinds)
    fake = []
    for k in kinds:
        e = MagicMock()
        e.kind.name = k
        fake.append(e)
    entries.entries.return_value = fake
    return entries


def fake_asset() -> MagicMock:
    asset = MagicMock()
    asset.get_id.return_value = "asset-1"
    return asset


def test_tag_write_reloads_the_asset():
    asset = fake_asset()
    AssetResponseWrapper._refresh_after_tag_write(asset, entries_of("ADD_TAG_TO_ASSET"))
    asset._cache_entry.refresh_after_write.assert_called_once()


def test_failed_or_empty_write_does_not_reload():
    for entries in (
        entries_of(),
        entries_of("WARNING_TAG_REMOVAL_FROM_ASSET_FAILED"),
    ):
        asset = fake_asset()
        AssetResponseWrapper._refresh_after_tag_write(asset, entries)
        asset._cache_entry.refresh_after_write.assert_not_called()


def test_a_failed_reload_does_not_break_the_run():
    asset = fake_asset()
    asset._cache_entry.refresh_after_write.side_effect = RuntimeError("API down")
    AssetResponseWrapper._refresh_after_tag_write(
        asset, entries_of("REMOVE_TAG_FROM_ASSET")
    )

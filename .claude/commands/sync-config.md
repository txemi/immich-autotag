Synchronise the private config file with the latest template, preserving all personal/private values.

## Files involved

- **Template** (source of improvements): `immich_autotag/config/user_config_template.py`
- **Private config** (target): `~/.config/immich_autotag/config.py`

## What to update (take from template)

- Python `#` comments and section headers
- `description=` field values on all config objects
- File docstring
- Structure and formatting improvements
- Any new config fields added to the template that are missing in the private config (use the template's default value)

## What to preserve (never change)

- `server`: `host`, `port`, `api_key`
- `date_correction`: `extraction_timezone`
- All `UserGroup` entries: `name`, `members` (emails), `description` if already personalised
- All `AlbumSelectionRule` entries: `keyword`, `groups`, `access`, `name`
- Any constants defined in the private config that are not in the template (e.g. `_ALL_AGES_MEME`, `_TAG_KEYWORD_MEME`, `_BAIGOMAR`, `_AGUAMAR`)
- Any `skip`, `filters`, `performance`, `threshold_days` values that differ from the template defaults

## Process

1. Read both files.
2. Identify differences: what the template has that the private config lacks or has outdated.
3. Show a brief summary of the planned changes before editing.
4. Apply the changes to `~/.config/immich_autotag/config.py`.
5. Verify the updated file loads without errors: `python -m immich_autotag.config.user_config_template` equivalent — run `python -c "exec(open('/home/txemi/.config/immich_autotag/config.py').read())" 2>&1 | tail -3` and confirm no traceback.

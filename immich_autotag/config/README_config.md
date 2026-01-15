# Immich Autotag Configuration Guide

This document explains how to configure the Immich autotag system for your instance.

## Recommended Location

Place your configuration file at:

`~/.config/immich_autotag/config.yaml`

This follows the XDG standard and keeps your home directory organized.

## Configuration File Formats

You can choose between two configuration formats:


Both templates are provided in this folder. You can copy and adapt either one to your needs. Each template is self-documented with comments and field explanations inside the file.
 
 - **YAML file** (simple, self-documented): Recommended for most users. See the template: [user_config_template.yaml](./user_config_template.yaml)
 - **Python file** (detailed, programmatic): For advanced users — includes richer inline documentation and examples that help explain concepts and advanced options. See the template: [user_config_template.py](./user_config_template.py)
 
 Both templates are provided so you can pick whichever format you prefer. Each template contains inline comments and field explanations; use YAML for straightforward setups and the Python template when you want more detailed guidance or programmatic flexibility.

## Example YAML Configuration

```yaml
server:
  host: "immich.example.com"
  port: 2283
  api_key: "YOUR_API_KEY_HERE"
filter_out_asset_links: []
classification_rules:
  - tag_names: ["meme", "autotag_input_meme"]
    album_name_patterns: null
  - tag_names: ["adult_meme", "autotag_input_adult_meme"]
    album_name_patterns: null
  - tag_names: ["autotag_input_pending_review"]
    album_name_patterns: null
  - tag_names: ["autotag_input_ignore"]
    album_name_patterns: null
  - tag_names: null
    album_name_patterns: ["^\\d{4}-(\\d{2}(-\\d{2})?)?"]
conversions:
  - source:
      tag_names: ["meme"]
      album_name_patterns: null
    destination:
      tag_names: ["autotag_input_meme"]
      album_name_patterns: null
  - source:
      tag_names: ["adult_meme"]
      album_name_patterns: null
    destination:
      tag_names: ["autotag_input_adult_meme"]
      album_name_patterns: null
auto_tags:
  enabled: true
  category_unknown: autotag_output_unknown
  category_conflict: autotag_output_conflict
  duplicate_asset_album_conflict: autotag_output_duplicate_asset_album_conflict
  duplicate_asset_classification_conflict: autotag_output_duplicate_asset_classification_conflict
  duplicate_asset_classification_conflict_prefix: autotag_output_duplicate_asset_classification_conflict_
features:
  enable_album_detection: true
  enable_tag_suggestion: false
  advanced_feature:
    enabled: true
    threshold: 0.8
  enable_album_name_strip: true
  album_detection_from_folders:
    enabled: false
    excluded_paths: ["whatsapp"]
  date_correction:
    enabled: false
    extraction_timezone: "UTC"
  enable_checkpoint_resume: false
```



## More Information

- For advanced configuration, you can also use a Python file (`config.py`) with a `user_config` object.
- See the code comments in `user_config_template.py` for field explanations.
- For troubleshooting and updates, visit the [project repository](https://github.com/txemi/immich-autotag).

---

If you run the CLI and no configuration is found, you will see a link to this guide.

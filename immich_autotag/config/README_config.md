---
uuid: b2884393-d332-4e6f-bf55-e93b6cdfb4f9
---

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

If any field, option, or behavior is unclear while using the YAML template, consult the Python template — it typically contains more exhaustive explanations and illustrative examples that clarify advanced usage.

## More Information

- For advanced configuration, you can also use a Python file (`config.py`) with a `user_config` object.
- See the code comments in `user_config_template.py` for field explanations.
- For troubleshooting and updates, visit the [project repository](https://github.com/txemi/immich-autotag).

---

If you run the CLI and no configuration is found, you will see a link to this guide.

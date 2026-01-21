import webbrowser
from typing import List

from typeguard import typechecked

from immich_autotag.config.models import UserConfig


@typechecked
def _generate_links(config: UserConfig) -> List[str]:
    host: str = config.server.host
    port: int = config.server.port
    links: List[str] = [f"- [Albums](http://{host}:{port}/albums)"]

    # Collect all autotag values from the new configuration structure
    tags_to_add = []

    # From classification rules (input tags)
    if config.classification and config.classification.rules:
        seen_tags = set()
        for rule in config.classification.rules:
            if rule.tag_names:
                for tag in rule.tag_names:
                    if tag.startswith("autotag_input_") and tag not in seen_tags:
                        seen_tags.add(tag)
                        # Clean label: remove prefix and format
                        label = (
                            tag.replace("autotag_input_", "").replace("_", " ").title()
                        )
                        tags_to_add.append((f"Input: {label}", tag))

    # From classification (output tags)
    if config.classification:
        if config.classification.autotag_unknown:
            tags_to_add.append(
                (
                    "Classification: Unknown",
                    config.classification.autotag_unknown,
                )
            )
        if config.classification.autotag_conflict:
            tags_to_add.append(
                (
                    "Classification: Conflict",
                    config.classification.autotag_conflict,
                )
            )

    # From duplicate_processing
    if config.duplicate_processing:
        if config.duplicate_processing.autotag_album_conflict:
            tags_to_add.append(
                (
                    "Duplicates: Album conflict",
                    config.duplicate_processing.autotag_album_conflict,
                )
            )
        if config.duplicate_processing.autotag_classification_conflict:
            tags_to_add.append(
                (
                    "Duplicates: Classification conflict",
                    config.duplicate_processing.autotag_classification_conflict,
                )
            )
        if config.duplicate_processing.autotag_album_detection_conflict:
            tags_to_add.append(
                (
                    "Duplicates: Album detection conflict",
                    config.duplicate_processing.autotag_album_detection_conflict,
                )
            )

    # From album_date_consistency
    if config.album_date_consistency and config.album_date_consistency.enabled:
        if config.album_date_consistency.autotag_album_date_mismatch:
            tags_to_add.append(
                (
                    "Consistency: Album date mismatch",
                    config.album_date_consistency.autotag_album_date_mismatch,
                )
            )

    # Generate links for each tag
    for label, tag_value in tags_to_add:
        url = f"http://{host}:{port}/tags?path={tag_value}"
        links.append(f"- [{label}]({url})")

    links.append(
        (
            "\nFor configuration details, see: "
            "[README_config.md](https://github.com/txemi/"
            "immich-autotag/blob/main/immich_autotag/config/README_config.md)"
        )
    )
    return links


@typechecked
def _print_links_to_console(config: UserConfig, links: List[str]) -> None:
    print("\nImmich autotagging process started!")
    print("You can monitor the results and progress at the following links:")
    for line in links:
        if line.startswith("- [Albums]"):
            print(
                f"- Albums:        http://{config.server.host}:"
                f"{config.server.port}/albums"
            )
        elif line.startswith("- ["):
            # Extract label and url for pretty print
            import re

            m = re.match(r"- \[(.+)\]\((.+)\)", line)
            if m:
                label, url = m.group(1), m.group(2)
                print(f"- {label}: {url}")
    print("\nFor configuration details, see:")
    print(
        "https://github.com/txemi/immich-autotag/blob/main/"
        "immich_autotag/config/README_config.md\n"
    )


@typechecked
def _write_links_markdown(links: List[str]) -> None:
    from immich_autotag.utils.run_output_dir import get_run_output_dir

    try:
        out_dir = get_run_output_dir()
        md_path = out_dir / "immich_autotag_links.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write("# Immich Autotagging Quick Links\n\n")
            f.write("\n".join(links))
            f.write("\n")
    except Exception as e:
        print(f"[WARN] Could not write links markdown: {e}")


@typechecked
def print_welcome_links(config: UserConfig) -> None:
    links = _generate_links(config)
    _print_links_to_console(config, links)
    _write_links_markdown(links)


@typechecked
def print_config_help() -> None:
    local_path = "immich_autotag/config/README_config.md"
    web_url = (
        "https://github.com/txemi/immich-autotag/blob/main/"
        "immich_autotag/config/README_config.md"
    )
    print("\nNo configuration found. Please see the configuration guide:")
    print(f"- Local file: {local_path}")
    print(f"- Online: {web_url}")
    try:
        webbrowser.open(web_url)
    except Exception:
        pass

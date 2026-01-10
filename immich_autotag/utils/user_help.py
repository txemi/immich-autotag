
import webbrowser
from typing import List
from typeguard import typechecked
from immich_autotag.config.models import UserConfig

@typechecked
def _generate_links(config: UserConfig) -> List[str]:
    host: str = config.server.host
    port: int = config.server.port
    auto_tags = getattr(config, 'auto_tags', None)
    links: List[str] = [f"- [Albums](http://{host}:{port}/albums)"]
    if auto_tags:
        for tag_key, tag_value in auto_tags.__dict__.items():
            if isinstance(tag_value, str) and tag_value:
                url = f"http://{host}:{port}/tags?path={tag_value}"
                label = tag_key.replace('_', ' ').capitalize()
                links.append(f"- [{label}]({url})")
    links.append("\nFor configuration details, see: [README_config.md](https://github.com/txemi/immich-autotag/blob/main/immich_autotag/config/README_config.md)")
    return links

@typechecked
def _print_links_to_console(config: UserConfig, links: List[str]) -> None:
    print("\nImmich autotagging process started!")
    print("You can monitor the results and progress at the following links:")
    for line in links:
        if line.startswith("- [Albums]"):
            print(f"- Albums:        http://{config.server.host}:{config.server.port}/albums")
        elif line.startswith("- ["):
            # Extract label and url for pretty print
            import re
            m = re.match(r"- \[(.+)\]\((.+)\)", line)
            if m:
                label, url = m.group(1), m.group(2)
                print(f"- {label}: {url}")
    print("\nFor configuration details, see:")
    print("https://github.com/txemi/immich-autotag/blob/main/immich_autotag/config/README_config.md\n")

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
    web_url = "https://github.com/txemi/immich-autotag/blob/main/immich_autotag/config/README_config.md"
    print("\nNo configuration found. Please see the configuration guide:")
    print(f"- Local file: {local_path}")
    print(f"- Online: {web_url}")
    try:
        webbrowser.open(web_url)
    except Exception:
        pass

def print_welcome_links(config):
def print_config_help():
import webbrowser
from typeguard import typechecked

@typechecked
def print_welcome_links(config: object) -> None:
    host = config.server.host
    port = config.server.port
    print("\nImmich autotagging process started!")
    print("You can monitor the results and progress at the following links:")
    print(f"- Conflict tags: http://{host}:{port}/tags?path=autotag_output_conflict")
    print(f"- Albums:        http://{host}:{port}/albums")
    print(f"- Unknown tags:  http://{host}:{port}/tags?path=autotag_output_unknown")
    print("\nFor configuration details, see:")
    print("https://github.com/txemi/immich-autotag/blob/main/immich_autotag/config/README_config.md\n")

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

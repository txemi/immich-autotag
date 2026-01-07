


from immich_autotag.config.experimental_config.manager import load_experimental_config_at_startup
from immich_autotag.entrypoint import run_main

if __name__ == "__main__":
    if False:
        # Carga experimental de configuración estructurada (no afecta al flujo principal)
        load_experimental_config_at_startup()
    run_main()

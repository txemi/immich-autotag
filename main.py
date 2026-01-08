


from immich_autotag.config.experimental_config.manager import load_experimental_config_at_startup
from immich_autotag.entrypoint import run_main

if __name__ == "__main__":
    if False:
        # Experimental loading of structured configuration (does not affect main flow)
        load_experimental_config_at_startup()
    run_main()

# 1. Immich AutoTag

## 1.1. Project Description (2 lines)

Immich AutoTag is a basic process and rule engine to automate actions on images and videos (assets) in Immich. It can create and assign albums, generate and assign tags, and repair dates based on a user-defined configuration file.

## 1.2. Motivation


### 1.2.1. Why Immich?

In recent years, [Immich](https://immich.app) has become one of the most popular solutions for private photo and video management, surpassing alternatives like Google Photos or NAS applications. External services such as Google Photos may lose features, delete data (e.g., face information), impose quotas, or reduce photo quality. NAS apps often perform poorly when run on typical home hardware, which is usually less powerful than professional setups. Immich stands out for being open-source (free software), fast, private, and having an active community, making it the preferred choice for many users.

### 1.2.2. Why this project?

When starting to use Immich, it is common to import large volumes of photos from older systems, where organization was done in folders or with other apps. This creates a challenge: many photos and videos remain unorganized or misclassified. Although Immich is powerful, manual classification can be slow and tedious. This project aims to make organization faster and easier through automatic rules and tagging.

> **Note:** Some users have found it hard to understand what this tool actually does. For a much simpler, intentionally non-technical explanation, see [Explain Like I'm 5](./docs/explain-like-im-5.md).




## 1.3. Key Features

- **Automatic album creation and assignment:** Create and assign albums based on detected duplicates in Immich, or from folders in your file system (if enabled). Both methods can be used to save time when organizing large libraries.
- **Rule-based classification engine:** Define flexible rules using tags and album name patterns to automatically categorize assets. Immich AutoTag will label each asset as classified, in conflict, or pending classification using output tags.
- **Permission management:** Configure user groups and rules in the config file to automatically assign album permissions to large sets of albums, based on keywords in album names.
- **Automatic date correction:** If enabled, the tool can automatically fix asset dates using duplicate analysis or by extracting dates from filenames (e.g., Android or WhatsApp photo naming patterns).
- **Global filtering:** Use inclusion or exclusion filters to process only specific assets, albums, or tags, instead of the entire library.
- **Date mismatch tagging:** Automatically tag assets whose date does not match the date in their album name (for date-patterned albums), making it easy to review and correct inconsistencies.
- **Modification and statistics logs:** The system generates detailed modification reports and statistics files, including counters for unclassified assets and detected conflicts, to help you track progress and quality.
- **Continuous or scheduled tagging:** A dedicated script allows for continuous asset tagging/classification during heavy editing sessions, or can be easily scheduled (e.g., nightly runs) using Docker or cron—making it easy to keep up with rapid changes or automate regular organization.
- **Batch tag/album conversions:** Apply new tags or albums to assets in bulk (by name pattern, tag, or asset), keeping or removing originals—ideal for reorganizing or refactoring your library as your needs evolve.

For a more structured and detailed overview (including internal tools and links to technical issues), see the [Functional Blocks Matrix](./docs/functional_blocks_matrix.md).

This classification relies on a rule engine that is continuously evolving to become more abstract and flexible, allowing adaptation to the specific needs of different users.

It helps to:
- Quickly create and assing albums
- Quickly detect which photos or videos are still unorganized.
- Highlight possible errors, such as assets classified under multiple conflicting criteria.
- Speed up the review and mass organization of your photo library.


> For more details and upcoming features, see the [Roadmap](./ROADMAP.md) and [Changelog](./CHANGELOG.md).

## 1.4. Quick Start

To get started quickly:


### 1.4.1. Copy the configuration file

- Place your config at `~/.config/immich_autotag/config.yaml` (recommended XDG location).
- See the [Configuration Guide](./immich_autotag/config/README_config.md) for details and an example config file.

### 1.4.2. Run the tool (choose one method)


You can run Immich AutoTag using any of the following methods:


**A. With Docker (recommended for most users)**

  - **One-shot execution (run once):**
    - Using the public image:
      ```bash
      bash scripts/docker/run_docker_public.sh
      ```
      This script always uses the latest public image from Docker Hub (`txemi/immich-autotag:latest`).
      All logs and statistics will be available in the `logs_docker_one_shot` folder on your host machine.
    - Using a local image:
      ```bash
      bash scripts/docker/run_docker_with_config.sh
      ```
      By default, this uses the local image (`immich-autotag:latest`).
      All logs and statistics will be available in the `logs_docker_one_shot` folder on your host machine.
      To use the public image explicitly:
      ```bash
      bash scripts/docker/run_docker_with_config.sh --image txemi/immich-autotag:latest
      ```

  - **Periodic execution (cron mode, ideal for Rancher/Portainer):**
    - Use the image `txemi/immich-autotag:cron` (or build from `Dockerfile.cron`).
    - **Note:** The cron image must be built and published to Docker Hub before it can be used as `txemi/immich-autotag:cron`.
    - You can set the schedule with the `CRON_SCHEDULE` environment variable (standard cron format).
    - Example: run every day at 2:00 AM (default):
      ```bash
      docker run -d --name autotag-cron \
        -e CRON_SCHEDULE="0 2 * * *" \
        -v ~/.config/immich_autotag:/root/.config/immich_autotag \
        txemi/immich-autotag:cron
      ```
    - Example: run every hour:
      ```bash
      docker run -d --name autotag-cron \
        -e CRON_SCHEDULE="0 * * * *" \
        -v ~/.config/immich_autotag:/root/.config/immich_autotag \
        txemi/immich-autotag:cron
      ```
    - Logs are saved to `/var/log/cron.log` inside the container (you can map it to a volume if desired).
    - See `docker/docker-compose.yml` for a multi-container example (one-shot and cron modes).

      - **Periodic execution with Docker Compose (recommended for advanced setups):**
        - You can use the provided `docker-compose.yml` to manage the cron service and volumes easily.
        - By default, the cron job runs every hour (`0 * * * *`). You can adjust the schedule in the configuration if needed.
        - To change the schedule, set the `CRON_SCHEDULE` environment variable in your `docker-compose.yml` under the `environment` section. For example, to run once per hour at minute 17:
          ```yaml
          services:
            autotag-cron:
              image: txemi/immich-autotag:cron
              container_name: autotag-cron
              restart: unless-stopped
              environment:
                - CRON_SCHEDULE=17 * * * *
              volumes:
                - ${HOME}/.config/immich_autotag:/root/.config/immich_autotag
                - ./logs_docker_cron:/root/logs
          ```
        - To start the service:
          ```bash
          docker compose up -d
          ```
          Or use the provided script:
          ```bash
          bash scripts/docker/cron/up_compose.sh
          ```
          (Recommended: all main actions have scripts for reproducibility and reference.)
        - All logs and statistics will be available in the `logs_docker_cron` folder on your host machine.

**B. With pipx (no code download required)**

  - If you have pipx installed:
    ```bash
    pipx run immich-autotag
    ```

  - You can also use the provided scripts:
    - Run once:
      ```bash
      bash scripts/pypi/run_immich_autotag.sh
      ```
    - Run in a loop (for continuous tagging/classification):
      ```bash
      bash scripts/pypi/loop_immich_autotag.sh
      ```



**C. Directly from the repo. Local/development runs (script, requires code download)**
  - All logs and statistics will be available in the `logs_local` folder on your host machine.
  - Use the provided scripts:
    - **Run once (single execution):**
      ```bash
      bash scripts/run/run_once_app.sh
      ```
    - **Run in a loop (continuous tagging/classification):**
      ```bash
      bash scripts/run/loop_run_app.sh
      ```

    - **Alternative:** You can run the packaged app directly. This is the recommended way
      to ensure imports resolve consistently (for example in CI):
      ```bash
      # Use the helper script which activates the venv and runs the package
      bash run_app.sh

      # Or run the package module directly
      python -m immich_autotag
      ```

That's it! Your Immich autotagging tool is ready to use.

> **Do you prefer to download the code and run it manually?**
> See the section [Installation and Automatic Client Generation](./docs/development.md#15-installation-and-automatic-client-generation) in the [Development Guide](./docs/development.md).


## 1.5. Reviewing Results: Example Links

After running the autotagging script, you can quickly review the results and take action using the following types of links. These links are generated for your Immich server and point directly to the relevant albums or tags:

**Example Quick Links:**

```
- [Albums](http://your-immich-server:2283/albums)
- [Category unknown](http://your-immich-server:2283/tags?path=autotag_output_unknown)
- [Category conflict](http://your-immich-server:2283/tags?path=autotag_output_conflict)
- [Duplicate asset album conflict](http://your-immich-server:2283/tags?path=autotag_output_duplicate_asset_album_conflict)
- [Duplicate asset classification conflict](http://your-immich-server:2283/tags?path=autotag_output_duplicate_asset_classification_conflict)
- [Duplicate asset classification conflict prefix](http://your-immich-server:2283/tags?path=autotag_output_duplicate_asset_classification_conflict_)
- [Album date mismatch](http://your-immich-server:2283/tags?path=autotag_output_album_date_mismatch)
```

> Replace `your-immich-server:2283` with the address and port of your Immich instance.

**How to use these links:**

- Click the "Albums" link to review all albums and their contents.
- Click any autotag link (e.g., "Category unknown", "Album date mismatch") to see all assets currently flagged with that tag.
- Use the Immich web interface to reclassify, retag, or move assets as needed.
- After making changes, rerun the script to update the tags and see your progress.

These links are also written to a Markdown file (`logs/<run_id>/immich_autotag_links.md`) for each run, so you can always find the direct links for your review workflow.



## 1.6. Practical Use Case: How to Take Advantage of This Script


After the motivation, let's describe a practical use case for this tool. 



**Step 1: Review and adjust your [configuration file](./immich_autotag/config/README_config.md)**

  - Decide if you want Immich AutoTag to create albums automatically:
    - From dates (e.g., daily albums for unclassified assets)
    - From folders in your file system (useful if you previously organized by folders)
  - Choose your classification criteria:
    - Define the rules (tags and/or album name patterns) that determine which assets are considered classified, unclassified, or in conflict. Immich AutoTag will use these to label assets accordingly.
  - Review other useful configuration options:
    - Set up permission groups, enable or disable automatic date correction, and configure global filters as needed.

You can define also special tags or albums for photos that do not belong to any album for a specific reason (e.g., memes automatically uploaded from mobile devices, which you do not want in any album). The default config suggests using certain tags for these cases, so the user can label memes or other photos accordingly, and the script will take them into account.

**Step 2: Run the script**

  - Launch Immich AutoTag using any of the methods described above (Docker, pipx, or directly from the repo).
  - For automated, periodic execution, you can use the Docker cron image or set up your own scheduling solution.

**Step 3: Use the generated links to organize your assets** 

[example quick links above](#121-reviewing-results-example-links) 

  - If you enabled automatic album creation, start by visiting the Albums view (see the link at the top of this document). Do not group by year, sort by number of assets, and filter by autotag. This will show you the largest automatically created albums first.
    - For each album, you can choose to rename and keep it, delete it if not needed, or modify its contents to better fit your organization.
    - Once you are satisfied with your albums, move to the next review step.
  - Next, use the provided links to review assets that are unclassified or in conflict. These links let you quickly find and address assets that need attention.
  - Finally, use the other links to review assets tagged for issues such as date mismatches or other warnings. Anything autotag has flagged and you don't agree with can be deleted; autotag will recreate the necessary tags on the next run based on your configuration.
  - Note: Immich AutoTag is designed to automatically remove warning tags when issues are resolved, so you don't need to clean them up manually.


 The user can keep iterating until the library is perfectly organized.

**Tips for Classification:**
- To find memes or photos that should be tagged to avoid being candidates for albums, use Immich's "find similar" feature (AI-powered), which helps you quickly locate and tag such photos in bulk.

> For a complete and detailed list of features, improvements, and changes, see the [Changelog](./CHANGELOG.md).

## 1.7. Development

For information about project structure, contributing, and technical details, see the [Developer Guide](./docs/development.md).

If you would like to contribute, please see the new [Contributing Guide](./docs/CONTRIBUTING.md). Any help is welcome—especially with re-enabling GitHub Actions (CI/CD), which is currently disabled due to the challenge of embedding the Immich client library in the build process. This project is developed in spare time, so all contributions are greatly appreciated!

## 1.8. Support
For questions, issues, or feature requests, please use the [GitHub Issues](https://github.com/txemi/immich-autotag/issues) ticketing system.

## 1.9. License
This project is licensed under the GNU GPL v3. See the [LICENSE](./LICENSE) file for details.



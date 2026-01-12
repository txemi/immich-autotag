# 1. Immich AutoTag

## 1.1. Motivation

### 1.1.1. Why Immich?

In recent years, [Immich](https://immich.app) has become one of the most popular solutions for private photo and video management, surpassing alternatives like Google Photos or NAS applications. External services such as Google Photos may lose features, delete data (e.g., face information), impose quotas, or reduce photo quality. NAS apps often perform poorly when run on typical home hardware, which is usually less powerful than professional setups. Immich stands out for being open-source (free software), fast, private, and having an active community, making it the preferred choice for many users.

### 1.1.2. Why this project?

When starting to use Immich, it is common to import large volumes of photos from older systems, where organization was done in folders or with other apps. This creates a challenge: many photos and videos remain unorganized or misclassified. Although Immich is powerful, manual classification can be slow and tedious. This project aims to make organization faster and easier through automatic rules and tagging.

> **Note:** Some users have found it hard to understand what this tool actually does. For a much simpler, intentionally non-technical explanation, see [Explain Like I'm 5](./docs/explain-like-im-5.md).

### 1.1.3. What does this project solve?

This project automatically applies new tags to assets (photos and videos) in Immich, based on existing albums and tags. 

**In the context of this project, a photo is considered 'classified' if it either belongs to a set of albums (configurable using patterns) that are deemed to provide classification, or it has one or more tags (also configurable) that the user considers sufficient for classification.**

This classification relies on a rule engine that is continuously evolving to become more abstract and flexible, allowing adaptation to the specific needs of different users.

It helps to:
- Quickly detect which photos or videos are still unorganized.
- Highlight possible errors, such as assets classified under multiple conflicting criteria.
- Speed up the review and mass organization of your photo library.

#### 1.1.3.1. Other Features 

In addition to its core focus on helping classify and organize photos, the project also provides several advanced features to streamline large-scale photo management:

- **Automatic date repair:** The system can automatically detect and fix incorrect or missing dates for assets based on file names and duplicate analysis.
- **Automatic classification based on duplicates:** Photos are automatically classified by analyzing duplicate assets, reducing manual work.
- **Continuous tagging loop script:** A dedicated script allows for continuous asset tagging/classification during heavy editing sessions, making it easier to keep up with rapid changes.
- **Asset exclusion by web link:** You can exclude specific sets of assets from processing by specifying their web link, giving you more control over what gets classified.
- **Modification and statistics logs:** The system generates detailed modification reports and statistics files, including counters for unclassified assets and detected conflicts, to help you track progress and quality.

> For more details and upcoming features, see the [Roadmap](./ROADMAP.md) and [Changelog](./CHANGELOG.md).

## 1.2. Quick Start

To get started quickly:


### 1. Copy the configuration file

- Place your config at `~/.config/immich_autotag/config.yaml` (recommended XDG location).
- See the [Configuration Guide](./immich_autotag/config/README_config.md) for details and an example config file.

### 2. Run the tool (choose one method)


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

That's it! Your Immich autotagging tool is ready to use.

> **Do you prefer to download the code and run it manually?**
> See the section [Installation and Automatic Client Generation](./docs/development.md#15-installation-and-automatic-client-generation) in the [Development Guide](./docs/development.md).


## 1.2.1. Reviewing Results: Example Links

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



## 1.3. Practical Use Case: How to Take Advantage of This Script

After the motivation, let's describe a practical use case for this tool. The script scans all your photos, trying to detect whether they have been classified, remain unclassified, or have multiple classifications (which could indicate an error).

**Step 1:** Review the pattern used to detect which albums are considered "classified" (this can be modified in the [configuration file](./immich_autotag/config/README_config.md)). By default, any album whose name starts with a date is assumed to be an event and its photos are considered organized.

**Step 2:** There are also special tags for photos that do not belong to any album for a specific reason (e.g., memes automatically uploaded from mobile devices, which you do not want in any album). The default config suggests using certain tags for these cases, so the user can label memes or other photos accordingly, and the script will take them into account.

**Step 3:** If the script finds a photo that is unclassified or classified in multiple places, it will use a special tag (by default, tags starting with `autotag_`). All of this is configurable in the user config file. This way, you can easily locate these photos from the Immich interface and decide what to do: add/remove them from albums, tag as meme, postpone, ignore, etc.

**Step 4:** After making corrections in Immich (see the [example quick links above](#121-reviewing-results-example-links) to easily review and access affected assets), you can rerun the script. It will remove the special tags from photos that have been resolved, so each run leaves fewer unclassified or conflicted photos. The user can keep iterating until the library is perfectly organized.

**Tips for Classification:**
- Use Immich's date view to quickly identify all photos from the same event and add them to an album with the name pattern you defined for valid classification.
- To find memes or photos that should be tagged to avoid being candidates for albums, use Immich's "find similar" feature (AI-powered), which helps you quickly locate and tag such photos in bulk.

## 1.4. Future Directions

With the logic for adding and removing tags now solved in this project, it becomes very easy to add new features. In the future, this tagging system and codebase could be extended to:

- Automatically create albums based on existing regular folder structures (e.g., import folder hierarchies as albums).
- Assist in the detection and management of duplicate folders or files within the photo library.
- Assign users to albums automatically based on the application's rule engine (e.g., ownership, sharing, or access control).
 - Make the rule engine more generic to enable processing workflows for batch operations that are better adapted to users' specific needs.
- Integrate with other automation or AI-based classification systems to further enhance photo management.

This foundation makes it straightforward to build more advanced features for organizing and maintaining large photo and video collections in Immich.

> For a complete and detailed list of features, improvements, and changes, see the [Changelog](./CHANGELOG.md).

## 1.5. Development

For information about project structure, contributing, and technical details, see the [Developer Guide](./docs/development.md).

If you would like to contribute, please see the new [Contributing Guide](./docs/CONTRIBUTING.md). Any help is welcome—especially with re-enabling GitHub Actions (CI/CD), which is currently disabled due to the challenge of embedding the Immich client library in the build process. This project is developed in spare time, so all contributions are greatly appreciated!

## 1.6. Support
For questions, issues, or feature requests, please use the [GitHub Issues](https://github.com/txemi/immich-autotag/issues) ticketing system.

## 1.7. License
This project is licensed under the GNU GPL v3. See the [LICENSE](./LICENSE) file for details.



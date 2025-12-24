# 1. Immich AutoTag

## 1.1. Motivation

### 1.1.1. Why Immich?

In recent years, [Immich](https://immich.app) has become one of the most popular solutions for private photo and video management, surpassing alternatives like Google Photos or NAS applications. External services such as Google Photos may lose features, delete data (e.g., face information), impose quotas, or reduce photo quality. NAS apps often perform poorly when run on typical home hardware, which is usually less powerful than professional setups. Immich stands out for being open-source (free software), fast, private, and having an active community, making it the preferred choice for many users.

### 1.1.2. Why this project?

When starting to use Immich, it is common to import large volumes of photos from older systems, where organization was done in folders or with other apps. This creates a challenge: many photos and videos remain unorganized or misclassified. Although Immich is powerful, manual classification can be slow and tedious. This project aims to make organization faster and easier through automatic rules and tagging.

### 1.1.3. What does this project solve?

This project automatically applies new tags to assets (photos and videos) in Immich, based on existing albums and tags. 

**In the context of this project, a photo is considered 'classified' if it either belongs to a set of albums (configurable) that are deemed to provide classification, or it has one or more tags (also configurable) that the user considers sufficient for classification.**

It helps to:
- Quickly detect which photos or videos are still unorganized.
- Highlight possible errors, such as assets classified under multiple conflicting criteria.
- Speed up the review and mass organization of your photo library.

## 1.2. Practical Use Case: How to Take Advantage of This Script

After the motivation, let's describe a practical use case for this tool. The script scans all your photos, trying to detect whether they have been classified, remain unclassified, or have multiple classifications (which could indicate an error).

**Step 1:** Review the pattern used to detect which albums are considered "classified". By default, any album whose name starts with a date is assumed to be an event and its photos are considered organized.

**Step 2:** There are also special tags for photos that do not belong to any album for a specific reason (e.g., memes automatically uploaded from mobile devices, which you do not want in any album). The script suggests using certain tags for these cases, so the user can label memes or other photos accordingly, and the script will take them into account.

**Step 3:** If the script finds a photo that is unclassified or classified in multiple places, it will use a special tag (by default, tags starting with `autotag_`). All of this is configurable in the user config file. This way, you can easily locate these photos from the Immich interface and decide what to do: add/remove them from albums, tag as meme, postpone, ignore, etc.

**Step 4:** After making corrections in Immich, you can rerun the script. It will remove the special tags from photos that have been resolved, so each run leaves fewer unclassified or conflicted photos. The user can keep iterating until the library is perfectly organized.

**Tips for Classification:**
- Use Immich's date view to quickly identify all photos from the same event and add them to an album.
- To find memes or photos that should be tagged to avoid being candidates for albums, use Immich's "find similar" feature (AI-powered), which helps you quickly locate and tag such photos in bulk.

## 1.3. Future Directions

With the logic for adding and removing tags now solved in this project, it becomes very easy to add new features. In the future, this tagging system and codebase could be extended to:

- Automatically create albums based on existing regular folder structures (e.g., import folder hierarchies as albums).
- Assist in the detection and management of duplicate folders or files within the photo library.
- Provide tools for batch operations or advanced organization workflows using tags as the main driver.
- Integrate with other automation or AI-based classification systems to further enhance photo management.

This foundation makes it straightforward to build more advanced features for organizing and maintaining large photo and video collections in Immich.

## 1.4. Installation and Automatic Client Generation

1. Clone the repository.
2. Run the script to create and activate the virtual environment, install dependencies, and generate the client:

```bash
source setup_venv.sh
```

This script:
- Creates and activates the `.venv` virtual environment.
- Installs external dependencies from `requirements.txt`.
- Installs `openapi-python-client` if not present.
- Automatically generates the `immich-client/` folder from the official OpenAPI spec if it does not exist.
- Installs the local client in editable mode.

3. If you want to regenerate the client, delete the `immich-client/` folder and rerun the script.

## 1.5. Execution

Run the main application:

```bash
./run_app.sh
```

## 1.6. Structure
- `main.py`: Main entry point for Immich AutoTag.
- `run_app.sh`: Script to launch the application.
- `setup_venv.sh`: Script to create the environment, install dependencies, and generate the client.
- `requirements.txt`: External project dependencies.
- `immich-client/`: Autogenerated client from OpenAPI.
- `immich_autotag/immich_user_config.py`: User-editable configuration (temporalmente dentro del paquete por motivos de refactorización).
- `immich_autotag/immich_user_config_template.py`: Configuration template without private data.
- `LICENSE`: GPL v3 license.
- `README.md`: This file.

## 1.7. Custom Configuration

For security reasons, **do not upload your `immich_user_config.py` file with private data** to the public repository.

Instead, use the template `immich_user_config_template.py`:

1. Copy the file `immich_autotag/immich_user_config_template.py` as `immich_autotag/immich_user_config.py`.
2. Edit the host, port, and API_KEY values to match your Immich instance.
3. Modify the tags and patterns as needed for your use case.

The template file does not contain sensitive information and can be uploaded to the repository as a reference for other users.



## 1.8. License
This project is licensed under the GNU GPL v3. See the LICENSE file for details.


# Immich user configuration template
# Copy this file to 'immich_user_config.py' and edit the values for your instance.


# DISCLAIMER: CONFIGURATION AS CODE (TEMPORARY)
# =============================================
# WARNING! This configuration is written as Python code and is located inside the main package for refactoring and development agility reasons.
# We are aware that this is unorthodox and not the recommended practice for mature projects.
# This decision is TEMPORARY and allows us to include small code fragments and logic in the configuration during this period of major changes.
# There is an open issue to decide the future of the configuration system and migrate to a more standard format once refactoring is complete.
# If you have questions or suggestions, please check the relevant issue and don't worry: this will be fixed!


# Immich host or domain (can be IP or DNS name)
# Example: "immich.example.com" or "192.168.1.100"
IMMICH_HOST = "immich.example.com"

# Port where Immich listens
IMMICH_PORT = 2283

# Immich API key (replace with your own key)
API_KEY = "YOUR_IMMICH_API_KEY_HERE"

# NOTE: We no longer use real tag hierarchy (slashes '/').
# All tags use underscores '_' instead of slashes. The namespace is only virtual/documentary.
# This avoids issues with Immich API and tag discovery, as hierarchical tags are not reliably supported.
CLASSIFIED_TAGS = [
    # TODO: Consider renaming CLASSIFIED_TAGS to something more semantically accurate (e.g., CLASSIFYING_TAGS),
    # since these are the tags used by the application to classify, not tags that are already classified.
    # This will help future maintainers understand the intent and avoid confusion.
    # Example tags (modify as needed for your use case)
    "meme",  # (LEGACY) Meme: humorous images, no prefix. Keep for compatibility.
    "adult_meme",  # (LEGACY) Adult meme: memes with sensitive/NSFW content, no prefix. Keep for compatibility.
    "autotag_input_ignore",  # Ignore: photos with no value, discarded from workflow
    # autotag_input_meme: Used to tag images (memes, jokes, viral content, etc.) that are uploaded indiscriminately from mobile devices to Immich.
    # These are not considered relevant family/event photos and should not be mixed with albums of vacations, events, or important memories.
    # This tag helps keep the main photo library focused on meaningful content, while still allowing you to keep memes and similar images for fun or reference.
    "autotag_input_meme",
    # autotag_input_adult_meme: Used to tag memes or images that are not suitable for all audiences (NSFW, adult, or sensitive content).
    # The purpose of this tag is to quickly identify and separate content that should not accidentally end up in family albums or be visible in general browsing.
    # This helps maintain a safe and appropriate environment in your main photo library, especially when sharing with family or children.
    "autotag_input_adult_meme",
    "autotag_input_pending_review",  # Pending review: photos postponed to decide their destination
]

# ALBUM_PATTERN defines which albums are considered "event albums" for classification purposes.
#
# Only albums whose names start with a date (e.g., '2023-', '2023-06', '2023-06-30') are treated as event albums.
# This means a photo should always belong to exactly one event album (matching this pattern) to be considered organized.
#
# Why use this pattern?
# - You may have other albums that are not events (e.g., collections about a person, a group, or a theme).
# - These non-event albums should NOT be considered for classification, so they are ignored by the script.
# - This approach lets you keep thematic or personal albums without affecting the event-based organization logic.
#
# You can adjust the pattern if your event album naming convention is different.
ALBUM_PATTERN = r"^\d{4}-(\d{2}(-\d{2})?)?"  # Matches: YYYY-, YYYY-MM or YYYY-MM-DD

# Tag conversions: legacy tag to new tag (origin -> destination)
# Each item is a dict with 'origin' and 'destination' keys
TAG_CONVERSIONS = [
    {"origin": "meme", "destination": "autotag_input_meme"},
    {"origin": "adult_meme", "destination": "autotag_input_adult_meme"},
]

# Output tags: no real hierarchy, use underscores
#
# AUTOTAG_CATEGORY_UNKNOWN: This tag is applied to assets (photos/videos) that could not be assigned to any event album (i.e., they do not match any group based on the event pattern).
# These are typically photos that are not yet organized, and need to be reviewed. You can use the Immich interface to filter by this tag and quickly find all unclassified assets.
# The goal is to ensure every photo belongs to exactly one event album or is intentionally excluded (e.g., meme, ignore, etc.).
AUTOTAG_CATEGORY_UNKNOWN = "autotag_output_unknown"
# TODO: refactorizar a AUTOTAG_CATEGORY_UNKNOWN
#
# AUTOTAG_CATEGORY_CONFLICT: This tag is applied to assets that are assigned to more than one event album (i.e., they match multiple groups, which is considered a classification conflict).
# The ideal is that each photo belongs to only one event album. If a photo is in several, it means the organization needs to be reviewed.
# Filtering by this tag in the Immich interface allows you to quickly focus on and resolve these conflicts: either by moving the photo to the correct album, removing it from extra albums, or reclassifying it (e.g., as meme or ignore).
AUTOTAG_CATEGORY_CONFLICT = "autotag_output_conflict"

# AUTOTAG_DUPLICATE_ASSET_ALBUM_CONFLICT: This tag is applied to assets that have a conflict of album assignment between duplicates (i.e., two or more duplicate assets are assigned to different event albums, which is an organizational inconsistency).
# Filtering by this tag in the Immich interface allows you to quickly find and resolve these duplicate album conflicts, ensuring that all duplicates are consistently organized.
AUTOTAG_DUPLICATE_ASSET_ALBUM_CONFLICT = "autotag_output_duplicate_asset_album_conflict"

# AUTOTAG_DUPLICATE_ASSET_CLASSIFICATION_CONFLICT: This tag is applied to assets that have a conflict of classification tags between duplicates (i.e., two or more duplicate assets have different classification tags, which is an organizational inconsistency).
# Filtering by this tag in the Immich interface allows you to quickly find and resolve these duplicate classification conflicts, ensuring that all duplicates are consistently organized.
AUTOTAG_DUPLICATE_ASSET_CLASSIFICATION_CONFLICT = (
    "autotag_output_duplicate_asset_classification_conflict"
)
# Prefix for group-specific duplicate classification conflict tag
AUTOTAG_DUPLICATE_ASSET_CLASSIFICATION_CONFLICT_PREFIX = (
    "autotag_output_duplicate_asset_classification_conflict_"
)


# Feature flag: Remove leading/trailing spaces from album names (default: True)
#
# When enabled, the autotag system will automatically clean up album names by removing any leading or trailing spaces
# when creating or updating albums. This helps avoid accidental duplicates and keeps album names tidy.
#
# Recommended: Keep enabled unless you have a specific reason to preserve spaces in album names.
ENABLE_ALBUM_NAME_STRIP = True

# Feature flag: Enable album detection from folder names (default: False)
ENABLE_ALBUM_DETECTION_FROM_FOLDERS = False

# Lista de patrones regex para excluir carpetas de la detección de álbumes por nombre de carpeta.
# Ejemplo: r"whatsapp" excluye cualquier carpeta que contenga 'whatsapp' en la ruta.
ALBUM_DETECTION_EXCLUDED_PATHS = [
    r"whatsapp",  # Excluye carpetas de WhatsApp
    # Añade aquí otros patrones si quieres excluir más carpetas
]

# Feature flag: Enable date correction for assets (default: False)
ENABLE_DATE_CORRECTION = False
# Zona horaria para fechas extraídas de nombres de archivo/carpeta (por defecto UTC, cambiar si tus fotos son siempre de otra zona)
DATE_EXTRACTION_TIMEZONE = "UTC"

# Global flag to control verbose logging throughout the application
VERBOSE_LOGGING = False

# Feature flag: Enable checkpoint resume (continue from last processed asset on restart).
# When enabled, the script will resume from the last processed asset using the checkpoint file.
# When disabled, the script will always start from the beginning (ignores checkpoint).
# Recommended: Enable for long runs or production. Disable for full reprocessing or debugging.
ENABLE_CHECKPOINT_RESUME = False

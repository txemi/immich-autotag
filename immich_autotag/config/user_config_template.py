"""
user_config_template.py

Configuration template for the Immich autotag system (without private data).
You can copy and adapt this file as user_config.py for your actual configuration.

This template is designed to be self-explanatory and easy to adapt. Each block includes comments to guide you.
"""

from immich_autotag.config.models import (
    AdvancedFeatureConfig,
    AlbumDetectionFromFoldersConfig,
    AutoTagsConfig,
    ClassificationRule,
    Conversion,
    DateCorrectionConfig,
    FeaturesConfig,
    ServerConfig,
    UserConfig,
)

user_config = UserConfig(
    # -------------------------------------------------------------------------
    # API and connection: Immich access credentials
    # host: Immich domain or IP
    # port: Port where Immich listens
    # api_key: Immich API key
    server=ServerConfig(
        host="immich.example.com", port=2283, api_key="YOUR_API_KEY_HERE"
    ),
    # -------------------------------------------------------------------------
    # ASSET FILTER: list of asset links or IDs to process.
    # If empty, all assets are processed. If not empty, only those indicated and detailed logging.
    filter_out_asset_links=[],
    # -------------------------------------------------------------------------
    # CLASSIFICATION AND RULES:
    # Rules to classify assets by tags or album name patterns.
    # Example: only albums starting with a date (YYYY-, YYYY-MM, YYYY-MM-DD) are considered "events".
    # NOTE: We no longer use real tag hierarchy (slashes '/').
    # All tags use underscores '_' instead of slashes. The namespace is only virtual/documentary.
    # This avoids issues with Immich API and tag discovery, as hierarchical tags are not reliably supported.
    classification_rules=[
        ClassificationRule(
            tag_names=[
                "meme",  # (LEGACY) Meme: humorous images, no prefix. Compatibility.
                "autotag_input_meme",  # Memes/jokes uploaded indiscriminately, not events.
            ]
        ),
        ClassificationRule(
            tag_names=[
                "adult_meme",  # (LEGACY) Adult meme: NSFW content, no prefix. Compatibility.
                "autotag_input_adult_meme",  # NSFW/adult memes, separate from family environment.
            ]
        ),
        ClassificationRule(
            tag_names=[
                "autotag_input_pending_review",  # Pending review: decide destination.
            ]
        ),
        ClassificationRule(
            tag_names=[
                "autotag_input_ignore",  # Ignore: photos discarded from main flow.
            ]
        ),
        ClassificationRule(
            album_name_patterns=[
                r"^\d{4}-(\d{2}(-\d{2})?)?"
            ]  # Only albums with a date name are considered "events"
        ),
    ],
    # -------------------------------------------------------------------------
    # TAG CONVERSIONS: mapping of old tags to new ones (compatibility/refactor)
    conversions=[
        Conversion(
            source=ClassificationRule(tag_names=["meme"]),
            destination=ClassificationRule(tag_names=["autotag_input_meme"]),
        ),
        Conversion(
            source=ClassificationRule(tag_names=["adult_meme"]),
            destination=ClassificationRule(tag_names=["autotag_input_adult_meme"]),
        ),
    ],
    # -------------------------------------------------------------------------
    # OUTPUT AND CONFLICT TAGS:
    # Configuration of automatic tags for unclassified assets, conflicts, duplicates, etc.
    # All tags use underscores '_' (no real hierarchy) to avoid issues with the Immich API.
    auto_tags=AutoTagsConfig(
        enabled=True,
        category_unknown="autotag_output_unknown",  # Assets not assigned to any event
        category_conflict="autotag_output_conflict",  # Assets in more than one event (conflict)
        duplicate_asset_album_conflict="autotag_output_duplicate_asset_album_conflict",  # Duplicates with album conflict
        duplicate_asset_classification_conflict="autotag_output_duplicate_asset_classification_conflict",  # Duplicates with classification conflict
        duplicate_asset_classification_conflict_prefix="autotag_output_duplicate_asset_classification_conflict_",  # Prefix for group conflicts
    ),
    # -------------------------------------------------------------------------
    # FEATURES AND FLAGS: enable/disable advanced features
    features=FeaturesConfig(
        enable_album_detection=True,  # Album detection by standard logic
        enable_tag_suggestion=False,  # Automatic tag suggestion (disabled)
        advanced_feature=AdvancedFeatureConfig(enabled=True, threshold=0.8),
        enable_album_name_strip=True,  # Trim spaces in album names
        album_detection_from_folders=AlbumDetectionFromFoldersConfig(
            enabled=False,  # Create albums from folders (disabled)
            excluded_paths=[r"whatsapp"],  # Exclude folders by pattern
        ),
        date_correction=DateCorrectionConfig(
            enabled=False,  # Date correction by file/folder name
            extraction_timezone="UTC",  # Timezone for date extraction
        ),
        enable_checkpoint_resume=False,  # Resume from last processed asset
    ),
)

if __name__ == "__main__":
    import pprint

    pprint.pprint(user_config.model_dump())

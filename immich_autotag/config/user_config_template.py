"""
user_config_template.py

Configuration template for the Immich autotag system (without private data).
You can copy and adapt this file as user_config.py for your actual configuration.

This template is designed to be self-explanatory and easy to adapt. Each block includes comments to guide you.
"""

from immich_autotag.config.models import (
    AlbumDetectionFromFoldersConfig,
    AlbumPermissionsConfig,
    AlbumSelectionRule,
    ClassificationConfig,
    ClassificationRule,
    Conversion,
    DateCorrectionConfig,
    DuplicateProcessingConfig,
    PerformanceConfig,
    ServerConfig,
    UserConfig,
    UserGroup,
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
    enable_album_name_strip=True,  # Trim spaces in album names
    enable_checkpoint_resume=True,  # Resume from last processed asset
    # -------------------------------------------------------------------------
    # ASSET FILTER: list of asset links or IDs to process.
    # If empty, all assets are processed. If not empty, only those indicated and detailed logging.
    filters=None,
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
    # CLASSIFICATION AND RULES:
    # Rules to classify assets by tags or album name patterns.
    # Example: only albums starting with a date (YYYY-, YYYY-MM, YYYY-MM-DD) are considered "events".
    # NOTE: We no longer use real tag hierarchy (slashes '/').
    # All tags use underscores '_' instead of slashes. The namespace is only virtual/documentary.
    # This avoids issues with Immich API and tag discovery, as hierarchical tags are not reliably supported.
    classification=ClassificationConfig(
        rules=[
            ClassificationRule(
                tag_names=[
                    "meme",  # (LEGACY) Meme: humorous images, no prefix. Compatibility.
                    "autotag_input_meme",  # Memes/jokes uploaded indiscriminately, not events.
                ],
                album_name_patterns=[
                    r"^autotag_input_meme$"  # Albums with exact name "autotag_input_meme"
                ],
            ),
            ClassificationRule(
                tag_names=[
                    "adult_meme",  # (LEGACY) Adult meme: NSFW content, no prefix. Compatibility.
                    "autotag_input_adult_meme",  # NSFW/adult memes, separate from family environment.
                ],
                album_name_patterns=[
                    r"^autotag_input_adult_meme$"  # Albums with exact name "autotag_input_adult_meme"
                ],
            ),
            ClassificationRule(
                tag_names=[
                    "autotag_input_pending_review",  # Pending review: decide destination.
                ],
                album_name_patterns=[
                    r"^autotag_input_pending_review$"  # Albums with exact name "autotag_input_pending_review"
                ],
            ),
            ClassificationRule(
                tag_names=[
                    "autotag_input_ignore",  # Ignore: photos discarded from main flow.
                ],
                album_name_patterns=[
                    r"^autotag_input_ignore$"  # Albums with exact name "autotag_input_ignore"
                ],
            ),
            ClassificationRule(
                album_name_patterns=[
                    r"^\d{4}-(\d{2}(-\d{2})?)?"
                ]  # Only albums with a date name are considered "events"
            ),
        ],
        autotag_unknown="autotag_output_unknown",  # Assets not assigned to any event
        autotag_conflict="autotag_output_conflict",  # Assets in more than one event (conflict)
        # create_album_from_date_if_missing: usa el valor por defecto (False) o pon True si lo deseas
    ),
    # -------------------------------------------------------------------------
    # DUPLICATE PROCESSING: configuration for handling duplicates
    duplicate_processing=DuplicateProcessingConfig(
        autotag_album_date_mismatch="autotag_output_album_date_mismatch",  # Duplicates with album date mismatch
        autotag_album_conflict="autotag_output_duplicate_asset_album_conflict",  # Duplicates with album conflict
        autotag_classification_conflict="autotag_output_duplicate_asset_classification_conflict",  # Duplicates with classification conflict
        autotag_classification_conflict_prefix="autotag_output_duplicate_asset_classification_conflict_",  # Prefix for group conflicts
        autotag_album_detection_conflict="autotag_output_album_detection_conflict",  # Multiple candidate folders for album detection
        date_correction=DateCorrectionConfig(
            enabled=True,  # Date correction by file/folder name
            extraction_timezone="UTC",  # Timezone for date extraction
        ),
    ),
    album_detection_from_folders=AlbumDetectionFromFoldersConfig(
        enabled=True,  # Create albums from folders (disabled)
        excluded_paths=[r"whatsapp"],  # Exclude folders by pattern
    ),
    create_album_from_date_if_missing=True,
    # -------------------------------------------------------------------------
    # ALBUM PERMISSIONS: Automatic album sharing to user groups based on keywords
    #
    # **IMPORTANT**: This configuration is the source of truth for album permissions.
    # Synchronization is COMPLETE: only members listed here will have access to matching albums.
    # Users removed from this config will automatically lose album access in Phase 2.
    #
    # Phase 1 (dry-run): Detect and log which albums would be shared (no API calls)
    # Phase 2 (production): Actually share albums with group members AND remove old ones
    #
    # Example: Albums named "2024-Familia-Vacation" contain "familia" → matched to familia group
    #
    # To enable, uncomment and customize:
    album_permissions=AlbumPermissionsConfig(
        enabled=True,  # Set to True to enable album permission detection
        user_groups=[
            UserGroup(
                name="familia",
                description="Family members",
                members=[
                    "abuelo@example.com",
                    "abuela@example.com",
                    "madre@example.com",
                ],
            ),
            UserGroup(
                name="amigos",
                description="Close friends",
                members=[
                    "juan@example.com",
                    "maria@example.com",
                ],
            ),
        ],
        selection_rules=[
            AlbumSelectionRule(
                name="Share Familia albums",
                keyword="familia",
                groups=["familia"],
                access="view",
            ),
            AlbumSelectionRule(
                name="Share Amigos albums",
                keyword="amigos",
                groups=["amigos"],
                access="view",
            ),
        ],
        log_unmatched=False,  # Set to True to log albums that don't match any rule
    ),
    # To disable, set to None or remove this line:
    # album_permissions=None,
    # -------------------------------------------------------------------------
    # PERFORMANCE: Tuning for production vs development
    performance=PerformanceConfig(
        enable_type_checking=True,  # Disable @typechecked in production (~50% perf improvement)
        # Set to True only for development/debugging to catch type errors early
    ),
    # Si necesitas advanced_feature, añádelo aquí como atributo propio
    # advanced_feature=AdvancedFeatureConfig(enabled=True, threshold=0.8),
)

if __name__ == "__main__":
    import pprint

    pprint.pprint(user_config.model_dump())

"""
user_config_template.py

Configuration template for the Immich autotag system (without private data).
You can copy and adapt this file as user_config.py for your actual configuration.

This template is designed to be self-explanatory and easy to adapt. Each block includes comments to guide you.
"""

from immich_autotag.config.models import (
    AlbumDateConsistencyConfig,
    AlbumDetectionFromFoldersConfig,
    AlbumPermissionsConfig,
    AlbumSelectionRule,
    ClassificationConfig,
    ClassificationRule,
    Conversion,
    DateCorrectionConfig,
    Destination,
    DuplicateProcessingConfig,
    FilterConfig,
    PerformanceConfig,
    ServerConfig,
    SkipConfig,
    UserConfig,
    UserGroup,
)

# Private module-level constants for repeated tag/album/group names
_AUTOTAG_INPUT_PREFIX = "autotag_input_"
_AUTOTAG_OUTPUT_PREFIX = "autotag_output_"
_FAMILY = "family"
_FRIENDS = "friends"
_ADULT_MEME_SUFFIX = "adult_meme"
_MEME_SUFFIX = "meme"
_PENDING_REVIEW_SUFFIX = "pending_review"
_IGNORE_SUFFIX = "ignore"
_UNKNOWN_SUFFIX = "unknown"
_CONFLICT_SUFFIX = "conflict"
_DUPLICATE_ASSET_ALBUM_CONFLICT_SUFFIX = "duplicate_asset_album_conflict"
_DUPLICATE_ASSET_CLASSIFICATION_CONFLICT_SUFFIX = (
    "duplicate_asset_classification_conflict"
)
_ALBUM_DETECTION_CONFLICT_SUFFIX = "album_detection_conflict"
_ALBUM_DATE_MISMATCH_SUFFIX = "album_date_mismatch"

_AUTOTAG_INPUT_ADULT_MEME = _AUTOTAG_INPUT_PREFIX + _ADULT_MEME_SUFFIX
_AUTOTAG_INPUT_MEME = _AUTOTAG_INPUT_PREFIX + _MEME_SUFFIX
_AUTOTAG_INPUT_PENDING_REVIEW = _AUTOTAG_INPUT_PREFIX + _PENDING_REVIEW_SUFFIX
_AUTOTAG_INPUT_IGNORE = _AUTOTAG_INPUT_PREFIX + _IGNORE_SUFFIX
_ADULT_MEME = _ADULT_MEME_SUFFIX

_AUTOTAG_OUTPUT_UNKNOWN = _AUTOTAG_OUTPUT_PREFIX + _UNKNOWN_SUFFIX
_AUTOTAG_OUTPUT_CONFLICT = _AUTOTAG_OUTPUT_PREFIX + _CONFLICT_SUFFIX
_AUTOTAG_OUTPUT_DUPLICATE_ASSET_ALBUM_CONFLICT = (
    _AUTOTAG_OUTPUT_PREFIX + _DUPLICATE_ASSET_ALBUM_CONFLICT_SUFFIX
)
_AUTOTAG_OUTPUT_DUPLICATE_ASSET_CLASSIFICATION_CONFLICT = (
    _AUTOTAG_OUTPUT_PREFIX + _DUPLICATE_ASSET_CLASSIFICATION_CONFLICT_SUFFIX
)
_AUTOTAG_OUTPUT_DUPLICATE_ASSET_CLASSIFICATION_CONFLICT_PREFIX = (
    _AUTOTAG_OUTPUT_DUPLICATE_ASSET_CLASSIFICATION_CONFLICT + "_"
)
_AUTOTAG_OUTPUT_ALBUM_DETECTION_CONFLICT = (
    _AUTOTAG_OUTPUT_PREFIX + _ALBUM_DETECTION_CONFLICT_SUFFIX
)
_AUTOTAG_OUTPUT_ALBUM_DATE_MISMATCH = (
    _AUTOTAG_OUTPUT_PREFIX + _ALBUM_DATE_MISMATCH_SUFFIX
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
    skip=SkipConfig(skip_n=0, resume_previous=True),  # Resume from last processed asset
    # -------------------------------------------------------------------------
    # ASSET FILTER: list of asset links or IDs to process.
    # If empty, all assets are processed. If not empty, only those indicated and detailed logging.
    filters=FilterConfig(filter_in=[ClassificationRule(asset_links=[])]),
    # -------------------------------------------------------------------------
    # TAG CONVERSIONS: mapping of old tags to new ones (compatibility/refactor)
    conversions=[
        Conversion(
            source=ClassificationRule(tag_names=[_MEME_SUFFIX]),
            destination=Destination(tag_names=[_AUTOTAG_INPUT_MEME]),
        ),
        Conversion(
            source=ClassificationRule(tag_names=[_ADULT_MEME]),
            destination=Destination(tag_names=[_AUTOTAG_INPUT_ADULT_MEME]),
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
                    _MEME_SUFFIX,  # (LEGACY) Meme: humorous images, no prefix. Compatibility.
                    _AUTOTAG_INPUT_MEME,  # Memes/jokes uploaded indiscriminately, not events.
                ],
                album_name_patterns=[
                    rf"^{_AUTOTAG_INPUT_MEME}$"  # Albums with exact name
                ],
            ),
            ClassificationRule(
                tag_names=[
                    _ADULT_MEME,  # (LEGACY) Adult meme: NSFW content, no prefix. Compatibility.
                    _AUTOTAG_INPUT_ADULT_MEME,  # NSFW/adult memes, separate from family environment.
                ],
                album_name_patterns=[
                    rf"^{_AUTOTAG_INPUT_ADULT_MEME}$"  # Albums with exact name
                ],
            ),
            ClassificationRule(
                tag_names=[
                    _AUTOTAG_INPUT_PENDING_REVIEW,  # Pending review: decide destination.
                ],
                album_name_patterns=[
                    rf"^{_AUTOTAG_INPUT_PENDING_REVIEW}$"  # Albums with exact name
                ],
            ),
            ClassificationRule(
                tag_names=[
                    _AUTOTAG_INPUT_IGNORE,  # Ignore: photos discarded from main flow.
                ],
                album_name_patterns=[
                    rf"^{_AUTOTAG_INPUT_IGNORE}$"  # Albums with exact name
                ],
            ),
            ClassificationRule(
                album_name_patterns=[
                    r"^\d{4}-(\d{2}(-\d{2})?)?"
                ]  # Only albums with a date name are considered "events"
            ),
        ],
        autotag_unknown=_AUTOTAG_OUTPUT_UNKNOWN,  # Assets not assigned to any event
        autotag_conflict=_AUTOTAG_OUTPUT_CONFLICT,  # Assets in more than one event (conflict)
        # create_album_from_date_if_missing: use the default value (False) or set True if desired
    ),
    # -------------------------------------------------------------------------
    # DUPLICATE PROCESSING: configuration for handling duplicates
    duplicate_processing=DuplicateProcessingConfig(
        autotag_album_conflict=_AUTOTAG_OUTPUT_DUPLICATE_ASSET_ALBUM_CONFLICT,  # Duplicates with album conflict
        autotag_classification_conflict=_AUTOTAG_OUTPUT_DUPLICATE_ASSET_CLASSIFICATION_CONFLICT,  # Duplicates with classification conflict
        autotag_classification_conflict_prefix=_AUTOTAG_OUTPUT_DUPLICATE_ASSET_CLASSIFICATION_CONFLICT_PREFIX,  # Prefix for group conflicts
        autotag_album_detection_conflict=_AUTOTAG_OUTPUT_ALBUM_DETECTION_CONFLICT,  # Multiple candidate folders for album detection
        date_correction=DateCorrectionConfig(
            enabled=True,  # Date correction by file/folder name
            extraction_timezone="UTC",  # Timezone for date extraction
        ),
    ),
    # -------------------------------------------------------------------------
    # ALBUM DATE CONSISTENCY: check if asset dates match album dates
    album_date_consistency=AlbumDateConsistencyConfig(
        enabled=True,
        autotag_album_date_mismatch=_AUTOTAG_OUTPUT_ALBUM_DATE_MISMATCH,
        threshold_days=180,  # 6 months - gradually reduce as you fix mismatches (180->90->60->30->7)
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
                name=_FAMILY,
                description="Family members",
                members=[
                    "grandpa@example.com",
                    "grandma@example.com",
                    "mother@example.com",
                ],
            ),
            UserGroup(
                name=_FRIENDS,
                description="Close friends",
                members=[
                    "john@example.com",
                    "jane@example.com",
                ],
            ),
        ],
        selection_rules=[
            AlbumSelectionRule(
                name="Share Family albums",
                keyword=_FAMILY,
                groups=[_FAMILY],
                access="view",
            ),
            AlbumSelectionRule(
                name="Share Friends albums",
                keyword=_FRIENDS,
                groups=[_FRIENDS],
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
    # If you need advanced_feature, add it here as your own attribute
    # advanced_feature=AdvancedFeatureConfig(enabled=True, threshold=0.8),
)

if __name__ == "__main__":
    import pprint

    pprint.pprint(user_config.model_dump())

# Immich user configuration template
# Copy this file to 'immich_user_config.py' and edit the values for your instance.

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
    # Example tags (modify as needed for your use case)
    "meme",  # (LEGACY) Meme: humorous images, no prefix. Keep for compatibility.
    "adult_meme",  # (LEGACY) Adult meme: memes with sensitive/NSFW content, no prefix. Keep for compatibility.
    "autotag_input_ignore",  # Ignore: photos with no value, discarded from workflow
    "autotag_input_meme",  # Meme: humorous images, separated from personal content
    "autotag_input_adult_meme",  # Adult meme: memes with sensitive/NSFW content
    "autotag_input_pending_review",  # Pending review: photos postponed to decide their destination
]
ALBUM_PATTERN = r"^\d{4}-(\d{2}(-\d{2})?)?"  # Example: YYYY-, YYYY-MM or YYYY-MM-DD

# Output tags: no real hierarchy, use underscores
AUTOTAG_UNKNOWN_CATEGORY = "autotag_output_unknown"  # Output: unclassified asset
AUTOTAG_CONFLICT_CATEGORY = "autotag_output_conflict"  # Output: asset with classification conflict

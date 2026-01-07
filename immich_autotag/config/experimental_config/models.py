"""
models.py

Modelos Pydantic para la nueva configuración estructurada (experimental).
"""
from typing import List, Optional
from pydantic import BaseModel, Field

class ServerConfig(BaseModel):
    host: str
    port: int
    api_key: str

# todo: las dos siguientes clases las juntaria en una sola
class TagClassificationRule(BaseModel):
    tag_names: List[str]

class AlbumClassificationRule(BaseModel):
    album_name_patterns: List[str]

class Conversion(BaseModel):
    source: TagClassificationRule
    destination: TagClassificationRule

class AutoTagsConfig(BaseModel):
    enabled: bool
    category_unknown: str
    category_conflict: str
    duplicate_asset_album_conflict: str
    duplicate_asset_classification_conflict: str
    duplicate_asset_classification_conflict_prefix: str

# todo: esto no se que es , estaba en el fichero de config original?
class AdvancedFeatureConfig(BaseModel):
    enabled: bool
    threshold: float

class FeaturesConfig(BaseModel):
    enable_album_detection: bool
    enable_tag_suggestion: bool
    advanced_feature: Optional[AdvancedFeatureConfig]
    enable_album_name_strip: bool
    # todo: las dos siguientes están acopladas, podrían ser una clase 
    enable_album_detection_from_folders: bool
    album_detection_excluded_paths: List[str]
    # todo: las dos siguientes estan acopladas, podrían ser una clase
    enable_date_correction: bool
    date_extraction_timezone: str
    enable_checkpoint_resume: bool

class UserConfig(BaseModel):
    server: ServerConfig
    filter_out_asset_links: List[str]
    tag_classification_rules: List[TagClassificationRule]
    album_classification_rules: List[AlbumClassificationRule]
    conversions: List[Conversion]
    auto_tags: AutoTagsConfig
    features: FeaturesConfig

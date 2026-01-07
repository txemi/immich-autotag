"""
models.py

Modelos Pydantic para la nueva configuración estructurada (experimental).
"""
from typing import List, Optional
from pydantic import BaseModel, Field

class ServerConfig(BaseModel):
    host: str
    port: int
    use_ssl: bool

class ClassificationRule(BaseModel):
    type: str
    patterns: List[str]
    labels: List[str]

class Conversion(BaseModel):
    source: ClassificationRule
    destination: ClassificationRule

class AutoTag(BaseModel):
    name: str
    criteria: List[str]

class AutoTagsConfig(BaseModel):
    enabled: bool
    tags: List[AutoTag]

class AdvancedFeatureConfig(BaseModel):
    enabled: bool
    threshold: float

class FeaturesConfig(BaseModel):
    enable_album_detection: bool
    enable_tag_suggestion: bool
    advanced_feature: Optional[AdvancedFeatureConfig]

class UserConfig(BaseModel):
    server: ServerConfig
    classification_rules: List[ClassificationRule]
    conversions: List[Conversion]
    auto_tags: AutoTagsConfig
    features: FeaturesConfig

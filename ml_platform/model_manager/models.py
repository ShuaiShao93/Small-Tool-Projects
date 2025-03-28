from typing import List, Optional, Union

from pydantic import BaseModel


class File(BaseModel):
    filename: str
    rename_to: Optional[str] = None


class HuggingFaceModelSource(BaseModel):
    huggingface_repo: str
    huggingface_revision: str
    files: List[File]


class LocalModelSource(BaseModel):
    name: str
    files: List[File]


class ModelSourceConfig(BaseModel):
    source: Union[HuggingFaceModelSource, LocalModelSource]
    target_subdirectory: Optional[str] = None


class ModelBaseConfig(BaseModel):
    name: str
    wizard_path: str
    model_sources: List[ModelSourceConfig]
    target_path: Optional[str] = None


class ModelReferenceConfig(BaseModel):
    base: str


class ModelArtifactConfig(BaseModel):
    name: str
    models: List[ModelReferenceConfig]
    target_path: Optional[str] = None


class CustomerModelConfig(BaseModel):
    name: str
    artifacts: List[ModelArtifactConfig]

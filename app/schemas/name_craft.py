from typing import Dict, List, Literal

from pydantic import BaseModel, Field


class NameCraftRequest(BaseModel):
    project_name: str = Field(..., min_length=2, max_length=120, description="Human-friendly project name")
    project_type: Literal["enterprise", "startup", "personal", "weekend project"] = Field(
        ..., description="Project context type"
    )
    naming_preference: Literal["professional", "balanced", "fun"] = Field(
        default="balanced",
        description="Naming tone preference",
    )

    include_database: bool = Field(default=False)
    include_microservices: bool = Field(default=False)
    include_frontend_backend_separation: bool = Field(default=False)
    include_messaging_system: bool = Field(default=False)
    include_analytics: bool = Field(default=False)

    advanced_options_enabled: bool = Field(default=False)
    cloud_provider: Literal["none", "azure", "aws", "gcp"] = Field(default="none")
    infrastructure_style: Literal["managed", "containers", "serverless", "hybrid"] = Field(default="managed")
    devops_workflow: Literal["github-actions", "azure-devops", "gitlab-ci", "jenkins", "none"] = Field(
        default="github-actions"
    )
    microservices_architecture: Literal["monolith", "modular-monolith", "microservices"] = Field(
        default="monolith"
    )


class NameCraftResponse(BaseModel):
    project_name: str
    recommended_repository_name: str
    naming_pattern: str
    environment_names: List[str] = Field(default_factory=lambda: ["dev", "staging", "prod"])
    component_suggestions: Dict[str, List[str]] = Field(default_factory=dict)
    environment_prefixed_examples: Dict[str, List[str]] = Field(default_factory=dict)
    cloud_resource_suggestions: Dict[str, List[str] | Dict[str, List[str]]] = Field(default_factory=dict)
    notes: List[str] = Field(default_factory=list)

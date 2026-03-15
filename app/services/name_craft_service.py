import logging
import os
import re
from pathlib import Path

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langsmith import Client

from app.config import settings
from app.schemas.name_craft import NameCraftRequest, NameCraftResponse


logger = logging.getLogger(__name__)


class NameCraftService:
    def __init__(self) -> None:
        if settings.LANGCHAIN_TRACING_V2:
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            os.environ["LANGCHAIN_API_KEY"] = settings.LANGCHAIN_API_KEY or ""
            os.environ["LANGCHAIN_PROJECT"] = settings.LANGCHAIN_PROJECT or "faltuai-fun"

        self.langsmith_client = None
        try:
            self.langsmith_client = Client()
            logger.info("LangSmith client initialized for NameCraftService")
        except Exception as exc:
            logger.warning(f"LangSmith client initialization failed: {exc}")

        self.llm = ChatOpenAI(
            openai_api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_MODEL,
            temperature=0.35,
        )

        self.prompt_path = Path(__file__).resolve().parents[1] / "prompts" / "name_craft.md"

    def _load_system_prompt(self) -> str:
        if not self.prompt_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {self.prompt_path}")

        return self.prompt_path.read_text(encoding="utf-8").strip()

    @staticmethod
    def _slugify(value: str) -> str:
        lowered = (value or "").strip().lower()
        lowered = re.sub(r"[^a-z0-9\s-]", "", lowered)
        lowered = re.sub(r"[\s_]+", "-", lowered)
        lowered = re.sub(r"-+", "-", lowered).strip("-")
        return lowered or "project"

    def _filter_component_suggestions(self, request: NameCraftRequest, response: NameCraftResponse) -> None:
        selected_flags = {
            "database": request.include_database,
            "db": request.include_database,
            "microservice": request.include_microservices,
            "service": request.include_microservices,
            "frontend": request.include_frontend_backend_separation,
            "backend": request.include_frontend_backend_separation,
            "api": request.include_frontend_backend_separation,
            "messaging": request.include_messaging_system,
            "queue": request.include_messaging_system,
            "topic": request.include_messaging_system,
            "analytics": request.include_analytics,
            "tracking": request.include_analytics,
            "event": request.include_analytics,
        }

        filtered = {}
        for key, names in response.component_suggestions.items():
            lowered_key = key.lower()
            matches = [flag for token, flag in selected_flags.items() if token in lowered_key]
            if matches and not any(matches):
                continue
            filtered[key] = names[:3]

        response.component_suggestions = filtered

    def _normalize_cloud_resource_suggestions(
        self,
        cloud_resource_suggestions: dict,
    ) -> dict[str, list[str]]:
        normalized: dict[str, list[str]] = {}

        if not isinstance(cloud_resource_suggestions, dict):
            return normalized

        for key, value in cloud_resource_suggestions.items():
            key_text = str(key).strip().lower().replace(" ", "_")

            if isinstance(value, list):
                normalized[key_text] = [str(item) for item in value if isinstance(item, str) and item.strip()]
                continue

            if isinstance(value, dict):
                for nested_key, nested_value in value.items():
                    nested_key_text = str(nested_key).strip().lower().replace(" ", "_")
                    if isinstance(nested_value, list):
                        normalized[nested_key_text] = [
                            str(item) for item in nested_value if isinstance(item, str) and item.strip()
                        ]

        return normalized

    async def generate_names(self, request: NameCraftRequest) -> NameCraftResponse:
        normalized_project_name = (request.project_name or "").strip()
        if len(normalized_project_name) < 2:
            raise ValueError("Please provide a project name with at least 2 characters.")

        system_prompt = self._load_system_prompt()

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                (
                    "human",
                    (
                        "Generate naming suggestions with this input:\n"
                        "Project Name: {project_name}\n"
                        "Project Type: {project_type}\n"
                        "Naming Preference: {naming_preference}\n"
                        "Include Database: {include_database}\n"
                        "Include Microservices: {include_microservices}\n"
                        "Include Frontend/Backend Separation: {include_frontend_backend_separation}\n"
                        "Include Messaging System: {include_messaging_system}\n"
                        "Include Analytics: {include_analytics}\n"
                        "Advanced Options Enabled: {advanced_options_enabled}\n"
                        "Cloud Provider: {cloud_provider}\n"
                        "Infrastructure Style: {infrastructure_style}\n"
                        "DevOps Workflow: {devops_workflow}\n"
                        "Microservices Architecture: {microservices_architecture}"
                    ),
                ),
            ]
        )

        chain = prompt | self.llm.with_structured_output(NameCraftResponse)

        result = await chain.ainvoke(
            {
                "project_name": normalized_project_name,
                "project_type": request.project_type,
                "naming_preference": request.naming_preference,
                "include_database": request.include_database,
                "include_microservices": request.include_microservices,
                "include_frontend_backend_separation": request.include_frontend_backend_separation,
                "include_messaging_system": request.include_messaging_system,
                "include_analytics": request.include_analytics,
                "advanced_options_enabled": request.advanced_options_enabled,
                "cloud_provider": request.cloud_provider,
                "infrastructure_style": request.infrastructure_style,
                "devops_workflow": request.devops_workflow,
                "microservices_architecture": request.microservices_architecture,
            },
            config={"run_name": "name_craft_generator", "tags": ["name-craft", "micro-tools"]},
        )

        if isinstance(result, NameCraftResponse):
            validated = result
        else:
            validated = NameCraftResponse.model_validate(result)

        base_slug = self._slugify(normalized_project_name)
        if not validated.recommended_repository_name:
            validated.recommended_repository_name = f"{base_slug}-{request.project_type.replace(' ', '-') }"

        validated.recommended_repository_name = self._slugify(validated.recommended_repository_name)
        validated.project_name = validated.project_name or normalized_project_name

        validated.environment_names = [self._slugify(name) for name in (validated.environment_names or ["dev", "staging", "prod"])][:3]
        if len(validated.environment_names) < 3:
            validated.environment_names = ["dev", "staging", "prod"]

        for key in list(validated.component_suggestions.keys()):
            validated.component_suggestions[key] = [self._slugify(item) for item in validated.component_suggestions[key] if item][:3]

        for key in list(validated.environment_prefixed_examples.keys()):
            validated.environment_prefixed_examples[key] = [
                self._slugify(item) for item in validated.environment_prefixed_examples[key] if item
            ][:3]

        normalized_cloud_resources = self._normalize_cloud_resource_suggestions(validated.cloud_resource_suggestions)
        validated.cloud_resource_suggestions = {
            key: [self._slugify(item) for item in names if item][:3]
            for key, names in normalized_cloud_resources.items()
        }

        self._filter_component_suggestions(request, validated)

        if not request.advanced_options_enabled:
            validated.cloud_resource_suggestions = {}

        return validated


name_craft_service = NameCraftService()

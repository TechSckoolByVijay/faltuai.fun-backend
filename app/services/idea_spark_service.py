import logging
import os
from pathlib import Path

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langsmith import Client

from app.config import settings
from app.schemas.idea_spark import IdeaSparkRequest
from app.schemas.idea_spark import IdeaSparkResponse


logger = logging.getLogger(__name__)


class IdeaSparkService:
    def __init__(self) -> None:
        if settings.LANGCHAIN_TRACING_V2:
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            os.environ["LANGCHAIN_API_KEY"] = settings.LANGCHAIN_API_KEY or ""
            os.environ["LANGCHAIN_PROJECT"] = settings.LANGCHAIN_PROJECT or "faltuai-fun"

        self.langsmith_client = None
        try:
            self.langsmith_client = Client()
            logger.info("LangSmith client initialized for IdeaSparkService")
        except Exception as exc:
            logger.warning(f"LangSmith client initialization failed: {exc}")

        self.llm = ChatOpenAI(
            openai_api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_MODEL,
            temperature=0.7,
        )

        self.prompt_path = Path(__file__).resolve().parents[1] / "prompts" / "idea_spark.md"

    def _load_system_prompt(self) -> str:
        if not self.prompt_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {self.prompt_path}")

        return self.prompt_path.read_text(encoding="utf-8").strip()

    async def spark_ideas(self, request: IdeaSparkRequest) -> IdeaSparkResponse:
        normalized_phrase = (request.phrase or "").strip()

        if len(normalized_phrase) < 2:
            raise ValueError("Please enter at least 2 characters.")

        system_prompt = self._load_system_prompt()

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                (
                    "human",
                    (
                        "Generate 10 practical micro-ideas using this context:\n"
                        "Phrase: {phrase}\n"
                        "Time Available: {time_available}\n"
                        "What to Create: {create_type}\n"
                        "Skill Area: {skill_area}\n"
                        "Difficulty Level: {difficulty_level}"
                    ),
                ),
            ]
        )

        chain = prompt | self.llm.with_structured_output(IdeaSparkResponse)

        result = await chain.ainvoke(
            {
                "phrase": normalized_phrase,
                "time_available": request.time_available,
                "create_type": request.create_type,
                "skill_area": request.skill_area,
                "difficulty_level": request.difficulty_level,
            },
            config={"run_name": "idea_spark_generator", "tags": ["idea-spark", "micro-tools"]},
        )

        if isinstance(result, IdeaSparkResponse):
            validated = result
        else:
            validated = IdeaSparkResponse.model_validate(result)

        if len(validated.ideas) != 10:
            ideas = [item.strip() for item in validated.ideas if isinstance(item, str) and item.strip()]
            if len(ideas) >= 10:
                ideas = ideas[:10]
            else:
                ideas.extend([f"Quick experiment #{index}" for index in range(len(ideas) + 1, 11)])

            return IdeaSparkResponse(phrase=validated.phrase or normalized_phrase, ideas=ideas)

        return validated


idea_spark_service = IdeaSparkService()

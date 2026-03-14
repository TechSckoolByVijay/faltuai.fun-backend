import logging
import os
from pathlib import Path

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langsmith import Client

from app.config import settings
from app.schemas.cringe import CringeResponse


logger = logging.getLogger(__name__)


class CringeService:
    def __init__(self) -> None:
        if settings.LANGCHAIN_TRACING_V2:
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            os.environ["LANGCHAIN_API_KEY"] = settings.LANGCHAIN_API_KEY or ""
            os.environ["LANGCHAIN_PROJECT"] = settings.LANGCHAIN_PROJECT or "faltuai-fun"

        self.langsmith_client = None
        try:
            self.langsmith_client = Client()
            logger.info("LangSmith client initialized for CringeService")
        except Exception as exc:
            logger.warning(f"LangSmith client initialization failed: {exc}")

        self.llm = ChatOpenAI(
            openai_api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_MODEL,
            temperature=0.4,
        )

        self.prompt_path = Path(__file__).resolve().parents[1] / "prompts" / "cringe_analyzer.md"

    def _load_system_prompt(self) -> str:
        if not self.prompt_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {self.prompt_path}")

        return self.prompt_path.read_text(encoding="utf-8").strip()

    async def analyze_post(self, content: str) -> CringeResponse:
        cleaned_content = (content or "").strip()

        if len(cleaned_content) < 10:
            raise ValueError("Post content is too short. Please provide at least 10 characters.")

        system_prompt = self._load_system_prompt()

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                ("human", "Analyze this LinkedIn post and return only structured output:\n\n{content}"),
            ]
        )

        chain = prompt | self.llm.with_structured_output(CringeResponse)

        result = await chain.ainvoke(
            {"content": cleaned_content},
            config={"run_name": "linkedin_cringe_analyzer", "tags": ["cringe-meter", "linkedin"]},
        )

        if isinstance(result, CringeResponse):
            return result

        return CringeResponse.model_validate(result)


cringe_service = CringeService()

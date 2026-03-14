import logging
import os
import re
from pathlib import Path
from typing import TypedDict, Optional

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langsmith import Client

from app.config import settings
from app.schemas.email_smoothener import EmailDraftAssessment, EmailSmoothenerResponse


logger = logging.getLogger(__name__)


class EmailSmoothenerState(TypedDict):
    raw_text: str
    response: Optional[EmailSmoothenerResponse]
    error: Optional[str]


class EmailSmoothenerService:
    def __init__(self) -> None:
        if settings.LANGCHAIN_TRACING_V2:
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            os.environ["LANGCHAIN_API_KEY"] = settings.LANGCHAIN_API_KEY or ""
            os.environ["LANGCHAIN_PROJECT"] = settings.LANGCHAIN_PROJECT or "faltuai-fun"

        self.langsmith_client = None
        try:
            self.langsmith_client = Client()
            logger.info("LangSmith client initialized for EmailSmoothenerService")
        except Exception as exc:
            logger.warning(f"LangSmith client initialization failed: {exc}")

        self.llm = ChatOpenAI(
            openai_api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_MODEL,
            temperature=0.5,
        )

        self.prompt_path = Path(__file__).resolve().parents[1] / "prompts" / "esm_email_smoothener.md"
        self.graph = self._build_graph()

    def _load_system_prompt(self) -> str:
        if not self.prompt_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {self.prompt_path}")

        return self.prompt_path.read_text(encoding="utf-8").strip()

    def _build_graph(self):
        workflow = StateGraph(EmailSmoothenerState)
        workflow.add_node("smoothen_email", self._smoothen_email_node)
        workflow.add_edge(START, "smoothen_email")
        workflow.add_edge("smoothen_email", END)
        return workflow.compile()

    def _score_to_int(self, value: int) -> int:
        try:
            return max(0, min(100, int(value)))
        except Exception:
            return 0

    def _normalize_draft_assessment(self, assessment: EmailDraftAssessment) -> EmailDraftAssessment:
        clarity_score = self._score_to_int(assessment.clarity_score)
        politeness_score = self._score_to_int(assessment.politeness_score)
        formality_score = self._score_to_int(assessment.formality_score)

        average_score = (clarity_score + politeness_score + formality_score) / 3
        is_good_enough = average_score >= 80

        if is_good_enough:
            good_enough_message = (
                "Your draft is good enough to send. You can still try the suggested variations if you want a different tone."
            )
        else:
            good_enough_message = (
                "Your draft can be improved before sending. The suggested variations make it more professional, polite, and clearer."
            )

        tone_summary = (assessment.tone_summary or "").strip() or "Neutral"
        lowered_tone = tone_summary.lower()
        sounds_aggressive = assessment.sounds_aggressive or any(
            token in lowered_tone for token in ["aggressive", "harsh", "frustrat", "blunt", "angry"]
        )
        sounds_friendly = assessment.sounds_friendly or any(
            token in lowered_tone for token in ["friendly", "warm", "polite", "respectful"]
        )

        return assessment.model_copy(
            update={
                "clarity_score": clarity_score,
                "politeness_score": politeness_score,
                "formality_score": formality_score,
                "tone_summary": tone_summary,
                "sounds_aggressive": sounds_aggressive,
                "sounds_friendly": sounds_friendly,
                "is_good_enough": is_good_enough,
                "good_enough_message": good_enough_message,
            }
        )

    def _paragraphize_sentences(self, sentences: list[str]) -> str:
        cleaned = [sentence.strip() for sentence in sentences if sentence.strip()]
        if not cleaned:
            return "Please let me know your update when convenient."

        if len(cleaned) == 1:
            cleaned.append("Please let me know if you need any additional details from my side.")

        if len(cleaned) <= 3:
            return " ".join(cleaned)

        midpoint = max(2, len(cleaned) // 2)
        paragraph_one = " ".join(cleaned[:midpoint])
        paragraph_two = " ".join(cleaned[midpoint:])
        return f"{paragraph_one}\n\n{paragraph_two}"

    def _normalize_professional_email(self, email_text: str) -> str:
        raw = (email_text or "").replace("\r\n", "\n").replace("\r", "\n").strip()
        raw = raw.replace("```", "")

        lines = [line.strip() for line in raw.split("\n") if line.strip()]
        combined = " ".join(lines)
        combined = re.sub(r"\s+", " ", combined).strip()

        if not combined:
            return "Hello,\n\nPlease let me know your update when convenient.\n\nBest regards,"

        greeting_line = "Hello,"
        greeting_match = re.match(
            r"^(hello(?:\s+[a-zA-Z][^,]*)?|hi(?:\s+[a-zA-Z][^,]*)?|dear(?:\s+[a-zA-Z][^,]*)?|good\s+(?:morning|afternoon|evening)(?:\s+[a-zA-Z][^,]*)?)\s*,\s*(.*)$",
            combined,
            flags=re.IGNORECASE,
        )

        if greeting_match:
            greeting_line = f"{greeting_match.group(1).strip()},"
            combined = greeting_match.group(2).strip()
            if combined.lower().startswith("team,"):
                combined = combined[5:].strip()

        if not combined:
            combined = "Please let me know your update when convenient."

        sentence_parts = [
            part.strip()
            for part in re.split(r"(?<=[.!?])\s+", combined)
            if part.strip()
        ]
        if not sentence_parts:
            sentence_parts = [combined]

        if not sentence_parts:
            sentence_parts = ["Please let me know your update when convenient."]

        body_lines = sentence_parts

        signoff_pattern = re.compile(
            r"^(best regards|kind regards|regards|sincerely|thanks|thank you)[,!]?$",
            re.IGNORECASE,
        )
        signoff_line = "Best regards,"

        if body_lines and signoff_pattern.match(body_lines[-1]):
            signoff_line = body_lines.pop(-1)
            if not signoff_line.endswith(","):
                signoff_line = f"{signoff_line.rstrip('.!')},"

        body_lines = [line.strip() for line in body_lines if line.strip()]
        cleaned_body_lines = []
        for line in body_lines:
            trimmed_line = re.sub(
                r"\s*(best regards|kind regards|regards|sincerely|thanks|thank you|best)[,!]?\s*$",
                "",
                line,
                flags=re.IGNORECASE,
            ).strip()
            if trimmed_line:
                cleaned_body_lines.append(trimmed_line)
        body_lines = cleaned_body_lines

        if not body_lines:
            body_lines = ["Please let me know your update when convenient."]

        body_text = self._paragraphize_sentences(body_lines)
        return f"{greeting_line}\n\n{body_text}\n\n{signoff_line}"

    def _enforce_professional_email_format(self, response: EmailSmoothenerResponse) -> EmailSmoothenerResponse:
        normalized_variants = []
        for variant in response.variants:
            normalized_variants.append(
                variant.model_copy(
                    update={"smoothed_email": self._normalize_professional_email(variant.smoothed_email)}
                )
            )

        normalized_assessment = self._normalize_draft_assessment(response.draft_assessment)

        return response.model_copy(update={"draft_assessment": normalized_assessment, "variants": normalized_variants})

    async def _smoothen_email_node(self, state: EmailSmoothenerState) -> EmailSmoothenerState:
        try:
            system_prompt = self._load_system_prompt()
            prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", system_prompt),
                    (
                        "human",
                        "Raw draft:\n\n{raw_text}\n\nReturn exactly three variants with style keys: corporate_robot, kind_but_firm, no_nonsense. Also provide draft_assessment fields requested by schema.",
                    ),
                ]
            )

            chain = prompt | self.llm.with_structured_output(EmailSmoothenerResponse)
            result = await chain.ainvoke(
                {"raw_text": state["raw_text"]},
                config={"run_name": "esm_email_smoothener", "tags": ["email-smoothener", "langgraph"]},
            )

            parsed = result if isinstance(result, EmailSmoothenerResponse) else EmailSmoothenerResponse.model_validate(result)

            normalized_keys = {variant.style_key for variant in parsed.variants}
            expected_keys = {"corporate_robot", "kind_but_firm", "no_nonsense"}
            if normalized_keys != expected_keys or len(parsed.variants) != 3:
                raise RuntimeError(
                    "Model output missing required variants. Expected corporate_robot, kind_but_firm, no_nonsense."
                )

            parsed = self._enforce_professional_email_format(parsed)

            return {
                "raw_text": state["raw_text"],
                "response": parsed,
                "error": None,
            }
        except Exception as exc:
            logger.error(f"Email smoothening failed: {exc}")
            return {
                "raw_text": state["raw_text"],
                "response": None,
                "error": str(exc),
            }

    async def smoothen_email(self, raw_text: str) -> EmailSmoothenerResponse:
        cleaned_text = (raw_text or "").strip()
        if len(cleaned_text) < 10:
            raise ValueError("Email draft is too short. Please provide at least 10 characters.")

        result = await self.graph.ainvoke({
            "raw_text": cleaned_text,
            "response": None,
            "error": None,
        })

        if result.get("error"):
            raise RuntimeError(result["error"])

        response = result.get("response")
        if not response:
            raise RuntimeError("Failed to generate smoothed email variants.")

        return response


email_smoothener_service = EmailSmoothenerService()

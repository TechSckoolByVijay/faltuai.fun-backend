"""
LLM Pipeline — LangGraph-based agentic pipeline.

Graph: step_analyst → step_writer → step_critic → (loop or END, max 2 rewrites)

Priority people & custom topics are SEARCHED for (upstream in worker.py),
then boosted in scoring, then MANDATED in prompts — triple-enforced.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import List, Optional, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph

from app.config import settings
from app.schemas.lifestyle_newsletter import NormalizedContent

logger = logging.getLogger(__name__)

_QUALITY_RULES_PATH = Path(__file__).parent.parent.parent / "prompts" / "newsletter_quality.md"


def _load_quality_rules() -> str:
    try:
        return _QUALITY_RULES_PATH.read_text(encoding="utf-8")
    except Exception as exc:
        logger.warning("Could not load newsletter_quality.md: %s", exc)
        return ""


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

class PipelineState(TypedDict):
    items: List[dict]
    analyses: str
    script: str
    topics_follow: List[str]
    custom_topics: List[str]
    priority_people: List[str]
    presentation_mode: str
    critique: str
    rewrite_count: int


# ---------------------------------------------------------------------------
# LLM
# ---------------------------------------------------------------------------

def _llm(temperature: float = 0.85) -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.OPENAI_MODEL,
        api_key=settings.OPENAI_API_KEY,
        temperature=temperature,
    )


# ---------------------------------------------------------------------------
# Node 1 — analyst_node
# ---------------------------------------------------------------------------

async def analyst_node(state: PipelineState) -> PipelineState:
    items = state["items"]
    topics_follow = state.get("topics_follow") or []
    custom_topics = state.get("custom_topics") or []
    priority_people = state.get("priority_people") or []

    if not items:
        return {**state, "analyses": "⚠️ No content items were fetched this week."}

    # Build mandatory focus block
    mandates = []
    if priority_people:
        mandates.append(
            f"MANDATORY PEOPLE — you MUST include at least one story about each of the following "
            f"if any item references them (items with SOURCE=TOPIC_SEARCH were fetched specifically "
            f"for them): {', '.join(priority_people)}"
        )
    if custom_topics:
        mandates.append(f"MANDATORY TOPICS — weave in coverage of: {', '.join(custom_topics)}")
    if topics_follow:
        mandates.append(f"TOPIC INTERESTS (prioritise): {', '.join(topics_follow)}")

    focus_block = (
        "\n\n⚠️ EDITOR MANDATES (non-negotiable):\n" +
        "\n".join(f"  • {m}" for m in mandates) +
        "\n\nItems with SOURCE=TOPIC_SEARCH were fetched specifically for the above — they MUST appear."
        if mandates else ""
    )

    content_block = "\n\n".join(
        f"[{i+1}] SOURCE={item['source'].upper()} | CATEGORY={item.get('category', '?')}\n"
        f"TITLE: {item['title']}\n"
        f"CONTENT: {item['summary'][:600]}\n"
        f"URL: {item.get('url', '')}\n"
        f"ENGAGEMENT: {item.get('engagement_score', 0):.0f}"
        for i, item in enumerate(items)
    )

    messages = [
        SystemMessage(content=(
            "You are a senior editor for 'Faltu AI Weekly' — a punchy weekly digest of what's "
            "actually buzzing in AI right now. Your readers are developers and researchers who "
            "already know the basics — they need to know what happened THIS WEEK that they must not miss.\n\n"
            "RULES:\n"
            "- Never explain what AI or LLMs are.\n"
            "- Prioritise NOVELTY and BUZZ over evergreen topics.\n"
            "- Every item must answer 'why does this matter THIS WEEK?'\n"
            "- Only use facts from the provided content — never invent."
        )),
        HumanMessage(content=(
            f"Here are {len(items)} items from this week:\n\n{content_block}\n\n{focus_block}\n"
            "---\n"
            "Sort and analyse into these buckets. Pick the best spread across sources.\n\n"
            "## BIG STORY OF THE WEEK\n"
            "The single most buzzworthy development — product launch, viral paper, company drama, "
            "tool everyone's talking about. 4-5 sentences: what happened, why it's a big deal, "
            "what it signals, your honest take.\n\n"
            "## 3-5 QUICK UPDATES\n"
            "Other noteworthy things. Each: what happened + why it matters today (2 sentences).\n\n"
            "## TOP RESEARCH PAPERS\n"
            "1-2 papers being discussed or with practical implications. "
            "What was found + what should a developer DO differently?\n\n"
            "## TOP GITHUB REPOS\n"
            "1-3 trending/new repos. What it does, why it's getting attention, notable stats.\n\n"
            "## QUICK TUTORIAL\n"
            "One practical how-to: what you'd show, 3-4 numbered steps, why now.\n\n"
            "## TOP AI PRODUCTS\n"
            "1-3 product launches. What it does, who the target user is, the standout feature.\n\n"
            "Be honest — if a bucket has nothing good, write NONE.\n\n"
            "SOURCE RULES (mandatory — do not override):\n"
            "- Items with SOURCE=GITHUB **must** go into 'TOP GITHUB REPOS'. Do NOT put them in other buckets.\n"
            "- Items with SOURCE=PRODUCTHUNT **must** go into 'TOP AI PRODUCTS'. Do NOT put them in other buckets.\n"
            "- If no GITHUB items exist, write NONE for TOP GITHUB REPOS.\n"
            "- If no PRODUCTHUNT items exist, write NONE for TOP AI PRODUCTS."
        )),
    ]

    response = await _llm(temperature=0.7).ainvoke(messages)
    logger.info("analyst_node: %d chars, %d items", len(response.content), len(items))
    return {**state, "analyses": response.content}


# ---------------------------------------------------------------------------
# Node 2 — writer_node
# ---------------------------------------------------------------------------

async def writer_node(state: PipelineState) -> PipelineState:
    analyses = state["analyses"]
    topics_follow = state.get("topics_follow") or []
    custom_topics = state.get("custom_topics") or []
    priority_people = state.get("priority_people") or []
    presentation_mode = state.get("presentation_mode") or "news"
    quality_rules = _load_quality_rules()
    rewrite_count = state.get("rewrite_count", 0)
    critique = state.get("critique", "")

    # Mandatory note for the writer
    mandates = []
    if priority_people:
        mandates.append(
            f"MUST mention or feature: {', '.join(priority_people)} — "
            "at minimum name each person and what they did this week. Do NOT skip them."
        )
    if custom_topics:
        mandates.append(f"MUST weave in: {', '.join(custom_topics)}")
    if topics_follow:
        mandates.append(f"Prioritise angle: {', '.join(topics_follow)}")

    focus_hint = (
        "\n\n⚠️ MANDATORY WRITER NOTE (non-negotiable — reader specifically asked for these):\n" +
        "\n".join(f"  • {m}" for m in mandates)
        if mandates else ""
    )

    rewrite_hint = (
        f"\n\n⚠️ REWRITE REQUESTED (attempt {rewrite_count}).\n"
        f"Previous draft failed quality check:\n{critique}\n"
        "Fix ONLY the failing sections — keep what was already good."
        if rewrite_count > 0 and critique else ""
    )

    prev_draft_hint = (
        f"\n\nPREVIOUS DRAFT (revise this):\n{state.get('script', '')}"
        if rewrite_count > 0 and state.get("script") else ""
    )

    # ── PODCAST MODE ────────────────────────────────────────────────────
    if presentation_mode == "podcast":
        response = await _llm(temperature=0.92).ainvoke([
            SystemMessage(content=(
                "You are the producer of 'Faltu AI Weekly Podcast'.\n\n"
                "Write a two-speaker podcast dialogue between:\n"
                "  Speaker A: the curious host — sets context, asks sharp questions\n"
                "  Speaker B: the AI expert guest — deep analysis, contrarian takes\n\n"
                "Format EXACTLY as:\nSpeaker A: [line]\nSpeaker B: [line]\n...\n\n"
                "Rules:\n"
                "- Natural conversation, light debate, occasional humour\n"
                "- Cover all major stories from the analyst notes\n"
                "- Total script: ~700-900 words (~4 minutes)\n"
                "- Start with Speaker A with a punchy cold open\n"
                "- End with Speaker A: a forward-looking teaser"
            )),
            HumanMessage(content=(
                f"{focus_hint}\n\n{rewrite_hint}\n\n{prev_draft_hint}\n\n"
                f"ANALYST NOTES:\n{analyses}\n\n"
                "Write the full podcast dialogue now."
            )),
        ])
        logger.info("writer_node (podcast): %d chars (attempt %d)", len(response.content), rewrite_count + 1)
        return {**state, "script": response.content}

    # ── NEWS BULLETIN MODE ───────────────────────────────────────────────
    response = await _llm(temperature=0.92).ainvoke([
        SystemMessage(content=(
            "You are the editor-in-chief of 'Faltu AI Weekly'.\n\n"
            "Your ONE job: tell developers and AI practitioners what happened in AI THIS WEEK "
            "that they absolutely must know. Think of it as texting your smartest friend — "
            "casual, opinionated, specific, no fluff.\n\n"
            "=== QUALITY RULES ===\n"
            f"{quality_rules}\n"
            "=== END QUALITY RULES ===\n\n"
            "Output is Markdown. Use ## for sections, ### for sub-headings, **bold** for key terms, "
            "> blockquotes for editorial takes, --- for section dividers. "
            "Target: 900-1100 words (~4 min read).\n\n"
            "CRITICAL RULE: If the analyst wrote NONE for any section, **omit that section entirely** "
            "from the output. Do NOT write placeholder text, filler, apologies, or humorous empty-state messages. "
            "Simply skip the section header and move on."
        )),
        HumanMessage(content=(
            "Write this week's Faltu AI Weekly newsletter from the analyst notes below.\n\n"
            "EXACT SECTION ORDER:\n\n"
            "---\n\n## 👋 Introduction\n"
            "<3-4 sentences. Jump straight into the news energy. NO 'Welcome to this week's edition'.>\n\n"
            "---\n\n## 📰 Big Story of the Week\n### <Specific descriptive title>\n"
            "<200-250 words. Context, stakes, what coverage missed, who wins/loses. "
            "End with a > blockquote — your sharpest take.>\n\n"
            "---\n\n## ⚡ Quick Updates\n"
            "<3-5 updates as ### sub-headings. 2-3 sentences each — what happened AND why it matters THIS week.>\n\n"
            "---\n\n## 🔬 Top Research Papers\n"
            "<1-2 papers as ### sub-headings. Lead with practical implication first.>\n\n"
            "---\n\n## 🐙 Top GitHub Repos\n"
            "<1-3 repos as ### sub-headings. What problem, who uses it, what's technically interesting.>\n\n"
            "---\n\n## 📖 Quick Tutorial\n### How to <specific actionable title>\n"
            "<100-130 words. Goal, 4 numbered steps, link. Something you can start in 15 minutes.>\n\n"
            "---\n\n## 🛠️ Top AI Products\n"
            "<1-3 products as ### sub-headings. One sentence what it does, one sentence who should care.>\n\n"
            "---\n\n## 🎯 The Faltu Take\n"
            "<80-100 words. Connect the dots. Concrete prediction or recommendation. "
            "End with something that makes them look forward to next week.>\n\n"
            "---\n\n"
            f"{focus_hint}\n\n"
            f"{rewrite_hint}\n\n"
            f"{prev_draft_hint}\n\n"
            f"ANALYST NOTES:\n{analyses}\n\n"
            "Write the full newsletter now. Make every word count. Be human."
        )),
    ])
    logger.info("writer_node: %d chars (attempt %d)", len(response.content), rewrite_count + 1)
    return {**state, "script": response.content}


# ---------------------------------------------------------------------------
# Node 3 — critic_node
# ---------------------------------------------------------------------------

MAX_REWRITES = 2


async def critic_node(state: PipelineState) -> PipelineState:
    script = state.get("script", "")
    rewrite_count = state.get("rewrite_count", 0)
    quality_rules = _load_quality_rules()
    priority_people = state.get("priority_people") or []

    people_check = (
        f"\n8. Does the newsletter specifically mention or feature the following people: "
        f"{', '.join(priority_people)}? If not, that is a FAIL."
        if priority_people else ""
    )

    response = await _llm(temperature=0.3).ainvoke([
        SystemMessage(content=(
            "You are a brutally honest quality editor for 'Faltu AI Weekly'. "
            "Be specific — identify exact sentences or sections that fail."
        )),
        HumanMessage(content=(
            "Check this newsletter draft against the quality rules below.\n\n"
            "=== QUALITY RULES ===\n"
            f"{quality_rules}\n"
            "=== END QUALITY RULES ===\n\n"
            f"=== NEWSLETTER DRAFT ===\n{script}\n=== END DRAFT ===\n\n"
            "Evaluate:\n"
            "1. Does the intro hook without 'welcome' or 'this week's edition'?\n"
            "2. Does each section explain why this matters THIS WEEK?\n"
            "3. Is the tone conversational — human friend, not press release?\n"
            "4. Any passive voice or corporate filler phrases? List them.\n"
            "5. Word count roughly 900-1100 words?\n"
            "6. Does the Big Story have a sharp editorial take?\n"
            "7. Does The Faltu Take end with something forward-looking and specific?"
            f"{people_check}\n\n"
            "Respond EXACTLY:\n"
            "PASS: yes|no\n"
            "ISSUES: <comma-separated issues or 'none'>\n"
            "SECTIONS_TO_FIX: <section names or 'none'>"
        )),
    ])

    critique_text = response.content
    passed = "pass: yes" in critique_text.lower()
    logger.info("critic_node: passed=%s, rewrite_count=%d", passed, rewrite_count)
    return {
        **state,
        "critique": critique_text,
        "rewrite_count": rewrite_count + (0 if passed else 1),
    }


def _should_rewrite(state: PipelineState) -> str:
    critique = state.get("critique", "")
    rewrite_count = state.get("rewrite_count", 0)
    passed = "pass: yes" in critique.lower()
    if not passed and rewrite_count <= MAX_REWRITES:
        logger.info("critic: rewrite %d/%d", rewrite_count, MAX_REWRITES)
        return "rewrite"
    return "done"


# ---------------------------------------------------------------------------
# Graph
# ---------------------------------------------------------------------------

def _build_graph() -> StateGraph:
    graph = StateGraph(PipelineState)
    graph.add_node("step_analyst", analyst_node)
    graph.add_node("step_writer", writer_node)
    graph.add_node("step_critic", critic_node)
    graph.set_entry_point("step_analyst")
    graph.add_edge("step_analyst", "step_writer")
    graph.add_edge("step_writer", "step_critic")
    graph.add_conditional_edges(
        "step_critic",
        _should_rewrite,
        {"rewrite": "step_writer", "done": END},
    )
    return graph.compile()


_compiled_graph = _build_graph()


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

async def run_pipeline(
    items: List[NormalizedContent],
    topics_follow: Optional[List[str]] = None,
    topics_exclude: Optional[List[str]] = None,
    custom_topics: Optional[List[str]] = None,
    priority_people: Optional[List[str]] = None,
    presentation_mode: str = "news",
    progress_cb=None,
) -> str:
    """Run the full agentic pipeline. Returns final newsletter / podcast script."""
    if progress_cb:
        progress_cb(f"📚 Analyst categorising {len(items)} items…")

    # Score and sort: priority_people and custom_topics get boosted
    def _score(item: NormalizedContent) -> float:
        text = (item.title + " " + item.summary).lower()
        score = float(item.engagement_score or 0)
        for t in (custom_topics or []):
            if t.lower() in text:
                score += 5.0
        for p in (priority_people or []):
            if p.lower() in text:
                score += 8.0   # high boost so they surface first
        return score

    sorted_items = sorted(items, key=_score, reverse=True)

    initial_state: PipelineState = {
        "items": [item.model_dump() for item in sorted_items],
        "analyses": "",
        "script": "",
        "topics_follow": topics_follow or [],
        "custom_topics": custom_topics or [],
        "priority_people": priority_people or [],
        "presentation_mode": presentation_mode,
        "critique": "",
        "rewrite_count": 0,
    }

    if progress_cb:
        progress_cb("✍️ Writing newsletter (agentic self-review loop)…")

    final_state = await _compiled_graph.ainvoke(initial_state)

    rewrites = final_state.get("rewrite_count", 0)
    if rewrites > 0 and progress_cb:
        progress_cb(f"🔁 Quality check triggered {rewrites} rewrite(s) — final draft approved ✅")

    return final_state["script"]


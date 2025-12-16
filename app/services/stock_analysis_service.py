"""
Stock Fundamental Analysis Service using LangGraph
Provides REAL stock analysis using Serper API and LangGraph workflow
Integrates with database for storage and caching
"""
import logging
import os
import json
import hashlib
from typing import TypedDict, Dict, List, Optional
from datetime import datetime, timedelta
import uuid

# LangGraph and LangChain components
from langgraph.graph import StateGraph, END, START
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langgraph.checkpoint.memory import MemorySaver
from langchain.tools import tool
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_core.tools import Tool

# Local imports
from app.config import settings
from app.services.common.llm_service import LLMService
from app.services.data_sources.serper_agent import serper_agent

logger = logging.getLogger(__name__)


# --- 1. Define the Graph State ---

class StockAnalysisState(TypedDict):
    """
    Represents the state of the stock analysis workflow
    """
    user_question: str
    stock_symbol: str
    stock_name: str
    analysis_plan: str
    research_data: str
    drafted_sections: List[str]
    final_report: str
    model_name: str
    error: str


# --- 2. Define the Agent/Node Logic ---

class StockAnalysisAgent:
    """
    Core agent for stock fundamental analysis using LangGraph
    Uses common services for LLM and data fetching
    """

    def __init__(self):
        logger.info("Initializing StockAnalysisAgent...")

        # Use common LLM service instead of direct OpenAI
        self.llm_service = LLMService()
        self.model_name = "gpt-4o-mini"
        
        # LangSmith setup
        if settings.LANGCHAIN_TRACING_V2:
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            os.environ["LANGCHAIN_API_KEY"] = settings.LANGCHAIN_API_KEY or ""
            os.environ["LANGCHAIN_PROJECT"] = settings.LANGCHAIN_PROJECT or "faltuai-finance"
            logger.info(f"LangSmith tracing enabled - Project: {os.environ.get('LANGCHAIN_PROJECT')}")

        # Initialize Serper search wrapper for stock data
        self.search_wrapper = GoogleSerperAPIWrapper(
            serper_api_key=settings.SERPER_API_KEY,
            k=10
        )

        # Define the search tool using the wrapper
        self.search_tool = Tool(
            name="search_stock_data",
            description="Fetches real-time financial data, latest news, and institutional ratings for a stock.",
            func=self.search_wrapper.run
        )
        
        logger.info("StockAnalysisAgent initialized successfully")

    # --- Node 1: Research Planning ---

    def research_plan_node(self, state: StockAnalysisState) -> StockAnalysisState:
        """Generate detailed research plan for stock analysis"""
        logger.info("---Executing research_plan_node---")
        user_question = state["user_question"]

        system_message = """
You are a senior stock market analyst with deep expertise in:
- Fundamental analysis
- Sector and industry analysis
- Valuation methodologies

You produce institutional-quality equity research notes.
Be factual, structured, and balanced.
Crucially, **avoid speculation**. If real-time or numerical data is unavailable, explicitly state this or use illustrative, plausible assumptions.

Your current task is to create a detailed, ordered plan for a full Equity Research Report
based on the user's investment question.

**PLANNING REQUIREMENT 1 (Analytical Detail):** The plan for each section must specify the exact data or analytical task required. For example, instead of 'Financial Analysis,' write 'Calculate 5-year revenue CAGR and operating margin trends' and 'Perform DuPont analysis to identify key return drivers.'

**PLANNING REQUIREMENT 2 (Structure):** Your plan MUST strictly cover the following seven mandatory sections in order: 
1. Executive Summary & Recommendation
2. Company Overview & Business Model
3. Industry & Macro Analysis
4. Financial Analysis (Historical)
5. Valuation & Projections
6. Core Risks & Monitoring Indicators
7. Environmental, Social, and Governance (ESG) Considerations

Output ONLY the structured plan as a list of detailed bullet points.
"""

        prompt = f"User Question: {user_question}"
        
        try:
            analysis_plan = self.llm_service.call_sync(
                prompt=prompt,
                system_message=system_message,
                temperature=0.2,
                max_tokens=2000
            )
            
            logger.info(f"Analysis plan generated successfully")
            
            return {
                "analysis_plan": analysis_plan,
                "model_name": self.model_name
            }
        except Exception as e:
            logger.error(f"Error in research_plan_node: {e}")
            return {
                "error": f"Failed to generate research plan: {str(e)}"
            }

    # --- Node 2: Data Fetching ---

    def fetch_data_node(self, state: StockAnalysisState) -> StockAnalysisState:
        """
        Fetch real-time stock data using Serper API
        """
        logger.info("---Executing fetch_data_node---")
        user_question = state["user_question"]
        stock_symbol = state.get("stock_symbol", "")
        stock_name = state.get("stock_name", "")
        
        # Construct targeted search query
        if stock_symbol:
            search_query = f"Provide latest financial data (last quarter or last year), institutional buy/sell/hold recommendations, and recent news for {stock_symbol} {stock_name}"
        else:
            search_query = f"{user_question}. Provide latest financial data, institutional recommendations, and recent news."
        
        try:
            logger.info(f"Executing search with query: {search_query}")
            research_data = self.search_tool.run(search_query)
            logger.info(f"Search data retrieved successfully")

            return {
                "research_data": research_data
            }
        except Exception as e:
            logger.error(f"Error in fetch_data_node: {e}")
            return {
                "error": f"Failed to fetch data: {str(e)}"
            }

    # --- Node 3: Draft Sections ---

    def draft_sections_node(self, state: StockAnalysisState) -> StockAnalysisState:
        """
        Draft detailed sections using the analysis plan and fetched data
        """
        logger.info("---Executing draft_sections_node---")
        user_question = state["user_question"]
        analysis_plan = state["analysis_plan"]
        research_data = state["research_data"]
        drafted_sections = state.get("drafted_sections", [])

        current_report_draft = "\n\n".join(
            [s for s in drafted_sections if s != 'PLAN_COMPLETE']
        )
        
        system_message = f"""You are an expert Equity Research Analyst. Your task is to draft a comprehensive section of the financial report based on the provided analysis plan, the user's question, and the **real-time financial data** gathered from external sources.

**USE THE PROVIDED REAL-TIME DATA TO ENSURE ACCURACY AND CURRENCY.**

**USER QUESTION**: {user_question}

**ANALYSIS PLAN**: {analysis_plan}

**REAL-TIME DATA (CRITICAL)**:
{research_data}

**EXISTING REPORT DRAFT**:
{current_report_draft}

**INSTRUCTIONS**:
- Produce the *next* logical, high-quality, detailed section for the report according to the Analysis Plan.
- Ensure the report incorporates the latest financial figures and institutional recommendations from the 'REAL-TIME DATA' section above.
- If a valuation is required, use the data for the inputs (P/E multiples, cash flow data, growth rates, etc.) and perform the required calculation, showing your work.
- Return ONLY the content for the next section, formatted professionally with appropriate markdown headings (e.g., ## II. Segmental Breakdown). Do not include any meta-information or conversational text.
- Do not duplicate content already present in the 'EXISTING REPORT DRAFT'.
- **CRITICAL SIGNAL**: If the content of the 'EXISTING REPORT DRAFT' already satisfies all 7 mandatory sections in the Analysis Plan, return the phrase 'PLAN_COMPLETE' and nothing else.
"""

        prompt = "Generate the next section of the report based on the Analysis Plan."
        
        try:
            new_section = self.llm_service.call_sync(
                prompt=prompt,
                system_message=system_message,
                temperature=0.3,
                max_tokens=2000
            )

            drafted_sections.append(new_section)
            logger.info(f"Drafted section added. Total sections: {len(drafted_sections)}")

            return {
                "drafted_sections": drafted_sections
            }
        except Exception as e:
            logger.error(f"Error in draft_sections_node: {e}")
            return {
                "error": f"Failed to draft section: {str(e)}"
            }

    # --- Router for Conditional Edge ---
    
    def route_drafting(self, state: StockAnalysisState) -> str:
        """
        Determines the next step after attempting to draft a section
        """
        logger.info("---Executing route_drafting---")
        
        last_chunk = state["drafted_sections"][-1] if state["drafted_sections"] else ""

        if "PLAN_COMPLETE" in last_chunk:
            logger.info("Plan completion signal received. Proceeding to assemble report.")
            return "assemble_report"
        else:
            logger.info("More sections to draft. Looping back to drafting.")
            return "draft_sections"

    # --- Node 4: Final Report Assembly ---

    def assemble_report_node(self, state: StockAnalysisState) -> StockAnalysisState:
        """
        Assemble and finalize the complete stock analysis report
        """
        logger.info("---Executing assemble_report_node---")
        
        clean_drafted_sections = [
            s for s in state["drafted_sections"] if s != 'PLAN_COMPLETE'
        ]

        user_question = state["user_question"]
        full_draft = "\n\n".join(clean_drafted_sections)

        system_message = """You are a meticulous Senior Equity Research Editor. Your task is to take the drafted sections and finalize them into a single, cohesive, professional-grade investment report.

**INSTRUCTIONS**:
- Review the full draft for flow, consistency, and professionalism.
- Ensure the report's length is detailed enough (typically over 3,000 words for a report of this nature).
- Add a professional disclaimer at the end.
- Clearly state the three most critical **Assumptions** and the **Confidence Level (High/Medium/Low)** at the end of the report summary, just before the disclaimer.
- Return ONLY the final, complete report text. Do not include any introductory or meta-text.
"""

        prompt = f"User Question: {user_question}\n\nDrafted Report Content:\n\n{full_draft}"
        
        try:
            final_report = self.llm_service.call_sync(
                prompt=prompt,
                system_message=system_message,
                temperature=0.3,
                max_tokens=4000
            )
            
            logger.info(f"Final report compiled successfully")

            return {
                "final_report": final_report
            }
        except Exception as e:
            logger.error(f"Error in assemble_report_node: {e}")
            return {
                "error": f"Failed to compile final report: {str(e)}"
            }


# --- 3. Build and Configure the Graph ---

class StockAnalysisService:
    """
    LangGraph-based Stock Analysis Service
    Manages the workflow for comprehensive stock fundamental analysis
    """
    MAX_SECTIONS: int = 10

    def __init__(self):
        logger.info("Initializing StockAnalysisService...")
        self.memory_saver = MemorySaver()
        self.graph = self._build_graph()

    def _build_graph(self):
        """Build and compile the LangGraph state machine"""
        logger.info("Building LangGraph for stock analysis...")
        agent = StockAnalysisAgent()
        
        # Define the graph
        workflow = StateGraph(StockAnalysisState)
        
        # Add nodes
        workflow.add_node("research_plan", agent.research_plan_node)
        workflow.add_node("fetch_data", agent.fetch_data_node)
        workflow.add_node("draft_sections", agent.draft_sections_node)
        workflow.add_node("assemble_report", agent.assemble_report_node)
        
        # Define edges
        workflow.add_edge(START, "research_plan")
        workflow.add_edge("research_plan", "fetch_data")
        workflow.add_edge("fetch_data", "draft_sections")
        
        # Conditional edge for iterative drafting
        workflow.add_conditional_edges(
            "draft_sections",
            agent.route_drafting,
            {
                "assemble_report": "assemble_report",
                "draft_sections": "draft_sections",
            }
        )

        workflow.add_edge("assemble_report", END)
        
        # Compile the graph
        compiled_graph = workflow.compile(checkpointer=self.memory_saver)
        logger.info("LangGraph compiled successfully")
        return compiled_graph

    async def run_analysis(
        self, 
        user_question: str,
        stock_symbol: Optional[str] = None,
        stock_name: Optional[str] = None
    ) -> Dict:
        """
        Execute the complete stock analysis workflow
        """
        logger.info(f"Running stock analysis for question: {user_question}")
        
        # Generate unique thread ID
        thread_id = str(uuid.uuid4())
        
        # Configuration
        config = {
            "configurable": {"thread_id": thread_id},
            "tags": ["stock-analysis-langgraph"],
            "metadata": {"user_question": user_question},
            "recursion_limit": self.MAX_SECTIONS + 4,
        }

        # Initial state
        initial_state = {
            "user_question": user_question,
            "stock_symbol": stock_symbol or "",
            "stock_name": stock_name or "",
            "analysis_plan": "",
            "research_data": "",
            "drafted_sections": [],
            "final_report": "",
            "model_name": "gpt-4o-mini",
            "error": ""
        }

        # Run the graph
        final_state = {}
        try:
            async for state in self.graph.astream(initial_state, config=config):
                final_state = state
            
            logger.info("Stock analysis completed successfully")
            
            # Extract the actual state values
            if final_state:
                # LangGraph returns dict with node names as keys
                for node_name, node_state in final_state.items():
                    if isinstance(node_state, dict) and "final_report" in node_state:
                        final_state = node_state
                        break
            
            return {
                "question": final_state.get("user_question"),
                "stock_symbol": final_state.get("stock_symbol"),
                "stock_name": final_state.get("stock_name"),
                "analysis_plan": final_state.get("analysis_plan"),
                "research_data": final_state.get("research_data"),
                "final_report": final_state.get("final_report"),
                "model": final_state.get("model_name"),
                "error": final_state.get("error")
            }
        except Exception as e:
            logger.error(f"Error during stock analysis workflow: {e}")
            return {
                "question": user_question,
                "error": f"Analysis workflow failed: {str(e)}"
            }


# Create global service instance
stock_analysis_service = StockAnalysisService()

__all__ = ["stock_analysis_service", "StockAnalysisService"]

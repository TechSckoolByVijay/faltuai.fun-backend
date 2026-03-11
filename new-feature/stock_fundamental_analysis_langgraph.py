import logging
import os
from typing import TypedDict, Dict, Annotated, List
from app.config import settings
import uuid

# LangGraph and LangChain components
from langgraph.graph import StateGraph, END, START
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langgraph.checkpoint.memory import MemorySaver
from langchain.tools import tool
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_core.tools import Tool


# Simple logging
logger = logging.getLogger(__name__)

# --- 1. Define the Graph State ---

class ReportState(TypedDict):
    """
    Represents the state of our graph.
    
    The 'plan' will guide the report generation.
    'research_data' is new and holds the search results.
    'drafted_sections' will accumulate the content chunks.
    'final_report' will hold the complete, assembled report.
    """
    user_question: str
    analysis_plan: str
    research_data: str  
    drafted_sections: List[str]
    final_report: str
    model_name: str

# --- 2. Define the Agent/Node Logic (The 'Nodes') ---

class StockAnalystAgent:
    """
    The core agent managing the LLM interactions for different stages, now including a data fetching tool.
    """

    def __init__(self):
        logger.info("Initializing StockAnalystAgent...")

        # LangSmith setup (inherited from original file)
        if settings.LANGCHAIN_TRACING_V2:
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            os.environ["LANGCHAIN_API_KEY"] = settings.LANGCHAIN_API_KEY or ""
            os.environ["LANGCHAIN_PROJECT"] = settings.LANGCHAIN_PROJECT or "faltuai-finance"
            logger.info(
                f"LangSmith tracing enabled - Project: {os.environ.get('LANGCHAIN_PROJECT')}"
            )

        # LLM initialization
        self.llm = ChatOpenAI(
            # Assumes OPENAI_API_KEY is configured in settings
            openai_api_key=settings.OPENAI_API_KEY, 
            model=settings.OPENAI_MODEL,
            temperature=0.2,
        )

        self.model_name = settings.OPENAI_MODEL
        logger.info(f"Chat model initialized: {settings.OPENAI_MODEL}")
        self.google_api_key = settings.GOOGLE_SEARCH_API
        self.google_cse_id =  settings.GOOGLE_CSE_ID 
        self.SERPER_API_KEY = settings.SERPER_API_KEY
        self.search_wrapper = GoogleSerperAPIWrapper(
                                                serper_api_key=self.SERPER_API_KEY,
                                                k=10)

        # 2. Define the search tool using the wrapper's run method
        self.search_tool = Tool(
            name="search_finance_data",
            description="Uses the configured SERPER API KEY to fetch real-time financial data, latest news, and institutional buy/sell/hold ratings for a stock.",
            func=self.search_wrapper.run # This uses the wrapper's run method, which only takes the query string
        )
        
        logger.info("StockAnalystAgent initialized with live GoogleSearchAPIWrapper.")

    # --- Node 1: Research Planning (No change needed) ---

    def research_plan_node(self, state: ReportState) -> ReportState:
        logger.info("---Executing research_plan_node---")
        user_question = state["user_question"]

        prompt = ChatPromptTemplate.from_messages([
            ("system", """
             You are a senior stock market analyst with deep expertise in:
                           - Fundamental analysis
                           - Sector and industry analysis
                           - Valuation methodologies

                           You produce institutional-quality equity research notes.
                           Be factual, structured, and balanced.
                           Crucially, **avoid speculation**. If real-time or numerical data is unavailable, explicitly state this or use illustrative, plausible assumptions (e.g., 'Assuming a 15% revenue CAGR...'). Every conclusion must be supported by a clear analytical argument.
 
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
              """),
            ("human", f"User Question: {user_question}"),
        ])

        chain = prompt | self.llm | StrOutputParser()
        analysis_plan = chain.invoke({"user_question": user_question})
        print("--------------------1-------------------")
        #print(analysis_plan)
        logger.info(f"Analysis plan generated:\n{analysis_plan}")
        print("---------------------------------------")
        return {
            "user_question": user_question,
            "analysis_plan": analysis_plan,
            "drafted_sections": [],
            "final_report": "",
            "model_name": self.model_name,
        }


    # --- Node 2: Data Fetching (NEW) ---

    def fetch_data_node(self, state: ReportState) -> ReportState:
        """
        Generates targeted search queries based on the plan and fetches real-time data
        using the defined search tool.
        """
        logger.info("---Executing data_fetch_node---")
        user_question = state["user_question"]
        analysis_plan = state["analysis_plan"]
        
        # A simple query derived from the plan to get critical, real-time data
        #search_query = f"{user_question}. Provide latest financial data (last quarter or last year), institutional buy/sell/hold recommendations, and recent news."
        #search_query = f"Provide latest financial data (last quarter or last year), institutional buy/sell/hold recommendations, and recent news for reliance industries"
        search_query = f"Provide latest financial data (last quarter or last year) for IDRFC FIRST BANK"
        
        # Execute the search tool
        logger.info(f"Executing search with query: {search_query}")
        research_data = self.search_tool.run(search_query)
        print("-------------2---------------")
        logger.info(f"Search data execution completed:\n{research_data}")

        return {
            "research_data": research_data,
            "user_question": user_question,
            "analysis_plan": analysis_plan,
            "drafted_sections": state.get("drafted_sections", []),
            "final_report": "",
            "model_name": self.model_name
        }


    # --- Node 3: Draft Sections (MODIFIED) ---

    def draft_sections_node(self, state: ReportState) -> ReportState:
        """
        Uses the analysis plan and now the fetched data to draft detailed sections.
        """
        logger.info("---Executing draft_sections_node---")
        user_question = state["user_question"]
        analysis_plan = state["analysis_plan"]
        research_data = state["research_data"] # <-- NEW: Retrieve data
        drafted_sections = state.get("drafted_sections", [])

        current_report_draft = "\n\n".join(
            [s for s in drafted_sections if s != 'PLAN_COMPLETE'] # Exclude a prior signal if it existed
        )
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"""You are an expert Equity Research Analyst. Your task is to draft a comprehensive section of the financial report based on the provided analysis plan, the user's question, and crucially, the **real-time financial data** gathered from external sources.

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
                        
            """),
            # The human message is now simplified as all context is in the system message
            ("human", "Generate the next section of the report based on the Analysis Plan.")
        ])

        chain = prompt | self.llm | StrOutputParser()
        new_section = chain.invoke(state)

        drafted_sections.append(new_section)

        print("--------------------3-------------------")
        #print(new_section)
        #print(f"Total drafted sections (including signals): {len(drafted_sections)}")
        #print("---------------------------------------")

        logger.info(f"Drafted section added. Total sections: {len(drafted_sections)}")

        return {
            "drafted_sections": drafted_sections,
            "user_question": user_question,
            "analysis_plan": analysis_plan,
            "research_data": research_data,
            "model_name": self.model_name
        }


    # --- New Conditional Edge Function (Router) ---
    def route_drafting(self, state: ReportState) -> str:
        """
        Determines the next step after attempting to draft a section.
        """
        logger.info("---Executing route_drafting---")
        
        # Get the latest item added to the list (which is the result of the last draft_sections_node call)
        last_chunk = state["drafted_sections"][-1] if state["drafted_sections"] else ""

        if "PLAN_COMPLETE" in last_chunk:
            logger.info("Plan completion signal received. Proceeding to final report.")
            return "final_report"
        else:
            logger.info("More sections to draft. Looping back to drafting.")
            return "draft_sections"

    # --- Node 4: Final Report Assembly (No change needed) ---

    def final_report_node(self, state: ReportState) -> ReportState:
        logger.info("---Executing final_report_node---")
        
        # Filter out the 'PLAN_COMPLETE' signal if it was appended
        clean_drafted_sections = [
            s for s in state["drafted_sections"] if s != 'PLAN_COMPLETE'
        ]

        #drafted_sections = state["drafted_sections"]
        user_question = state["user_question"]

        # Concatenate all drafted sections
        full_draft = "\n\n".join(clean_drafted_sections)

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a meticulous Senior Equity Research Editor. Your task is to take the drafted sections and finalize them into a single, cohesive, professional-grade investment report.

            **INSTRUCTIONS**:
            - Review the full draft for flow, consistency, and professionalism.
            - Ensure the report's length is detailed enough (typically over 3,000 words for a report of this nature).
            - Add a professional disclaimer at the end.
            - Clearly state the three most critical **Assumptions** and the **Confidence Level (High/Medium/Low)** at the end of the report summary, just before the disclaimer.
            - Return ONLY the final, complete report text. Do not include any introductory or meta-text.
            """),
            ("human", f"User Question: {user_question}\n\nDrafted Report Content:\n\n{full_draft}"),
        ])

        chain = prompt | self.llm | StrOutputParser()
        final_report = chain.invoke({}) # Note: Chain should be passed the full state for full context.
        print("--------------------4-------------------")
        #print(final_report)
        #print("---------------------------------------")
        logger.info(f"Final report compiled:\n{final_report}")

        return {
            "final_report": final_report,
            "user_question": user_question,
            "analysis_plan": state["analysis_plan"],
            "drafted_sections": state["drafted_sections"],
            "model_name": state["model_name"]
        }


# --- 3. Build and Configure the Graph ---

class LangGraphStockAnalystService:
    # Set this to a reasonable limit, though the 'PLAN_COMPLETE' signal is the primary guardrail
    MAX_SECTIONS: int = 10 

    def __init__(self):
        logger.info("Initializing LangGraphStockAnalystService...")
        self.memory_saver = MemorySaver()
        self.graph = self._build_graph()

    def _build_graph(self):
        """Builds and compiles the LangGraph state machine."""
        logger.info("Building LangGraph...")
        agent = StockAnalystAgent()
        
        # Define the graph
        workflow = StateGraph(ReportState)
        
        # 1. Research Planning
        workflow.add_node("research_plan", agent.research_plan_node)
        
        # 2. Data Fetching (NEW NODE)
        workflow.add_node("fetch_data", agent.fetch_data_node)
        
        # 3. Draft Sections
        workflow.add_node("draft_sections", agent.draft_sections_node)
        
        # 4. Final Report Assembly
        workflow.add_node("final_report", agent.final_report_node)
        
        # Define the connections (Edges)
        workflow.add_edge(START, "research_plan")
        
        # New Connection: After planning, fetch data
        workflow.add_edge("research_plan", "fetch_data")
        
        # New Connection: After fetching data, draft sections
        workflow.add_edge("fetch_data", "draft_sections")
        
        # CRITICAL CHANGE: Conditional Edge for Iterative Drafting
        # The router decides whether to loop back to 'draft_sections' or proceed to 'final_report'
        workflow.add_conditional_edges(
            "draft_sections",
            agent.route_drafting,
            {
                "final_report": "final_report",
                "draft_sections": "draft_sections",
            }
        )

        workflow.add_edge("final_report", END)
        
        # Compile the graph
        self.graph = workflow.compile(checkpointer=self.memory_saver)
        logger.info("LangGraph compiled successfully.")
        return self.graph

    async def run_analysis(self, user_question: str) -> Dict:
        # ... (Method implementation remains the same) ...
        # [Placeholder for the original run_analysis implementation]
        logger.info(f"Running LangGraph analysis for question: {user_question}")
        
        # Generate a unique thread ID for the run
        thread_id = str(uuid.uuid4())
        
        # Configuration for the run (including LangSmith tracing if enabled)
        config = {
            "configurable": {"thread_id": thread_id},
            "tags": ["finance-analysis-langgraph"],
            "metadata": {"user_id": "dummy-user"},
            "recursion_limit": self.MAX_SECTIONS + 4, # Max sections + buffer
            "name": self.graph.name
        }

        # Initial state for the run
        initial_state = {
            "user_question": user_question,
            "analysis_plan": "",
            "research_data": "",
            "drafted_sections": [],
            "final_report": "",
            "model_name": settings.OPENAI_MODEL,
        }

        # Run the graph using the astream method and passing the config
        final_state = {}
        async for state in self.graph.astream(initial_state, config=config):
            # Update the final_state variable with the latest state from the generator
            final_state = state 

        logger.info("LangGraph analysis completed")

        # Use the last yielded state as the final result
        return {
            "question": final_state.get("user_question"),
            "analysis": final_state.get("final_report"),
            "model": final_state.get("model_name"),
        }

    def verify_langsmith_setup(self) -> Dict:
        # ... (Method implementation remains the same) ...
        # [Placeholder for the original verify_langsmith_setup implementation]
        return {
            "tracing_enabled": settings.LANGCHAIN_TRACING_V2,
            "api_key_configured": bool(
                settings.LANGCHAIN_API_KEY
                and settings.LANGCHAIN_API_KEY != "dummy-langsmith-key"
            ),
            "project_name": os.environ.get("LANGCHAIN_PROJECT"),
            "endpoint": settings.LANGCHAIN_ENDPOINT,
            "status": "configured"
            if settings.LANGCHAIN_TRACING_V2
            and settings.LANGCHAIN_API_KEY != "dummy-langsmith-key"
            else "not_configured",
        }


# Create global service instance
langgraph_stock_analyst_service = LangGraphStockAnalystService()

# Create global service instance
langgraph_stock_analyst_service = LangGraphStockAnalystService()

__all__ = ["langgraph_stock_analyst_service", "LangGraphStockAnalystService"]
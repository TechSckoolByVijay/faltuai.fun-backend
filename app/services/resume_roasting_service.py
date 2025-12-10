import logging
import os
from typing import Dict, List, Optional
from app.config import settings

# Simple logging
logger = logging.getLogger(__name__)

# LangChain components
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

class ResumeRoastingService:
    """Simple resume roasting service with LangSmith tracing"""
    
    def __init__(self):
        logger.info("Initializing ResumeRoastingService...")
        
        # Simple LangSmith setup - only set if tracing is enabled
        if settings.LANGCHAIN_TRACING_V2:
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            os.environ["LANGCHAIN_API_KEY"] = settings.LANGCHAIN_API_KEY or ""
            os.environ["LANGCHAIN_PROJECT"] = settings.LANGCHAIN_PROJECT or "faltuai-fun"
            logger.info(f"LangSmith tracing enabled - Project: {os.environ.get('LANGCHAIN_PROJECT')}")
        
        # Simple ChatOpenAI initialization
        self.llm = ChatOpenAI(
            openai_api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_MODEL,
            temperature=0.8
        )
        logger.info(f"ChatOpenAI initialized with model: {settings.OPENAI_MODEL}")
        
        # Simple roasting styles
        self.roast_styles = {
            "funny": {
                "name": "Funny Roast",
                "description": "Light-hearted, humorous critique",
                "system_prompt": "You are a witty career coach who gives funny but constructive feedback on resumes."
            },
            "professional": {
                "name": "Professional Review", 
                "description": "Constructive professional feedback",
                "system_prompt": "You are a professional HR expert providing constructive feedback on resumes."
            },
            "brutal": {
                "name": "Brutal Honesty",
                "description": "No-holds-barred honest critique", 
                "system_prompt": "You are a brutally honest hiring manager who doesn't sugarcoat feedback."
            },
            "constructive": {
                "name": "Constructive Feedback",
                "description": "Detailed improvement suggestions",
                "system_prompt": "You are a career counselor focused on helping people improve their resumes."
            }
        }
    
    def get_available_styles(self) -> Dict[str, Dict]:
        """Get available roasting styles"""
        return {k: {"name": v["name"], "description": v["description"]} 
                for k, v in self.roast_styles.items()}
    
    async def roast_resume(self, resume_text: str, style: str = "funny") -> Dict:
        """Simple resume roasting with LangSmith tracing"""
        logger.info(f"Starting resume roast - style: {style}")
        
        # Validate style
        if style not in self.roast_styles:
            style = "funny"
        
        style_config = self.roast_styles[style]
        
        # Create simple prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", style_config["system_prompt"]),
            ("human", "Please review this resume: {resume_text}")
        ])
        
        # Simple chain
        chain = prompt | self.llm | StrOutputParser()
        
        # Execute - LangSmith will automatically trace if enabled
        logger.info("Executing LangChain...")
        result = await chain.ainvoke({"resume_text": resume_text})
        logger.info(f"LangChain completed - {len(result)} chars")
        
        # Simple response
        return {
            "roast": result,
            "style": style,
            "suggestions": ["Improve formatting", "Add achievements", "Be more specific"],
            "confidence_score": 7.0
        }

# Create global service instance
resume_roasting_service = ResumeRoastingService()

# Export service
__all__ = ["resume_roasting_service", "ResumeRoastingService"]
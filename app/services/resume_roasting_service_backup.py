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

logger.info("LangChain components loaded")

logger = logging.getLogger(__name__)

class ResumeRoastingService:
    """
    Service for roasting resumes using LangChain and LangSmith
    """
    
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
        
        # Roasting styles and their prompts
        self.roast_styles = {
            "funny": {
                "name": "Funny Roast",
                "description": "Light-hearted, humorous critique",
                "system_prompt": "You are a witty career coach who gives funny but constructive feedback on resumes. Be humorous but not mean-spirited. Point out issues in a clever way while still being helpful."
            },
            "professional": {
                "name": "Professional Review",
                "description": "Constructive professional feedback",
                "system_prompt": "You are a professional HR expert providing constructive feedback on resumes. Be direct but respectful. Focus on improvements and best practices."
            },
            "brutal": {
                "name": "Brutal Honesty",
                "description": "No-holds-barred honest critique",
                "system_prompt": "You are a brutally honest hiring manager who doesn't sugarcoat feedback. Be direct and harsh but fair. Point out every flaw but also acknowledge strengths."
            },
            "constructive": {
                "name": "Constructive Feedback",
                "description": "Detailed improvement suggestions",
                "system_prompt": "You are a career counselor focused on helping people improve their resumes. Provide detailed, actionable feedback with specific suggestions for improvement."
            }
        }
    
    def get_available_styles(self) -> Dict[str, Dict]:
        """
        Get available roasting styles
        
        Returns:
            Dictionary of available styles
        """
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
    
    @traceable(
        name="resume_roasting_service",
        metadata=lambda self, resume_text, style: {
            "service": "resume_roasting", 
            "style": style,
            "input_length": len(resume_text)
        }
    )
    async def _roast_implementation(self, resume_text: str, style: str) -> Dict:
        """Core resume roasting implementation with explicit LangSmith tracing"""
        logger.info(f"🎯 Starting resume roasting - Style: {style}, Resume length: {len(resume_text)}")
        
        try:
            # Validate style
            if style not in self.roast_styles:
                logger.warning(f"Invalid style '{style}', defaulting to 'funny'")
                style = "funny"
            
            style_config = self.roast_styles[style]
            logger.info(f"Using style config: {style_config['name']}")
            
            # Process with LangChain and LangSmith tracing
            logger.info("🤖 Processing with LangChain and LangSmith tracing")
            
            # Use LangChain with LangSmith tracing - ALL AI calls go through this path
            prompt = ChatPromptTemplate.from_messages([
                    ("system", style_config["system_prompt"]),
                    ("human", """
                    Please review this resume and provide feedback in the requested style:
                    
                    RESUME CONTENT:
                    {resume_text}
                    
                    Please provide:
                    1. A {style_name} review of the overall resume
                    2. Specific issues you notice
                    3. Three actionable suggestions for improvement
                    4. A confidence score (1-10) for how hireable this person is
                    
                    Format your response clearly with sections for each part.
                    """)
            ])
            
            # Create the LangChain chain with proper tracing
            logger.info("🔗 Creating LangChain processing chain")
            
            # Verify tracing before creating chain
            await self._ensure_langsmith_tracing()
            
            # Create chain with named components for better tracing visibility
            chain = (
                {
                    "resume_text": RunnablePassthrough(),
                    "style_name": lambda x: style_config['name'].lower()
                }
                | prompt
                | self.llm.with_config({"run_name": f"resume_roast_{style}"})
                | StrOutputParser()
            )
            
            logger.info(f"📤 Invoking LangChain chain - Model: {settings.OPENAI_MODEL}")
            logger.info(f"🔍 LANGCHAIN_TRACING_V2: {os.environ.get('LANGCHAIN_TRACING_V2')}")
            logger.info(f"🔍 LANGCHAIN_PROJECT: {os.environ.get('LANGCHAIN_PROJECT')}")
            
            # Execute chain - LangChain should automatically trace this
            roast_content = await chain.ainvoke(
                resume_text,
                config={
                    "run_name": f"resume_roasting_{style}",
                    "tags": ["resume_roasting", style, "faltuai_fun"],
                    "metadata": {
                        "style": style,
                        "resume_length": len(resume_text),
                        "model": settings.OPENAI_MODEL
                    }
                }
            )
            
            logger.info(f"📥 Chain invocation completed - Response length: {len(roast_content)} characters")
            logger.info("✅ LangChain automatic tracing should capture full chain in LangSmith")
            
            # Log trace metadata for debugging
            logger.info(f"🏷️  Trace metadata: style={style}, input_length={len(resume_text)}, output_length={len(roast_content)}")
            
            # Extract suggestions (simple extraction - could be improved with better parsing)
            logger.info("📋 Extracting suggestions and confidence score from AI response")
            suggestions = self._extract_suggestions(roast_content)
            confidence_score = self._extract_confidence_score(roast_content)
            
            logger.info(f"📊 Extracted {len(suggestions)} suggestions, confidence score: {confidence_score}")
            
            result = {
                "roast": roast_content,
                "style": style,
                "suggestions": suggestions,
                "confidence_score": confidence_score
            }
            
            # Log successful completion
            logger.info(f"✅ Resume roasting completed successfully:")
            logger.info(f"   📝 Style: {style}")
            logger.info(f"   📏 Input length: {len(resume_text)} chars")
            logger.info(f"   📄 Output length: {len(roast_content)} chars")
            logger.info(f"   🎯 Suggestions count: {len(suggestions)}")
            logger.info(f"   📈 Confidence: {confidence_score}")
            
            if os.environ.get('LANGCHAIN_TRACING_V2') == 'true':
                logger.info("🔍 Check LangSmith dashboard for trace details")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error roasting resume: {str(e)}")
            logger.exception("Full error traceback:")
            # Return a fallback response
            return {
                "roast": f"Sorry, I couldn't roast your resume right now due to a technical issue. But hey, at least you uploaded something! That's more than most people do. 😄\n\nError: {str(e)}",
                "style": style,
                "suggestions": [
                    "Try again in a few moments",
                    "Check your internet connection",
                    "Make sure your resume has actual content"
                ],
                "confidence_score": 5.0
            }
    

    
    def _extract_suggestions(self, content: str) -> List[str]:
        """
        Extract suggestions from AI response
        
        Args:
            content: AI response content
            
        Returns:
            List of suggestions
        """
        # Simple extraction - look for numbered suggestions
        suggestions = []
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if any(line.startswith(f"{i}.") for i in range(1, 10)):
                # Remove the number and clean up
                suggestion = line[2:].strip()
                if suggestion:
                    suggestions.append(suggestion)
        
        # If no numbered suggestions found, provide generic ones
        if not suggestions:
            suggestions = [
                "Improve formatting and structure",
                "Add quantifiable achievements",
                "Tailor content to job requirements"
            ]
        
        return suggestions[:5]  # Return max 5 suggestions
    
    def _extract_confidence_score(self, content: str) -> Optional[float]:
        """
        Extract confidence score from AI response
        
        Args:
            content: AI response content
            
        Returns:
            Confidence score or None
        """
        import re
        
        # Look for patterns like "7/10", "7 out of 10", "Score: 7"
        patterns = [
            r'(\d+)/10',
            r'(\d+)\s+out\s+of\s+10',
            r'[Ss]core:?\s*(\d+)',
            r'[Cc]onfidence:?\s*(\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                try:
                    score = float(match.group(1))
                    return min(max(score, 1.0), 10.0)  # Clamp between 1-10
                except ValueError:
                    continue
        
        return 6.5  # Default score
    
    async def _ensure_langsmith_tracing(self) -> bool:
        """Ensure LangSmith tracing is properly configured"""
        logger.info("🔍 Verifying LangSmith tracing setup")
        
        # Check environment variables
        tracing_enabled = os.environ.get('LANGCHAIN_TRACING_V2', 'false').lower() == 'true'
        api_key_set = bool(os.environ.get('LANGCHAIN_API_KEY'))
        project_set = bool(os.environ.get('LANGCHAIN_PROJECT'))
        
        logger.info(f"LANGCHAIN_TRACING_V2: {tracing_enabled}")
        logger.info(f"API key set: {api_key_set}")
        logger.info(f"Project set: {project_set}")
        
        if tracing_enabled and api_key_set:
            logger.info("✅ LangSmith tracing properly configured")
            return True
        else:
            logger.warning("⚠️ LangSmith tracing not properly configured")
            return False

    async def _create_traced_chain(self, prompt, style: str):
        """Create a LangChain chain with proper tracing configuration"""
        return (
            {
                "resume_text": RunnablePassthrough(), 
                "style_name": lambda x: self.roast_styles[style]['name'].lower()
            }
            | prompt.with_config({"run_name": f"prompt_formatting_{style}"})
            | self.llm.with_config({"run_name": f"openai_generation_{style}"})
            | StrOutputParser().with_config({"run_name": f"output_parsing_{style}"})
        )
    
    def verify_langsmith_setup(self) -> Dict[str, any]:
        """Verify LangSmith configuration and connectivity"""
        logger.info("🔍 Verifying LangSmith setup...")
        
        status = {
            "langchain_available": True,  # Always available as required dependency
            "tracing_enabled": os.environ.get('LANGCHAIN_TRACING_V2', 'false').lower() == 'true',
            "api_key_set": bool(os.environ.get('LANGCHAIN_API_KEY')),
            "project_set": bool(os.environ.get('LANGCHAIN_PROJECT')),
            "endpoint": os.environ.get('LANGCHAIN_ENDPOINT', 'default')
        }
        
        logger.info(f"LangSmith Status: {status}")
        
        if all([status['tracing_enabled'], status['api_key_set']]):
            logger.info("✅ LangSmith fully configured")
            status['ready'] = True
        else:
            logger.warning("⚠️ LangSmith not fully configured")
            status['ready'] = False
            
        return status

# Create global service instance
resume_roasting_service = ResumeRoastingService()

# Export service
__all__ = ["resume_roasting_service", "ResumeRoastingService"]
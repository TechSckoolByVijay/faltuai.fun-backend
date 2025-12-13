"""
Common LLM Service Library
Provides reusable utilities for LLM interactions across the application
"""
import json
import asyncio
from typing import Dict, Any, Optional, List
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
import logging
import os

logger = logging.getLogger(__name__)

class LLMService:
    """Centralized service for all LLM operations"""
    
    def __init__(self):
        self.client = ChatOpenAI(
            model_name="gpt-4o-mini",
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            temperature=0.7,
            max_tokens=2000
        )
    
    async def call_async(
        self, 
        prompt: str, 
        system_message: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        json_response: bool = False
    ) -> str:
        """
        Generic async LLM call with configurable parameters
        """
        try:
            # Configure client for this call
            client = ChatOpenAI(
                model_name="gpt-4o-mini",
                openai_api_key=os.getenv("OPENAI_API_KEY"),
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            messages = []
            if system_message:
                messages.append(SystemMessage(content=system_message))
            
            if json_response:
                prompt += "\n\nIMPORTANT: Respond with valid JSON only, no additional text or formatting."
            
            messages.append(HumanMessage(content=prompt))
            
            response = await client.ainvoke(messages)
            return response.content.strip()
            
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise Exception(f"LLM service error: {str(e)}")
    
    def call_sync(
        self, 
        prompt: str, 
        system_message: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        json_response: bool = False
    ) -> str:
        """
        Synchronous LLM call wrapper
        """
        return asyncio.run(self.call_async(
            prompt=prompt,
            system_message=system_message,
            temperature=temperature,
            max_tokens=max_tokens,
            json_response=json_response
        ))
    
    async def generate_structured_response(
        self,
        prompt: str,
        schema_description: str,
        system_message: Optional[str] = None,
        temperature: float = 0.3
    ) -> Dict[str, Any]:
        """
        Generate structured JSON response following a specific schema
        """
        full_prompt = f"""
{prompt}

RESPONSE SCHEMA:
{schema_description}

Generate a valid JSON response matching the schema above.
"""
        
        response = await self.call_async(
            prompt=full_prompt,
            system_message=system_message,
            temperature=temperature,
            json_response=True
        )
        
        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {response}")
            raise Exception(f"Invalid JSON response from LLM: {str(e)}")
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """
        Multi-turn conversation completion
        messages format: [{"role": "system|user|assistant", "content": "..."}]
        """
        try:
            formatted_messages = []
            for msg in messages:
                if msg["role"] == "system":
                    formatted_messages.append(SystemMessage(content=msg["content"]))
                elif msg["role"] in ["user", "human"]:
                    formatted_messages.append(HumanMessage(content=msg["content"]))
                # Note: LangChain doesn't have direct AssistantMessage, would need AIMessage
            
            client = ChatOpenAI(
                model_name="gpt-4o-mini",
                openai_api_key=os.getenv("OPENAI_API_KEY"),
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            response = await client.ainvoke(formatted_messages)
            return response.content.strip()
            
        except Exception as e:
            logger.error(f"Chat completion failed: {e}")
            raise Exception(f"Chat completion error: {str(e)}")

# Global instance
llm_service = LLMService()
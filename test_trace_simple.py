#!/usr/bin/env python3
"""
Test script to check LangSmith trace creation with error handling
"""
import os
import logging
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Set up logging to see trace errors
logging.basicConfig(level=logging.DEBUG)

print(f"Testing LangSmith tracing - {datetime.now()}")
print(f"LANGCHAIN_TRACING_V2: {os.getenv('LANGCHAIN_TRACING_V2')}")
print(f"LANGCHAIN_PROJECT: {os.getenv('LANGCHAIN_PROJECT')}")

try:
    # Create a simple LangChain chain
    llm = ChatOpenAI(model="gpt-4", temperature=0.7)
    prompt = ChatPromptTemplate.from_template("Write a very short greeting for {name}")
    parser = StrOutputParser()
    chain = prompt | llm | parser
    
    print("Executing LangChain chain...")
    result = chain.invoke({"name": f"UI_TEST_{datetime.now().strftime('%H%M%S')}"})
    print(f"Chain result: {result[:100]}...")
    
    print("✅ Chain execution completed")
    print("Note: Traces are uploaded asynchronously, check LangSmith in a few moments")
    
except Exception as e:
    print(f"❌ Error executing chain: {e}")
    import traceback
    traceback.print_exc()
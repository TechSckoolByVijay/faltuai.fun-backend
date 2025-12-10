#!/usr/bin/env python3
"""
Test script to verify LangChain integration works
"""
import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from services.resume_roasting_service import ResumeRoastingService

async def test_langchain_integration():
    """Test the LangChain integration"""
    print("🧪 Testing LangChain Integration...")
    
    # Initialize the service
    service = ResumeRoastingService()
    
    # Test resume content
    test_resume = """
    John Doe
    Software Engineer
    
    Experience:
    - Worked at company for 2 years
    - Did some programming
    - Fixed bugs
    
    Skills:
    - Python
    - JavaScript
    - Excel
    """
    
    print("📝 Testing resume roasting with funny style...")
    
    try:
        # Test the roasting service
        result = await service.roast_resume(test_resume, "funny")
        
        print("✅ Success! Roast result:")
        print(f"Style: {result['style']}")
        print(f"Confidence Score: {result['confidence_score']}")
        print(f"Suggestions: {len(result['suggestions'])} items")
        print(f"Roast preview: {result['roast'][:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_langchain_integration())
    if success:
        print("🎉 LangChain integration test passed!")
    else:
        print("💥 LangChain integration test failed!")
    sys.exit(0 if success else 1)
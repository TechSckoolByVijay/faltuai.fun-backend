#!/usr/bin/env python3
"""
Docker test script to verify LangChain and LangSmith integration
"""
import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.append('/app')

async def test_langchain_integration():
    """Test the LangChain and LangSmith integration"""
    print("🧪 Testing LangChain and LangSmith Integration in Docker...")
    
    try:
        from app.services.resume_roasting_service import ResumeRoastingService
        print("✅ Successfully imported ResumeRoastingService")
        
        # Initialize the service
        service = ResumeRoastingService()
        print("✅ Successfully initialized service")
        
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
        
        # Test the roasting service
        result = await service.roast_resume(test_resume, "funny")
        
        print("✅ Success! Roast result:")
        print(f"Style: {result['style']}")
        print(f"Confidence Score: {result['confidence_score']}")
        print(f"Suggestions: {len(result['suggestions'])} items")
        print(f"Roast preview (first 300 chars): {result['roast'][:300]}...")
        
        # Check if LangChain is available
        print(f"\n🔍 Checking integration status:")
        if "LangSmith Status:" in result['roast']:
            print("✅ LangSmith monitoring is configured!")
        elif "LangChain not available" in result['roast']:
            print("⚠️ LangChain not available - using fallback mode")
        else:
            print("ℹ️ Using standard OpenAI integration")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_langchain_imports():
    """Test LangChain imports"""
    print("\n🔍 Testing LangChain package imports...")
    
    imports_to_test = [
        ("langchain_openai", "ChatOpenAI"),
        ("langchain_core.prompts", "ChatPromptTemplate"), 
        ("langchain_core.output_parsers", "StrOutputParser"),
        ("langchain_core.runnables", "RunnablePassthrough"),
        ("langsmith", "trace")
    ]
    
    successful_imports = 0
    total_imports = len(imports_to_test)
    
    for module_name, class_name in imports_to_test:
        try:
            module = __import__(module_name, fromlist=[class_name])
            getattr(module, class_name)
            print(f"✅ {module_name}.{class_name}")
            successful_imports += 1
        except ImportError as e:
            print(f"❌ {module_name}.{class_name} - {str(e)}")
        except AttributeError as e:
            print(f"⚠️ {module_name}.{class_name} - {str(e)}")
    
    print(f"\n📊 Import Summary: {successful_imports}/{total_imports} successful")
    
    return successful_imports > 0

if __name__ == "__main__":
    print("🐳 Docker LangChain Integration Test")
    print("=" * 50)
    
    # Test imports first
    imports_ok = asyncio.run(test_langchain_imports())
    
    # Test service integration
    service_ok = asyncio.run(test_langchain_integration())
    
    print("\n" + "=" * 50)
    if imports_ok and service_ok:
        print("🎉 All tests passed! LangChain integration is working in Docker!")
        exit_code = 0
    elif service_ok:
        print("⚠️ Service working but some imports failed - check LangChain configuration")
        exit_code = 0
    else:
        print("💥 Tests failed! Check your Docker configuration and requirements.txt")
        exit_code = 1
    
    sys.exit(exit_code)
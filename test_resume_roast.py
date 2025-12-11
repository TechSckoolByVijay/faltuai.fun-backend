#!/usr/bin/env python3
"""
Test script for resume roasting functionality
"""
import asyncio
import aiohttp
import json

BASE_URL = "https://faltuai.reddune-c0e74598.centralindia.azurecontainerapps.io"

async def test_endpoints():
    async with aiohttp.ClientSession() as session:
        print("🧪 Testing Resume Roasting Endpoints")
        print("=" * 50)
        
        # Test 1: Health check
        print("\n1. Testing health endpoint...")
        try:
            async with session.get(f"{BASE_URL}/health") as response:
                data = await response.json()
                print(f"   ✅ Health: {data}")
        except Exception as e:
            print(f"   ❌ Health failed: {e}")
        
        # Test 2: Database health
        print("\n2. Testing database health...")
        try:
            async with session.get(f"{BASE_URL}/health/db") as response:
                data = await response.json()
                print(f"   ✅ DB Health: {data}")
        except Exception as e:
            print(f"   ❌ DB Health failed: {e}")
        
        # Test 3: Test endpoint (no auth)
        print("\n3. Testing resume roast test endpoint...")
        try:
            async with session.get(f"{BASE_URL}/api/v1/resume-roast/test") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✅ Test roast successful!")
                    print(f"   🤖 Result: {data['result']['roast'][:100]}...")
                else:
                    error_text = await response.text()
                    print(f"   ❌ Test roast failed ({response.status}): {error_text}")
        except Exception as e:
            print(f"   ❌ Test roast failed: {e}")
        
        # Test 4: LangSmith status (no auth)
        print("\n4. Testing LangSmith status...")
        try:
            async with session.get(f"{BASE_URL}/api/v1/resume-roast/langsmith-status") as response:
                data = await response.json()
                print(f"   ✅ LangSmith Status: {data['langsmith_configuration']['status']}")
        except Exception as e:
            print(f"   ❌ LangSmith status failed: {e}")
        
        # Test 5: Styles endpoint (requires auth)
        print("\n5. Testing styles endpoint (should require auth)...")
        try:
            async with session.get(f"{BASE_URL}/api/v1/resume-roast/styles") as response:
                if response.status == 403:
                    print(f"   ✅ Styles endpoint properly requires authentication")
                else:
                    print(f"   ⚠️  Unexpected response: {response.status}")
        except Exception as e:
            print(f"   ❌ Styles test failed: {e}")
            
        print("\n" + "=" * 50)
        print("🎉 Testing complete!")

if __name__ == "__main__":
    asyncio.run(test_endpoints())
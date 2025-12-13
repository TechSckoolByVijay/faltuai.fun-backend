"""
Test script for Real Market Research System
Run this to verify all APIs are working correctly
"""

import asyncio
import sys
import os
from datetime import datetime

# Add app to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.data_sources.serper_agent import serper_agent
from app.services.data_sources.github_trends_agent import github_trends_agent
from app.services.data_sources.hackernews_agent import hackernews_agent
from app.services.data_sources.youtube_agent import youtube_agent
from app.services.market_research_agent import market_research_agent


async def test_serper():
    """Test Serper API (Google Search)"""
    print("\n" + "="*60)
    print("🔍 Testing Serper API (Google Search)")
    print("="*60)
    
    try:
        # Test basic search
        result = await serper_agent.search("python developer jobs", num_results=5)
        
        if result.get('organic'):
            print(f"✅ SUCCESS: Found {len(result['organic'])} search results")
            print(f"   First result: {result['organic'][0].get('title', 'N/A')[:60]}...")
            return True
        else:
            error = result.get('error', 'Unknown error')
            print(f"❌ FAILED: {error}")
            if "API key" in error:
                print("   → Add SERPER_API_KEY to .env file")
                print("   → Get key from: https://serper.dev/")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


async def test_github():
    """Test GitHub API"""
    print("\n" + "="*60)
    print("🐙 Testing GitHub API")
    print("="*60)
    
    try:
        # Test repository search
        repos = await github_trends_agent.search_repositories(
            "python tutorial stars:>1000",
            per_page=5
        )
        
        if repos:
            print(f"✅ SUCCESS: Found {len(repos)} repositories")
            if repos:
                print(f"   Top repo: {repos[0].get('full_name')} ({repos[0].get('stargazers_count', 0):,} stars)")
            return True
        else:
            print("⚠️  WARNING: No results (may be rate limited)")
            print("   → Add GITHUB_TOKEN to .env for higher limits")
            print("   → Get token from: https://github.com/settings/tokens")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


async def test_hackernews():
    """Test HackerNews API"""
    print("\n" + "="*60)
    print("📰 Testing HackerNews API")
    print("="*60)
    
    try:
        # Test story search
        stories = await hackernews_agent.search_stories("hiring", limit=5)
        
        if stories:
            print(f"✅ SUCCESS: Found {len(stories)} stories")
            if stories:
                print(f"   Latest: {stories[0].get('title', 'N/A')[:60]}...")
            return True
        else:
            print("⚠️  WARNING: No results found")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


async def test_youtube():
    """Test YouTube Data API"""
    print("\n" + "="*60)
    print("▶️  Testing YouTube Data API")
    print("="*60)
    
    try:
        # Test video search
        videos = await youtube_agent.search_videos("python tutorial", max_results=5)
        
        if videos:
            print(f"✅ SUCCESS: Found {len(videos)} videos")
            if videos:
                snippet = videos[0].get('snippet', {})
                stats = videos[0].get('statistics', {})
                print(f"   Top video: {snippet.get('title', 'N/A')[:60]}...")
                print(f"   Views: {stats.get('view_count', 0):,}")
            return True
        else:
            print("⚠️  WARNING: No results (API key may not be configured)")
            print("   → YOUTUBE_API_KEY is optional")
            print("   → Get key from: https://console.cloud.google.com/")
            return False
            
    except Exception as e:
        if "API key not configured" in str(e):
            print("ℹ️  INFO: YouTube API not configured (optional)")
            print("   → Add YOUTUBE_API_KEY to .env for video recommendations")
            return None  # Optional, so not a failure
        else:
            print(f"❌ ERROR: {e}")
            return False


async def test_market_research():
    """Test full market research workflow"""
    print("\n" + "="*60)
    print("🎯 Testing Full Market Research Workflow")
    print("="*60)
    
    try:
        print("   Running comprehensive research for 'frontend'...")
        print("   This may take 30-60 seconds (real API calls)...")
        
        result = await market_research_agent.research_market_trends(
            topic="frontend",
            experience_level="intermediate"
        )
        
        if result:
            print(f"✅ SUCCESS: Market research completed")
            print(f"   Job postings analyzed: {result.get('market_demand', {}).get('job_postings_analyzed', 0)}")
            print(f"   Skills identified: {len(result.get('skill_gaps', {}).get('high_demand_skills', []))}")
            print(f"   Resources found: {result.get('learning_resources', {}).get('total_resources_found', 0)}")
            print(f"   Data sources: {', '.join(result.get('data_sources', []))}")
            return True
        else:
            print("❌ FAILED: No research data returned")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("🧪 Real Market Research System - API Tests")
    print(f"   Timestamp: {datetime.now().isoformat()}")
    print("="*60)
    
    results = {}
    
    # Test individual APIs
    results['serper'] = await test_serper()
    results['github'] = await test_github()
    results['hackernews'] = await test_hackernews()
    results['youtube'] = await test_youtube()
    
    # Test full workflow if Serper is working
    if results['serper']:
        results['market_research'] = await test_market_research()
    else:
        print("\n⚠️  Skipping full market research test (Serper API required)")
        results['market_research'] = False
    
    # Close API sessions
    await serper_agent.close()
    await github_trends_agent.close()
    await hackernews_agent.close()
    await youtube_agent.close()
    
    # Summary
    print("\n" + "="*60)
    print("📊 Test Summary")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v is True)
    failed = sum(1 for v in results.values() if v is False)
    optional = sum(1 for v in results.values() if v is None)
    total = len(results)
    
    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {failed}/{total}")
    if optional:
        print(f"ℹ️  Optional: {optional}/{total}")
    
    print("\nDetailed Results:")
    for test_name, result in results.items():
        status = "✅ PASS" if result is True else ("❌ FAIL" if result is False else "ℹ️  OPTIONAL")
        print(f"  {status}: {test_name}")
    
    print("\n" + "="*60)
    
    if results['serper'] and results['market_research']:
        print("🎉 System is READY for production!")
        print("\nNext steps:")
        print("  1. Test with learning plan generation")
        print("  2. Monitor API usage and costs")
        print("  3. Adjust cache settings if needed")
    elif results['serper']:
        print("⚠️  System is PARTIALLY ready")
        print("\nIssues:")
        if not results['market_research']:
            print("  - Full market research failed (check logs)")
        print("\nOptional improvements:")
        if not results['youtube']:
            print("  - Add YouTube API for video recommendations")
    else:
        print("❌ System is NOT ready - Serper API required")
        print("\nRequired action:")
        print("  1. Get Serper API key from https://serper.dev/")
        print("  2. Add to .env: SERPER_API_KEY=your_key_here")
        print("  3. Restart backend and run this test again")
    
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())

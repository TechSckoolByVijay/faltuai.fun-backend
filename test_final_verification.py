"""Final verification that real market research is working"""
import asyncio
from app.services.data_sources.serper_agent import SerperSearchAgent
from app.services.data_sources.github_trends_agent import GitHubTrendsAgent
from app.services.data_sources.youtube_agent import YouTubeResourceAgent

async def final_test():
    print("\n" + "=" * 70)
    print("FINAL VERIFICATION: REAL MARKET RESEARCH APIS")
    print("=" * 70)
    
    all_working = True
    
    # Test 1: Serper (Google Search)
    print("\n1️⃣  Serper API (Google Search for Jobs)")
    print("-" * 70)
    serper = SerperSearchAgent()
    try:
        result = await serper.search("python developer jobs 2025", num_results=5)
        if result and 'organic' in result and len(result['organic']) > 0:
            print(f"✅ WORKING: Found {len(result['organic'])} real job search results")
            print(f"   Example: {result['organic'][0].get('title', 'N/A')[:60]}...")
        else:
            print(f"❌ FAILED: No results")
            all_working = False
    except Exception as e:
        print(f"❌ ERROR: {str(e)[:100]}")
        all_working = False
    finally:
        await serper.close()
    
    # Test 2: GitHub
    print("\n2️⃣  GitHub API (Technology Trends)")
    print("-" * 70)
    github = GitHubTrendsAgent()
    try:
        repos = await github.search_repositories("react hooks tutorial stars:>500", per_page=5)
        if repos and len(repos) > 0:
            print(f"✅ WORKING: Found {len(repos)} real repositories")
            print(f"   Top: {repos[0].get('full_name')} ({repos[0].get('stargazers_count', 0):,} stars)")
        else:
            print(f"❌ FAILED: No repositories")
            all_working = False
    except Exception as e:
        print(f"❌ ERROR: {str(e)[:100]}")
        all_working = False
    finally:
        await github.close()
    
    # Test 3: YouTube
    print("\n3️⃣  YouTube API (Learning Resources)")
    print("-" * 70)
    youtube = YouTubeResourceAgent()
    try:
        videos = await youtube.search_videos("react hooks tutorial 2024", max_results=5)
        if videos and len(videos) > 0:
            print(f"✅ WORKING: Found {len(videos)} real educational videos")
            snippet = videos[0].get('snippet', {})
            stats = videos[0].get('statistics', {})
            print(f"   Top: {snippet.get('title', 'N/A')[:60]}...")
            print(f"   Views: {int(stats.get('view_count', 0)):,}")
        else:
            print(f"❌ FAILED: No videos")
            all_working = False
    except Exception as e:
        print(f"❌ ERROR: {str(e)[:100]}")
        all_working = False
    finally:
        await youtube.close()
    
    # Final Summary
    print("\n" + "=" * 70)
    print("FINAL RESULT")
    print("=" * 70)
    
    if all_working:
        print("\n🎉 SUCCESS! All real data APIs are working!")
        print("\nYour learning plan agent now uses:")
        print("  ✅ Real job postings from Google")
        print("  ✅ Real technology trends from GitHub")
        print("  ✅ Real learning content from YouTube")
        print("\n🚀 NO MORE FAKE DATA - Everything is from real sources!")
        print("\nNext steps:")
        print("  1. Generate a learning plan via API")
        print("  2. Verify it contains real job data and resources")
        print("  3. Monitor API usage in Serper/YouTube dashboards")
    else:
        print("\n⚠️  Some APIs failed - check configuration")
    
    print("=" * 70 + "\n")

if __name__ == '__main__':
    asyncio.run(final_test())

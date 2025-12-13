"""Test YouTube and GitHub API keys"""
import asyncio
import sys

from app.services.data_sources.youtube_agent import YouTubeResourceAgent
from app.services.data_sources.github_trends_agent import GitHubTrendsAgent

async def test_keys():
    print('Testing YouTube API Key...')
    print('-' * 50)
    youtube = YouTubeResourceAgent(api_key='AIzaSyAIW5krBT9LMHZ03OSvrS8_L86btdPjepc')
    youtube_working = False
    try:
        result = await youtube.search_videos('python tutorial', max_results=3)
        if result and len(result) > 0:
            print(f'✅ SUCCESS: Found {len(result)} videos')
            snippet = result[0].get('snippet', {})
            title = snippet.get('title', 'N/A')
            print(f'   First video: {title[:60]}...')
            stats = result[0].get('statistics', {})
            views = stats.get('view_count', 0)
            likes = stats.get('like_count', 0)
            print(f'   Views: {views:,}')
            print(f'   Likes: {likes:,}')
            youtube_working = True
        else:
            print(f'❌ FAILED: No results returned')
    except Exception as e:
        error_msg = str(e)[:200]
        print(f'❌ ERROR: {error_msg}')
    finally:
        await youtube.close()
    
    print()
    print('Testing GitHub Token...')
    print('-' * 50)
    github_token = os.getenv('GITHUB_TOKEN')
    github = GitHubTrendsAgent(api_token=github_token)
    github_working = False
    try:
        repos = await github.search_repositories('python tutorial stars:>1000', per_page=3)
        if repos and len(repos) > 0:
            print(f'✅ SUCCESS: Found {len(repos)} repositories')
            repo_name = repos[0].get('full_name')
            stars = repos[0].get('stargazers_count', 0)
            print(f'   Top repo: {repo_name} ({stars:,} stars)')
            github_working = True
        else:
            print(f'❌ FAILED: No results returned')
    except Exception as e:
        error_msg = str(e)[:200]
        print(f'❌ ERROR: {error_msg}')
    finally:
        await github.close()
    
    print()
    print('=' * 50)
    if youtube_working and github_working:
        print('🎉 BOTH API KEYS WORKING!')
        return 'both'
    elif youtube_working:
        print('✅ YouTube API working (GitHub failed)')
        return 'youtube'
    elif github_working:
        print('✅ GitHub Token working (YouTube failed)')
        return 'github'
    else:
        print('❌ BOTH KEYS FAILED')
        return 'none'

if __name__ == '__main__':
    result = asyncio.run(test_keys())
    print(f'\nRESULT: {result}')
    sys.exit(0 if result in ['both', 'youtube', 'github'] else 1)

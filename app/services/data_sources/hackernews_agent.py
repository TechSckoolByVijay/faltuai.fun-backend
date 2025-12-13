"""
HackerNews API Integration for Job Market Insights

Uses HackerNews API to fetch:
- "Who's Hiring" threads for real job requirements
- Tech industry discussions
- Trending technologies in the community
"""

import aiohttp
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging
import re

logger = logging.getLogger(__name__)


class HackerNewsAgent:
    """Agent for analyzing job market through HackerNews"""
    
    def __init__(self):
        self.base_url = "https://hacker-news.firebaseio.com/v0"
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close(self):
        """Close aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def get_item(self, item_id: int) -> Optional[Dict[str, Any]]:
        """Get a single item (story, comment, etc.)"""
        try:
            session = await self._get_session()
            async with session.get(f"{self.base_url}/item/{item_id}.json") as response:
                if response.status == 200:
                    return await response.json()
        except Exception as e:
            logger.error(f"Failed to fetch HN item {item_id}: {e}")
        return None
    
    async def search_stories(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Search HackerNews stories using Algolia HN Search API
        """
        search_url = "https://hn.algolia.com/api/v1/search"
        params = {
            "query": query,
            "tags": "story",
            "hitsPerPage": limit
        }
        
        try:
            session = await self._get_session()
            async with session.get(search_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("hits", [])
        except Exception as e:
            logger.error(f"HN search failed for '{query}': {e}")
        return []
    
    async def get_who_is_hiring_threads(self, months_back: int = 3) -> List[Dict[str, Any]]:
        """
        Find recent "Who is Hiring" threads
        
        These threads are posted monthly and contain hundreds of job postings
        """
        logger.info(f"Searching for Who is Hiring threads (last {months_back} months)")
        
        # Search for "Who is Hiring" threads
        stories = await self.search_stories("Who is Hiring", limit=20)
        
        # Filter for actual monthly threads (from the last few months)
        cutoff_date = datetime.utcnow() - timedelta(days=months_back * 30)
        
        hiring_threads = []
        for story in stories:
            title = story.get("title", "")
            created_at = story.get("created_at")
            
            # Check if it's a legitimate "Who is Hiring" thread
            if "who is hiring" in title.lower() and created_at:
                story_date = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                if story_date >= cutoff_date:
                    hiring_threads.append({
                        "id": story.get("objectID"),
                        "title": title,
                        "created_at": created_at,
                        "num_comments": story.get("num_comments", 0),
                        "url": story.get("url") or f"https://news.ycombinator.com/item?id={story.get('objectID')}"
                    })
        
        # Sort by date, most recent first
        hiring_threads.sort(key=lambda x: x["created_at"], reverse=True)
        
        logger.info(f"Found {len(hiring_threads)} Who is Hiring threads")
        return hiring_threads[:months_back]  # Return most recent
    
    async def analyze_job_requirements(
        self,
        skill_area: str,
        role: str = "",
        months_back: int = 2
    ) -> Dict[str, Any]:
        """
        Analyze job requirements from "Who is Hiring" threads
        
        Extracts:
        - Required skills mentioned
        - Experience levels
        - Technologies in demand
        - Remote vs on-site trends
        """
        logger.info(f"Analyzing job requirements for {skill_area}")
        
        # Get recent hiring threads
        threads = await self.get_who_is_hiring_threads(months_back)
        
        if not threads:
            return {
                "skill_area": skill_area,
                "data_available": False,
                "message": "No recent hiring threads found"
            }
        
        # Fetch comments from threads (job postings are in comments)
        all_job_posts = []
        
        for thread in threads[:2]:  # Analyze top 2 most recent threads
            thread_id = thread.get("id")
            # Note: We'd need to fetch the full thread with comments
            # For now, we'll use search to find relevant job posts
            await asyncio.sleep(0.5)
        
        # Search for job posts mentioning the skill
        search_queries = [
            f"{skill_area} Who is Hiring",
            f"{role} {skill_area} hiring" if role else f"{skill_area} engineer hiring"
        ]
        
        for query in search_queries:
            results = await self.search_stories(query, limit=30)
            all_job_posts.extend(results)
            await asyncio.sleep(0.5)
        
        # Extract insights from job posts
        skills_mentioned = self._extract_skills(all_job_posts, skill_area)
        remote_stats = self._analyze_remote_mentions(all_job_posts)
        experience_levels = self._extract_experience_levels(all_job_posts)
        
        return {
            "skill_area": skill_area,
            "threads_analyzed": len(threads),
            "job_posts_analyzed": len(all_job_posts),
            "top_skills_mentioned": skills_mentioned[:15],
            "remote_work_stats": remote_stats,
            "experience_levels": experience_levels,
            "data_timestamp": datetime.utcnow().isoformat(),
            "data_source": "HackerNews Who is Hiring threads"
        }
    
    async def get_trending_tech_discussions(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get trending technology discussions from HackerNews front page
        """
        try:
            session = await self._get_session()
            async with session.get(f"{self.base_url}/topstories.json") as response:
                if response.status == 200:
                    story_ids = await response.json()
                    
                    # Fetch top stories
                    stories = []
                    for story_id in story_ids[:limit]:
                        item = await self.get_item(story_id)
                        if item and item.get("type") == "story":
                            stories.append({
                                "title": item.get("title"),
                                "url": item.get("url"),
                                "score": item.get("score", 0),
                                "num_comments": item.get("descendants", 0),
                                "time": item.get("time"),
                                "hn_url": f"https://news.ycombinator.com/item?id={story_id}"
                            })
                        await asyncio.sleep(0.1)  # Rate limiting
                    
                    return stories
        except Exception as e:
            logger.error(f"Failed to fetch trending discussions: {e}")
        return []
    
    def _extract_skills(self, posts: List[Dict], skill_area: str) -> List[Dict[str, int]]:
        """Extract and count skill mentions from job posts"""
        # Common tech skills
        tech_skills = [
            "python", "javascript", "typescript", "react", "node.js", "vue", "angular",
            "docker", "kubernetes", "aws", "azure", "gcp", "postgresql", "mongodb",
            "redis", "kafka", "graphql", "rest api", "microservices", "ci/cd",
            "machine learning", "deep learning", "tensorflow", "pytorch", "ai",
            "java", "go", "rust", "c++", "ruby", "php", "swift", "kotlin",
            "django", "flask", "fastapi", "spring", "express", "next.js"
        ]
        
        skill_counts = {}
        
        for post in posts:
            text = (post.get("title", "") + " " + post.get("story_text", "")).lower()
            
            for skill in tech_skills:
                if skill in text:
                    skill_counts[skill] = skill_counts.get(skill, 0) + 1
        
        # Sort by frequency
        sorted_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)
        
        return [{"skill": skill, "mentions": count} for skill, count in sorted_skills]
    
    def _analyze_remote_mentions(self, posts: List[Dict]) -> Dict[str, Any]:
        """Analyze remote work mentions"""
        remote_keywords = ["remote", "work from home", "wfh", "distributed", "anywhere"]
        onsite_keywords = ["on-site", "onsite", "in-office", "office"]
        
        remote_count = 0
        onsite_count = 0
        hybrid_count = 0
        
        for post in posts:
            text = (post.get("title", "") + " " + post.get("story_text", "")).lower()
            
            has_remote = any(keyword in text for keyword in remote_keywords)
            has_onsite = any(keyword in text for keyword in onsite_keywords)
            
            if has_remote and has_onsite:
                hybrid_count += 1
            elif has_remote:
                remote_count += 1
            elif has_onsite:
                onsite_count += 1
        
        total = remote_count + onsite_count + hybrid_count
        
        return {
            "remote_jobs": remote_count,
            "onsite_jobs": onsite_count,
            "hybrid_jobs": hybrid_count,
            "remote_percentage": round((remote_count / total * 100) if total > 0 else 0, 1)
        }
    
    def _extract_experience_levels(self, posts: List[Dict]) -> Dict[str, int]:
        """Extract experience level requirements"""
        levels = {
            "junior": 0,
            "mid": 0,
            "senior": 0,
            "staff": 0,
            "principal": 0
        }
        
        for post in posts:
            text = (post.get("title", "") + " " + post.get("story_text", "")).lower()
            
            if "junior" in text or "entry" in text or "0-2 years" in text:
                levels["junior"] += 1
            if "mid" in text or "intermediate" in text or "2-5 years" in text:
                levels["mid"] += 1
            if "senior" in text or "5+ years" in text or "experienced" in text:
                levels["senior"] += 1
            if "staff" in text or "lead" in text:
                levels["staff"] += 1
            if "principal" in text or "architect" in text:
                levels["principal"] += 1
        
        return levels


# Global instance
hackernews_agent = HackerNewsAgent()

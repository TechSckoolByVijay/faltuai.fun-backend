"""
GitHub API Integration for Technology Trends and Adoption Metrics

Uses GitHub's public API to fetch:
- Repository growth trends (stars, forks, issues)
- Technology adoption rates
- Popular learning repositories
- Framework comparison metrics
"""

import aiohttp
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging
import os

logger = logging.getLogger(__name__)


class GitHubTrendsAgent:
    """Agent for analyzing technology trends using GitHub API"""
    
    def __init__(self, api_token: Optional[str] = None):
        self.api_token = api_token or os.getenv("GITHUB_TOKEN")
        self.base_url = "https://api.github.com"
        self.session: Optional[aiohttp.ClientSession] = None
        
        # GitHub API: 5000 requests/hour with auth, 60 without
        logger.info(f"GitHub API initialized {'with' if self.api_token else 'without'} authentication")
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session with GitHub auth"""
        if self.session is None or self.session.closed:
            headers = {
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "FaltuAI-Learning-Plan-Agent"
            }
            if self.api_token:
                headers["Authorization"] = f"token {self.api_token}"
            
            self.session = aiohttp.ClientSession(headers=headers)
        return self.session
    
    async def close(self):
        """Close aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def search_repositories(
        self,
        query: str,
        sort: str = "stars",
        order: str = "desc",
        per_page: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Search GitHub repositories
        
        Args:
            query: Search query (e.g., "language:python machine learning")
            sort: Sort by stars, forks, or updated
            order: asc or desc
            per_page: Results per page (max 100)
        """
        endpoint = f"{self.base_url}/search/repositories"
        params = {
            "q": query,
            "sort": sort,
            "order": order,
            "per_page": min(per_page, 100)
        }
        
        try:
            session = await self._get_session()
            async with session.get(endpoint, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    repos = data.get("items", [])
                    logger.info(f"Found {len(repos)} repositories for '{query}'")
                    return repos
                else:
                    error_text = await response.text()
                    logger.error(f"GitHub API error {response.status}: {error_text}")
                    return []
        except Exception as e:
            logger.error(f"GitHub search failed for '{query}': {e}")
            return []
    
    async def analyze_technology_adoption(
        self,
        technology: str,
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze adoption and growth of a specific technology
        
        Returns metrics like:
        - Total repositories using the technology
        - Growth rate (starred repos over time)
        - Popular frameworks/libraries
        - Community activity
        """
        logger.info(f"Analyzing technology adoption for {technology}")
        
        # Build search query
        query_parts = [technology]
        if language:
            query_parts.append(f"language:{language}")
        
        # Add filters for active, maintained repos
        query_parts.append("stars:>100")
        
        query = " ".join(query_parts)
        
        repos = await self.search_repositories(query, sort="stars", per_page=50)
        
        if not repos:
            return {"technology": technology, "data_available": False}
        
        # Calculate metrics
        total_stars = sum(repo.get("stargazers_count", 0) for repo in repos)
        total_forks = sum(repo.get("forks_count", 0) for repo in repos)
        avg_stars = total_stars / len(repos) if repos else 0
        
        # Get top repositories
        top_repos = sorted(repos, key=lambda r: r.get("stargazers_count", 0), reverse=True)[:10]
        
        # Extract common topics/tags
        all_topics = []
        for repo in repos:
            all_topics.extend(repo.get("topics", []))
        
        topic_counts = {}
        for topic in all_topics:
            topic_counts[topic] = topic_counts.get(topic, 0) + 1
        
        trending_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "technology": technology,
            "total_repositories": len(repos),
            "total_stars": total_stars,
            "total_forks": total_forks,
            "average_stars": round(avg_stars),
            "top_repositories": [
                {
                    "name": repo.get("full_name"),
                    "description": repo.get("description", ""),
                    "stars": repo.get("stargazers_count", 0),
                    "forks": repo.get("forks_count", 0),
                    "language": repo.get("language"),
                    "url": repo.get("html_url"),
                    "last_updated": repo.get("updated_at")
                }
                for repo in top_repos
            ],
            "trending_topics": [{"topic": topic, "count": count} for topic, count in trending_topics],
            "data_timestamp": datetime.utcnow().isoformat(),
            "data_source": "GitHub API"
        }
    
    async def find_learning_repositories(
        self,
        topic: str,
        experience_level: str = "beginner"
    ) -> List[Dict[str, Any]]:
        """
        Find popular learning repositories for a specific topic
        
        Searches for:
        - Tutorial repositories
        - Awesome lists
        - Sample projects
        - Documentation repos
        """
        logger.info(f"Finding learning repositories for {topic}")
        
        # Search queries for different types of learning resources
        queries = [
            f"{topic} tutorial stars:>50",
            f"awesome {topic} stars:>100",
            f"{topic} examples stars:>50",
            f"learn {topic} stars:>50"
        ]
        
        all_repos = []
        for query in queries:
            repos = await self.search_repositories(query, per_page=15)
            all_repos.extend(repos)
            await asyncio.sleep(0.5)  # Rate limiting
        
        # Deduplicate by repository ID
        seen_ids = set()
        unique_repos = []
        for repo in all_repos:
            repo_id = repo.get("id")
            if repo_id not in seen_ids:
                seen_ids.add(repo_id)
                unique_repos.append(repo)
        
        # Sort by stars and filter
        learning_repos = sorted(unique_repos, key=lambda r: r.get("stargazers_count", 0), reverse=True)[:20]
        
        return [
            {
                "name": repo.get("full_name"),
                "description": repo.get("description", ""),
                "stars": repo.get("stargazers_count", 0),
                "forks": repo.get("forks_count", 0),
                "url": repo.get("html_url"),
                "topics": repo.get("topics", []),
                "language": repo.get("language"),
                "last_updated": repo.get("updated_at"),
                "resource_type": self._classify_learning_repo(repo)
            }
            for repo in learning_repos
        ]
    
    async def compare_frameworks(
        self,
        frameworks: List[str],
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Compare popularity and adoption of multiple frameworks
        
        Example: Compare React, Vue, Angular
        """
        logger.info(f"Comparing frameworks: {', '.join(frameworks)}")
        
        comparison = {}
        
        for framework in frameworks:
            adoption_data = await self.analyze_technology_adoption(framework, language)
            comparison[framework] = {
                "total_repos": adoption_data.get("total_repositories", 0),
                "total_stars": adoption_data.get("total_stars", 0),
                "average_stars": adoption_data.get("average_stars", 0),
                "top_repo": adoption_data.get("top_repositories", [{}])[0] if adoption_data.get("top_repositories") else {}
            }
            await asyncio.sleep(0.5)  # Rate limiting
        
        # Rank frameworks by popularity
        ranked = sorted(
            comparison.items(),
            key=lambda x: x[1].get("total_stars", 0),
            reverse=True
        )
        
        return {
            "frameworks_compared": frameworks,
            "comparison_data": comparison,
            "popularity_ranking": [fw for fw, _ in ranked],
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "data_source": "GitHub API"
        }
    
    async def get_trending_repositories(
        self,
        language: Optional[str] = None,
        since: str = "weekly"
    ) -> List[Dict[str, Any]]:
        """
        Get trending repositories (using search with recent stars)
        
        Note: GitHub removed the trending API, so we approximate with search
        """
        # Create query for recently popular repos
        date_range = {
            "daily": 1,
            "weekly": 7,
            "monthly": 30
        }.get(since, 7)
        
        from_date = (datetime.utcnow() - timedelta(days=date_range)).strftime("%Y-%m-%d")
        
        query_parts = [f"created:>{from_date}", "stars:>50"]
        if language:
            query_parts.append(f"language:{language}")
        
        query = " ".join(query_parts)
        
        repos = await self.search_repositories(query, sort="stars", per_page=30)
        
        return [
            {
                "name": repo.get("full_name"),
                "description": repo.get("description", ""),
                "stars": repo.get("stargazers_count", 0),
                "language": repo.get("language"),
                "url": repo.get("html_url"),
                "created_at": repo.get("created_at")
            }
            for repo in repos[:15]
        ]
    
    def _classify_learning_repo(self, repo: Dict) -> str:
        """Classify the type of learning repository"""
        name = repo.get("name", "").lower()
        description = (repo.get("description") or "").lower()
        
        if "awesome" in name:
            return "curated_list"
        elif any(word in name or word in description for word in ["tutorial", "learn", "course"]):
            return "tutorial"
        elif any(word in name or word in description for word in ["example", "demo", "sample"]):
            return "example_project"
        elif "documentation" in name or "docs" in name:
            return "documentation"
        else:
            return "general_resource"


# Global instance
github_trends_agent = GitHubTrendsAgent()

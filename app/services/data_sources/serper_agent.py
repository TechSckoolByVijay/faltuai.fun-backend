"""
Serper API Integration for Real Market Research Data

Uses Serper.dev Google Search API to fetch:
- Job postings and requirements
- Technology trends and news
- Salary discussions
- Learning resource recommendations
"""

import aiohttp
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging
import os
import json

logger = logging.getLogger(__name__)


class SerperSearchAgent:
    """Agent for conducting real market research using Google Search via Serper API"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("SERPER_API_KEY")
        self.base_url = "https://google.serper.dev"
        self.session: Optional[aiohttp.ClientSession] = None
        
        if not self.api_key:
            logger.warning("Serper API key not configured. Real search disabled.")
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={
                    "X-API-KEY": self.api_key,
                    "Content-Type": "application/json"
                }
            )
        return self.session
    
    async def close(self):
        """Close aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def search(
        self, 
        query: str, 
        search_type: str = "search",  # search, news, places, images
        num_results: int = 10,
        location: str = "United States"
    ) -> Dict[str, Any]:
        """
        Perform Google search via Serper API
        
        Args:
            query: Search query
            search_type: Type of search (search, news, places, images)
            num_results: Number of results to return
            location: Geographic location for search
            
        Returns:
            Search results with snippets, links, and metadata
        """
        if not self.api_key:
            logger.error("Serper API key not configured")
            return {"organic": [], "error": "API key not configured"}
        
        endpoint = f"{self.base_url}/{search_type}"
        
        payload = {
            "q": query,
            "num": num_results,
            "gl": "us",  # Country code
            "hl": "en",  # Language
            "location": location
        }
        
        try:
            session = await self._get_session()
            async with session.post(endpoint, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Serper search successful: {query} ({len(data.get('organic', []))} results)")
                    return data
                else:
                    error_text = await response.text()
                    logger.error(f"Serper API error {response.status}: {error_text}")
                    return {"organic": [], "error": f"API error: {response.status}"}
                    
        except Exception as e:
            logger.error(f"Serper search failed for '{query}': {e}")
            return {"organic": [], "error": str(e)}
    
    async def research_job_market(
        self, 
        role: str, 
        skill_area: str,
        experience_level: str,
        location: str = "United States"
    ) -> Dict[str, Any]:
        """
        Research real job market data for specific role and skills
        
        Returns:
            - Job requirements (extracted from search results)
            - Salary mentions
            - Required skills
            - Trending job titles
        """
        logger.info(f"Researching job market for {role} - {skill_area} ({experience_level})")
        
        # Multiple targeted searches
        searches = [
            f"{role} {skill_area} jobs {experience_level} requirements 2025",
            f"{role} salary range {experience_level} 2025",
            f"{skill_area} developer skills in demand 2025",
            f"hiring {role} {skill_area} 2025 companies"
        ]
        
        all_results = []
        for query in searches:
            result = await self.search(query, num_results=10, location=location)
            if "organic" in result:
                all_results.extend(result["organic"])
            await asyncio.sleep(0.5)  # Rate limiting
        
        # Extract insights from search results
        job_requirements = self._extract_job_requirements(all_results)
        salary_data = self._extract_salary_mentions(all_results)
        required_skills = self._extract_skills(all_results, skill_area)
        
        return {
            "search_results_count": len(all_results),
            "job_requirements": job_requirements,
            "salary_insights": salary_data,
            "required_skills": required_skills,
            "raw_results": all_results[:20],  # Keep top 20 for reference
            "search_timestamp": datetime.utcnow().isoformat(),
            "search_queries": searches,
            "data_source": "Serper API (Google Search)"
        }
    
    async def research_technology_trends(
        self, 
        technology: str,
        context: str = ""
    ) -> Dict[str, Any]:
        """
        Research current technology trends and adoption
        
        Returns:
            - Recent news and articles
            - Adoption trends
            - Industry discussions
        """
        logger.info(f"Researching technology trends for {technology}")
        
        searches = [
            f"{technology} trends 2025 {context}",
            f"companies using {technology} 2025",
            f"{technology} vs alternatives 2025",
            f"{technology} best practices 2025"
        ]
        
        news_results = []
        organic_results = []
        
        for query in searches[:2]:
            result = await self.search(query, search_type="search", num_results=10)
            if "organic" in result:
                organic_results.extend(result["organic"])
            await asyncio.sleep(0.5)
        
        for query in searches[2:]:
            result = await self.search(query, search_type="news", num_results=5)
            if "news" in result:
                news_results.extend(result["news"])
            await asyncio.sleep(0.5)
        
        return {
            "technology": technology,
            "news_articles": news_results,
            "industry_discussions": organic_results,
            "articles_count": len(news_results) + len(organic_results),
            "search_timestamp": datetime.utcnow().isoformat(),
            "data_source": "Serper API (Google Search + News)"
        }
    
    async def research_learning_resources(
        self,
        topic: str,
        experience_level: str,
        platform_preference: List[str] = None
    ) -> Dict[str, Any]:
        """
        Find real learning resources from Udemy, Coursera, YouTube, etc.
        
        Returns:
            - Course listings with actual URLs
            - Ratings and reviews (from search snippets)
            - Platform information
        """
        logger.info(f"Researching learning resources for {topic} at {experience_level} level")
        
        platforms = platform_preference or ["udemy", "coursera", "youtube", "pluralsight", "freecodecamp"]
        
        searches = [
            f"best {topic} courses {experience_level} 2025 udemy coursera",
            f"learn {topic} tutorial {experience_level} youtube 2025",
            f"{topic} certification {experience_level} 2025",
            f"free {topic} courses {experience_level} 2025"
        ]
        
        all_results = []
        for query in searches:
            result = await self.search(query, num_results=10)
            if "organic" in result:
                all_results.extend(result["organic"])
            await asyncio.sleep(0.5)
        
        courses = self._extract_courses(all_results, platforms)
        
        return {
            "courses_found": courses,
            "total_sources": len(all_results),
            "search_timestamp": datetime.utcnow().isoformat(),
            "data_source": "Serper API (Google Search)",
            "platforms_searched": platforms
        }
    
    async def research_salary_data(
        self,
        role: str,
        skill_area: str,
        experience_level: str,
        location: str = "United States"
    ) -> Dict[str, Any]:
        """
        Research salary ranges from public discussions and databases
        
        Targets: levels.fyi, glassdoor, salary.com, reddit discussions
        """
        logger.info(f"Researching salary data for {role} - {skill_area}")
        
        searches = [
            f"{role} {skill_area} salary {experience_level} levels.fyi 2025",
            f"{role} compensation {location} {experience_level} 2025",
            f"{skill_area} developer salary range {experience_level} glassdoor",
            f"{role} {skill_area} pay {experience_level} reddit 2025"
        ]
        
        all_results = []
        for query in searches:
            result = await self.search(query, num_results=8, location=location)
            if "organic" in result:
                all_results.extend(result["organic"])
            await asyncio.sleep(0.5)
        
        salary_mentions = self._extract_salary_mentions(all_results)
        
        return {
            "salary_data": salary_mentions,
            "sources_count": len(all_results),
            "search_timestamp": datetime.utcnow().isoformat(),
            "location": location,
            "data_source": "Serper API (Google Search)"
        }
    
    # Helper methods to extract structured data from search results
    
    def _extract_job_requirements(self, results: List[Dict]) -> List[Dict[str, Any]]:
        """Extract job requirements from search results"""
        requirements = []
        
        for result in results:
            snippet = result.get("snippet", "")
            title = result.get("title", "")
            link = result.get("link", "")
            
            # Look for requirement keywords
            requirement_keywords = [
                "required", "must have", "experience with", "proficient in",
                "skills:", "qualifications:", "requirements:", "looking for"
            ]
            
            if any(keyword in snippet.lower() or keyword in title.lower() for keyword in requirement_keywords):
                requirements.append({
                    "title": title,
                    "snippet": snippet,
                    "url": link,
                    "source": result.get("displayLink", ""),
                    "position": result.get("position", 0)
                })
        
        return requirements[:15]  # Top 15 most relevant
    
    def _extract_salary_mentions(self, results: List[Dict]) -> List[Dict[str, Any]]:
        """Extract salary mentions from search results"""
        import re
        
        salary_data = []
        salary_pattern = r'\$[\d,]+(?:k|K)?(?:\s*-\s*\$[\d,]+(?:k|K)?)?'
        
        for result in results:
            snippet = result.get("snippet", "")
            title = result.get("title", "")
            
            # Find salary mentions
            salaries = re.findall(salary_pattern, snippet + " " + title)
            
            if salaries:
                salary_data.append({
                    "salary_mention": salaries,
                    "context": snippet[:200],
                    "source": result.get("displayLink", ""),
                    "url": result.get("link", ""),
                    "title": title
                })
        
        return salary_data
    
    def _extract_skills(self, results: List[Dict], skill_area: str) -> List[str]:
        """Extract mentioned skills from search results"""
        import re
        
        # Common tech skills patterns
        tech_keywords = [
            "python", "javascript", "react", "node", "docker", "kubernetes", "aws", "azure",
            "typescript", "java", "c++", "go", "rust", "sql", "nosql", "mongodb", "postgresql",
            "git", "ci/cd", "agile", "scrum", "api", "rest", "graphql", "microservices",
            "machine learning", "ai", "data science", "deep learning", "tensorflow", "pytorch",
            "vue", "angular", "django", "flask", "spring", "express", "fastapi"
        ]
        
        skill_counts = {}
        
        for result in results:
            text = (result.get("snippet", "") + " " + result.get("title", "")).lower()
            
            for skill in tech_keywords:
                if skill in text:
                    skill_counts[skill] = skill_counts.get(skill, 0) + 1
        
        # Sort by frequency
        sorted_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)
        
        return [skill for skill, count in sorted_skills[:20]]
    
    def _extract_courses(self, results: List[Dict], platforms: List[str]) -> List[Dict[str, Any]]:
        """Extract course information from search results"""
        courses = []
        
        for result in results:
            title = result.get("title", "")
            snippet = result.get("snippet", "")
            link = result.get("link", "")
            source = result.get("displayLink", "").lower()
            
            # Check if it's from a learning platform
            if any(platform in source or platform in link.lower() for platform in platforms):
                # Extract rating if mentioned
                rating = None
                import re
                rating_match = re.search(r'(\d+\.?\d*)\s*(?:stars?|rating|★)', snippet.lower())
                if rating_match:
                    rating = float(rating_match.group(1))
                
                courses.append({
                    "title": title,
                    "platform": source,
                    "url": link,
                    "description": snippet,
                    "rating": rating,
                    "found_via": "Google Search"
                })
        
        return courses[:20]  # Top 20 courses


# Global instance
serper_agent = SerperSearchAgent()

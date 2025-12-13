"""
Market Research Agent using LangGraph and Real Data Sources
Provides REAL market research capabilities using APIs instead of LLM hallucinations
"""
import json
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from app.services.common import llm_service
from app.services.data_sources.serper_agent import serper_agent
from app.services.data_sources.github_trends_agent import github_trends_agent
from app.services.data_sources.hackernews_agent import hackernews_agent
from app.services.data_sources.youtube_agent import youtube_agent
import logging

logger = logging.getLogger(__name__)

class MarketResearchAgent:
    """
    Agent for conducting REAL market trends research using multiple data sources
    
    Data Sources:
    - Serper API: Google Search for job postings, trends, salaries
    - GitHub API: Technology adoption and popularity metrics
    - HackerNews API: Job market insights from "Who's Hiring" threads
    - YouTube API: Learning resource availability and popularity
    - LLM: Only for synthesis and interpretation of real data
    """
    
    def __init__(self):
        self.llm_service = llm_service
        self.serper = serper_agent
        self.github = github_trends_agent
        self.hackernews = hackernews_agent
        self.youtube = youtube_agent
    
    async def research_market_trends(
        self, 
        topic: str, 
        experience_level: str,
        time_horizon: str = "2025-2026"
    ) -> Dict[str, Any]:
        """
        Conduct REAL, comprehensive market research using multiple data sources
        
        This method performs actual API calls to gather genuine market data:
        1. Serper API: Real job postings and salary data from Google Search
        2. GitHub API: Technology adoption metrics and trends
        3. HackerNews: Job requirements from "Who's Hiring" threads
        4. YouTube API: Available learning resources
        5. LLM: Synthesizes real data into actionable insights
        """
        logger.info(f"Starting REAL market research for {topic} at {experience_level} level")
        
        # Execute all research tasks in parallel for efficiency
        research_tasks = [
            self._research_real_job_demand(topic, experience_level),
            self._analyze_real_skill_gaps(topic),
            self._research_real_career_paths(topic, experience_level),
            self._find_real_learning_resources(topic, experience_level),
            self._research_tech_trends(topic)
        ]
        
        results = await asyncio.gather(*research_tasks, return_exceptions=True)
        
        # Unpack results
        demand_research = results[0] if not isinstance(results[0], Exception) else {}
        skills_analysis = results[1] if not isinstance(results[1], Exception) else {}
        career_research = results[2] if not isinstance(results[2], Exception) else {}
        learning_resources = results[3] if not isinstance(results[3], Exception) else {}
        tech_trends = results[4] if not isinstance(results[4], Exception) else {}
        
        # Synthesize findings using LLM (with REAL data as input)
        market_insights = await self._synthesize_real_research(
            demand_research, skills_analysis, career_research, 
            learning_resources, tech_trends, topic
        )
        
        return {
            "market_demand": demand_research,
            "skill_gaps": skills_analysis,
            "career_paths": career_research,
            "learning_resources": learning_resources,
            "tech_trends": tech_trends,
            "market_insights": market_insights,
            "research_timestamp": datetime.utcnow().isoformat(),
            "research_version": "real_data_v1",
            "data_sources": ["Serper API", "GitHub API", "HackerNews API", "YouTube API"]
        }
    
    async def _research_real_job_demand(self, topic: str, experience_level: str) -> Dict[str, Any]:
        """
        Research REAL job market demand using Serper API + HackerNews
        
        Sources:
        - Google Search results for job postings (Serper)
        - HackerNews "Who's Hiring" threads
        """
        logger.info(f"Researching real job demand for {topic}")
        
        try:
            # Map topic to role/title
            role_map = {
                "frontend": "Frontend Developer",
                "backend": "Backend Developer",
                "fullstack": "Full Stack Developer",
                "ai-ml": "Machine Learning Engineer",
                "data-science": "Data Scientist",
                "devops": "DevOps Engineer",
                "mobile": "Mobile Developer"
            }
            role = role_map.get(topic.lower(), f"{topic} Developer")
            
            # Parallel data collection
            serper_task = self.serper.research_job_market(role, topic, experience_level)
            hn_task = self.hackernews.analyze_job_requirements(topic, role, months_back=2)
            
            serper_data, hn_data = await asyncio.gather(serper_task, hn_task, return_exceptions=True)
            
            if isinstance(serper_data, Exception):
                logger.error(f"Serper job research failed: {serper_data}")
                serper_data = {}
            
            if isinstance(hn_data, Exception):
                logger.error(f"HackerNews research failed: {hn_data}")
                hn_data = {}
            
            # Combine insights
            return {
                "google_search_results": serper_data.get("search_results_count", 0),
                "job_postings_analyzed": serper_data.get("search_results_count", 0) + hn_data.get("job_posts_analyzed", 0),
                "required_skills": serper_data.get("required_skills", []),
                "hn_trending_skills": hn_data.get("top_skills_mentioned", []),
                "remote_work_percentage": hn_data.get("remote_work_stats", {}).get("remote_percentage", 0),
                "experience_levels_demand": hn_data.get("experience_levels", {}),
                "salary_mentions": serper_data.get("salary_insights", []),
                "data_sources": ["Serper API (Google Search)", "HackerNews API"],
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Real job demand research failed: {e}")
            return {}
    
    async def _analyze_real_skill_gaps(self, topic: str) -> Dict[str, Any]:
        """
        Analyze REAL skill gaps using GitHub trends + job postings
        
        Sources:
        - GitHub repository trends and topics
        - Job posting requirements from Serper
        """
        logger.info(f"Analyzing real skill gaps for {topic}")
        
        try:
            # Get technology adoption data from GitHub
            github_task = self.github.analyze_technology_adoption(topic)
            
            # Get skill mentions from job searches
            serper_task = self.serper.research_job_market(f"{topic} developer", topic, "intermediate")
            
            github_data, serper_data = await asyncio.gather(github_task, serper_task, return_exceptions=True)
            
            if isinstance(github_data, Exception):
                logger.error(f"GitHub trends failed: {github_data}")
                github_data = {}
            
            if isinstance(serper_data, Exception):
                logger.error(f"Serper skills research failed: {serper_data}")
                serper_data = {}
            
            # Extract trending topics from GitHub
            trending_topics = github_data.get("trending_topics", [])
            top_repos = github_data.get("top_repositories", [])
            
            # Extract required skills from job postings
            job_skills = serper_data.get("required_skills", [])
            
            return {
                "high_demand_skills": job_skills[:10],
                "emerging_technologies": [topic["topic"] for topic in trending_topics[:10]],
                "popular_repositories": [
                    {
                        "name": repo["name"],
                        "stars": repo["stars"],
                        "url": repo["url"]
                    }
                    for repo in top_repos[:5]
                ],
                "github_total_repos": github_data.get("total_repositories", 0),
                "github_total_stars": github_data.get("total_stars", 0),
                "data_sources": ["GitHub API", "Serper API"],
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Real skill gap analysis failed: {e}")
            return {}
    
    async def _research_real_career_paths(self, topic: str, experience_level: str) -> Dict[str, Any]:
        """Research REAL career paths using salary data from Serper"""
        logger.info(f"Researching real career paths for {topic}")
        
        try:
            role_map = {
                "frontend": "Frontend Developer",
                "backend": "Backend Developer",
                "fullstack": "Full Stack Developer",
                "ai-ml": "Machine Learning Engineer",
                "data-science": "Data Scientist",
                "devops": "DevOps Engineer",
                "mobile": "Mobile Developer"
            }
            role = role_map.get(topic.lower(), f"{topic} Developer")
            
            # Get real salary data
            salary_data = await self.serper.research_salary_data(role, topic, experience_level)
            
            # Use LLM to structure the data (not fabricate it)
            prompt = f"""
            Based on REAL salary data and job market information:
            
            {json.dumps(salary_data, indent=2)}
            
            Create a structured career path for {topic} professionals at {experience_level} level.
            Use ONLY the data provided above. Do not invent salary figures or statistics.
            """
            
            schema = """
            {
              "career_timeline": [
                {"level": "Junior", "years_experience": "0-2", "typical_titles": ["Junior Dev", "Developer I"]},
                {"level": "Mid", "years_experience": "2-5", "typical_titles": ["Developer", "Developer II"]}
              ],
              "advancement_skills": ["Technical Leadership", "System Design"],
              "data_sources": ["Serper API"],
              "real_salary_mentions": []  # From actual search results
            }
            """
            
            structured = await self.llm_service.generate_structured_response(
                prompt=prompt,
                schema_description=schema,
                temperature=0.2
            )
            
            # Add real data to response
            structured["real_salary_data"] = salary_data.get("salary_data", [])
            structured["data_sources"] = ["Serper API (Google Search)"]
            structured["timestamp"] = datetime.utcnow().isoformat()
            
            return structured
            
        except Exception as e:
            logger.error(f"Real career path research failed: {e}")
            return {}
    
    async def _find_real_learning_resources(self, topic: str, experience_level: str) -> Dict[str, Any]:
        """Find REAL learning resources using Serper + YouTube APIs"""
        logger.info(f"Finding real learning resources for {topic}")
        
        try:
            # Get real data from multiple sources
            serper_task = self.serper.research_learning_resources(topic, experience_level)
            youtube_task = self.youtube.find_learning_content(topic, experience_level)
            github_task = self.github.find_learning_repositories(topic, experience_level)
            
            serper_data, youtube_data, github_data = await asyncio.gather(
                serper_task, youtube_task, github_task, return_exceptions=True
            )
            
            if isinstance(serper_data, Exception):
                logger.error(f"Serper resource search failed: {serper_data}")
                serper_data = {}
            
            if isinstance(youtube_data, Exception):
                logger.error(f"YouTube search failed: {youtube_data}")
                youtube_data = {}
            
            if isinstance(github_data, Exception):
                logger.error(f"GitHub learning repos failed: {github_data}")
                github_data = []
            
            return {
                "online_courses": serper_data.get("courses_found", [])[:10],
                "youtube_videos": youtube_data.get("top_videos", [])[:10],
                "youtube_channels": youtube_data.get("recommended_channels", [])[:5],
                "github_learning_repos": github_data[:10],
                "total_resources_found": (
                    len(serper_data.get("courses_found", [])) +
                    len(youtube_data.get("top_videos", [])) +
                    len(github_data)
                ),
                "data_sources": ["Serper API", "YouTube Data API", "GitHub API"],
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Real learning resource search failed: {e}")
            return {}
    
    async def _research_tech_trends(self, topic: str) -> Dict[str, Any]:
        """Research REAL technology trends using Serper + GitHub"""
        logger.info(f"Researching tech trends for {topic}")
        
        try:
            # Get real trend data
            serper_task = self.serper.research_technology_trends(topic)
            github_task = self.github.analyze_technology_adoption(topic)
            
            serper_data, github_data = await asyncio.gather(serper_task, github_task, return_exceptions=True)
            
            if isinstance(serper_data, Exception):
                logger.error(f"Serper trends failed: {serper_data}")
                serper_data = {}
            
            if isinstance(github_data, Exception):
                logger.error(f"GitHub trends failed: {github_data}")
                github_data = {}
            
            return {
                "news_articles": serper_data.get("news_articles", [])[:10],
                "industry_discussions": serper_data.get("industry_discussions", [])[:10],
                "github_adoption_data": {
                    "total_repositories": github_data.get("total_repositories", 0),
                    "total_stars": github_data.get("total_stars", 0),
                    "top_repositories": github_data.get("top_repositories", [])[:5]
                },
                "trending_topics": github_data.get("trending_topics", [])[:10],
                "data_sources": ["Serper API (News + Search)", "GitHub API"],
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Tech trends research failed: {e}")
            return {}
    
    async def _synthesize_real_research(
        self,
        demand_research: Dict[str, Any],
        skills_analysis: Dict[str, Any],
        career_research: Dict[str, Any],
        learning_resources: Dict[str, Any],
        tech_trends: Dict[str, Any],
        topic: str
    ) -> Dict[str, Any]:
        """
        Synthesize REAL research data into actionable insights using LLM
        
        Important: LLM receives REAL data and only synthesizes/interprets it.
        It does NOT fabricate data.
        """
        # Summarize real data for LLM
        research_summary = {
            "real_data_summary": {
                "job_postings_analyzed": demand_research.get("job_postings_analyzed", 0),
                "required_skills_found": demand_research.get("required_skills", [])[:10],
                "salary_data_points": len(demand_research.get("salary_mentions", [])),
                "github_repos_analyzed": skills_analysis.get("github_total_repos", 0),
                "github_stars": skills_analysis.get("github_total_stars", 0),
                "learning_resources_found": learning_resources.get("total_resources_found", 0),
                "news_articles": len(tech_trends.get("news_articles", [])),
                "trending_github_topics": tech_trends.get("trending_topics", [])[:5]
            },
            "data_sources_used": [
                "Serper API (Google Search)",
                "GitHub API",
                "HackerNews API",
                "YouTube Data API"
            ]
        }
        
        prompt = f"""
        You are analyzing REAL market research data (not generating fake data).
        
        Topic: {topic}
        
        Real Data Collected:
        {json.dumps(research_summary, indent=2)}
        
        Based ONLY on this real data, provide:
        1. Top 3 market opportunities (based on actual job postings)
        2. Critical skills to learn (based on actual requirements found)
        3. Realistic timeline estimates
        4. Career strategies based on real salary data
        
        IMPORTANT: Use only the data provided. Do not invent statistics or facts.
        If data is limited, acknowledge it honestly.
        """
        
        schema = """
        {
          "market_opportunities": [
            {
              "opportunity": "Based on X job postings found",
              "evidence": "Specific data points",
              "confidence": "High|Medium|Low based on data quality"
            }
          ],
          "critical_skills": [
            {
              "skill": "Skill name",
              "evidence": "Found in X% of job postings",
              "priority": "High|Medium|Low"
            }
          ],
          "timeline_recommendation": {
            "weeks": 12,
            "rationale": "Based on resource availability and skill complexity"
          },
          "data_quality_note": "Assessment of how comprehensive the real data was"
        }
        """
        
        try:
            synthesis = await self.llm_service.generate_structured_response(
                prompt=prompt,
                schema_description=schema,
                temperature=0.3
            )
            
            # Add metadata about data sources
            synthesis["real_data_sources"] = research_summary["data_sources_used"]
            synthesis["research_timestamp"] = datetime.utcnow().isoformat()
            
            return synthesis
            
        except Exception as e:
            logger.error(f"Research synthesis failed: {e}")
            return {}

# Global instance
market_research_agent = MarketResearchAgent()
"""
Market Research Agent using LangGraph
Provides enhanced market research capabilities for learning plan generation
"""
import json
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from app.services.common import llm_service
import logging

logger = logging.getLogger(__name__)

class MarketResearchAgent:
    """Agent for conducting market trends research and job market analysis"""
    
    def __init__(self):
        self.llm_service = llm_service
    
    async def research_market_trends(
        self, 
        topic: str, 
        experience_level: str,
        time_horizon: str = "2025-2026"
    ) -> Dict[str, Any]:
        """
        Conduct FRESH, comprehensive market research for a specific tech topic
        This method performs real-time analysis of current market conditions
        """
        logger.info(f"Starting fresh market research for {topic} at {experience_level} level")
        
        # Step 1: Research current market demand with December 2025 focus
        demand_research = await self._research_current_job_demand(topic, experience_level)
        
        # Step 2: Analyze latest skill gaps and emerging technologies
        skills_analysis = await self._analyze_current_skill_gaps(topic)
        
        # Step 3: Research latest salary trends and career paths
        career_research = await self._research_current_career_paths(topic, experience_level)
        
        # Step 4: Find latest courses and learning resources (updated for 2025-2026)
        learning_resources = await self._find_current_learning_resources(topic, experience_level)
        
        # Step 5: Research industry news and recent developments
        industry_news = await self._research_industry_developments(topic)
        
        # Step 6: Synthesize all fresh findings
        market_insights = await self._synthesize_fresh_research(
            demand_research, skills_analysis, career_research, learning_resources, industry_news, topic
        )
        
        return {
            "market_demand": demand_research,
            "skill_gaps": skills_analysis,
            "career_paths": career_research,
            "learning_resources": learning_resources,
            "industry_developments": industry_news,
            "market_insights": market_insights,
            "research_timestamp": datetime.utcnow().isoformat(),
            "research_version": "fresh_2025_q4"
        }
    
    async def _research_current_job_demand(self, topic: str, experience_level: str) -> Dict[str, Any]:
        """Research FRESH job market demand for December 2025"""
        prompt = f"""
        Analyze the CURRENT job market demand for {topic} skills at {experience_level} level as of December 2025.
        
        Focus specifically on:
        1. Q4 2025 job market trends and demand levels
        2. Recent changes in hiring patterns (Oct-Dec 2025)
        3. Companies actively hiring in Q4 2025/Q1 2026
        4. Post-economic adjustment hiring trends
        5. Remote vs hybrid work trends in late 2025
        6. December 2025 salary data and recent adjustments
        7. 2026 projected demand based on current indicators
        
        Provide the most current, up-to-date analysis available.
        """
        
        schema = """
        {
          "demand_level": "High|Medium|Low",
          "growth_projection": "Growing|Stable|Declining",
          "growth_rate_percentage": 15.5,
          "top_hiring_sectors": ["Tech", "Finance", "Healthcare"],
          "top_companies": ["Company1", "Company2", "Company3"],
          "geographic_hotspots": [
            {"region": "San Francisco Bay Area", "demand": "Very High", "avg_salary": "$120,000"},
            {"region": "New York", "demand": "High", "avg_salary": "$110,000"}
          ],
          "remote_opportunities_percentage": 75,
          "key_insights": ["Insight 1", "Insight 2"]
        }
        """
        
        return await self.llm_service.generate_structured_response(
            prompt=prompt,
            schema_description=schema,
            temperature=0.3
        )
    
    async def _analyze_current_skill_gaps(self, topic: str) -> Dict[str, Any]:
        """Analyze FRESH skill gaps and emerging technologies for Q4 2025"""
        prompt = f"""
        Analyze the CURRENT skill gaps in the {topic} field as of December 2025.
        
        Focus on:
        1. Skills gaps identified in Q4 2025 job postings and industry reports
        2. Technologies that gained significant traction in 2025
        3. Skills that became less relevant during 2025
        4. Critical skills for 2026 career advancement
        5. New skill combinations emerging in late 2025
        6. Industry certifications gaining value in Q4 2025
        7. Technologies expected to dominate in 2026
        
        Prioritize the most recent market feedback and industry developments.
        """
        
        schema = """
        {
          "high_demand_skills": [
            {"skill": "Skill Name", "demand_level": "Critical|High|Medium", "reason": "Why it's in demand"}
          ],
          "emerging_technologies": [
            {"technology": "Tech Name", "adoption_stage": "Early|Growing|Mainstream", "impact": "description"}
          ],
          "declining_skills": ["Skill1", "Skill2"],
          "career_critical_skills": ["Skill1", "Skill2", "Skill3"],
          "valuable_combinations": [
            {"skills": ["Skill A", "Skill B"], "value_proposition": "Why this combination is valuable"}
          ]
        }
        """
        
        return await self.llm_service.generate_structured_response(
            prompt=prompt,
            schema_description=schema,
            temperature=0.3
        )
    
    async def _research_career_paths(self, topic: str, experience_level: str) -> Dict[str, Any]:
        """Research career progression paths and opportunities"""
        prompt = f"""
        Research career progression paths for {topic} professionals at {experience_level} level.
        
        Provide:
        1. Typical career progression timeline
        2. Next-level role opportunities
        3. Required skills for advancement
        4. Alternative career paths (e.g., management vs. technical leadership)
        5. Entrepreneurship opportunities
        """
        
        schema = """
        {
          "career_timeline": [
            {"level": "Junior", "years_experience": "0-2", "avg_salary": "$60,000-$80,000"},
            {"level": "Mid", "years_experience": "2-5", "avg_salary": "$80,000-$120,000"}
          ],
          "next_roles": [
            {"title": "Senior Developer", "requirements": ["5+ years", "Leadership skills"], "salary_range": "$120,000-$160,000"}
          ],
          "advancement_skills": ["Technical Leadership", "System Design", "Mentoring"],
          "career_paths": [
            {"path": "Technical Track", "description": "Focus on deep technical expertise", "roles": ["Senior Dev", "Staff Engineer", "Principal Engineer"]},
            {"path": "Management Track", "description": "Focus on people and project management", "roles": ["Team Lead", "Engineering Manager", "Director"]}
          ],
          "entrepreneurship_opportunities": ["SaaS Products", "Consulting", "Technical Content Creation"]
        }
        """
        
        return await self.llm_service.generate_structured_response(
            prompt=prompt,
            schema_description=schema,
            temperature=0.3
        )
    
    async def _find_learning_resources(self, topic: str, experience_level: str) -> Dict[str, Any]:
        """Find relevant courses, books, and learning resources"""
        prompt = f"""
        Find the best learning resources for {topic} at {experience_level} level in 2025-2026.
        
        Include:
        1. Top online courses (Coursera, Udemy, Pluralsight, etc.)
        2. YouTube channels and playlists
        3. Books and documentation
        4. Hands-on projects and tutorials
        5. Certification programs
        6. Free vs paid resources
        
        Prioritize resources that are:
        - Recently updated (2024-2025)
        - Highly rated by professionals
        - Practical and project-based
        - Industry-recognized
        """
        
        schema = """
        {
          "online_courses": [
            {
              "title": "Course Title",
              "provider": "Coursera|Udemy|Pluralsight|edX",
              "duration": "8 weeks",
              "cost": "$49|Free",
              "rating": 4.7,
              "url": "https://...",
              "difficulty": "Beginner|Intermediate|Advanced",
              "key_topics": ["Topic1", "Topic2"]
            }
          ],
          "youtube_resources": [
            {
              "channel": "Channel Name",
              "playlist_title": "Playlist Title",
              "url": "https://youtube.com/...",
              "subscriber_count": "500K",
              "content_quality": "High|Medium",
              "focus": "Tutorials|Theory|Projects"
            }
          ],
          "books": [
            {
              "title": "Book Title",
              "author": "Author Name",
              "publication_year": 2025,
              "difficulty": "Beginner|Intermediate|Advanced",
              "key_strengths": ["Practical examples", "Latest practices"]
            }
          ],
          "projects": [
            {
              "title": "Project Name",
              "description": "Build a...",
              "difficulty": "Easy|Medium|Hard",
              "estimated_hours": 20,
              "skills_practiced": ["Skill1", "Skill2"],
              "github_examples": "https://github.com/..."
            }
          ],
          "certifications": [
            {
              "name": "Certification Name",
              "provider": "AWS|Google|Microsoft|Industry Body",
              "cost": "$150",
              "validity_years": 3,
              "industry_value": "High|Medium|Low",
              "preparation_time": "2-3 months"
            }
          ]
        }
        """
        
        return await self.llm_service.generate_structured_response(
            prompt=prompt,
            schema_description=schema,
            temperature=0.2
        )
    
    # Enhanced methods for fresh research
    
    async def _research_current_career_paths(self, topic: str, experience_level: str) -> Dict[str, Any]:
        """Research current career progression paths with 2025 market updates"""
        prompt = f"""
        Research CURRENT career progression paths for {topic} professionals at {experience_level} level, 
        considering Q4 2025 market conditions.
        
        Analyze:
        1. Career paths that gained prominence in 2025
        2. New role titles and responsibilities emerging in late 2024
        3. Current salary ranges adjusted for 2024 market conditions
        4. Skills required for advancement in the current market
        5. Alternative career paths gaining traction in 2024
        6. 2025 career opportunities and projections
        7. Impact of AI/automation on career paths in 2024
        """
        
        schema = """
        {
          "career_timeline": [
            {"level": "Junior", "years_experience": "0-2", "avg_salary_2024": "$65,000-$85,000", "market_demand": "High"},
            {"level": "Mid", "years_experience": "2-5", "avg_salary_2024": "$85,000-$130,000", "market_demand": "Very High"}
          ],
          "emerging_roles_2024": [
            {"title": "AI-Enhanced Developer", "requirements": ["Traditional dev skills", "AI integration"], "salary_range": "$130,000-$180,000", "demand": "Growing rapidly"}
          ],
          "advancement_skills_2024": ["AI Integration", "Cloud Architecture", "DevSecOps", "Product Thinking"],
          "hot_career_paths": [
            {"path": "AI-First Development", "description": "Focus on AI-integrated solutions", "growth_rate": "300% in 2024"}
          ],
          "market_shifts_2024": ["Remote-first companies", "AI tooling expertise", "Cross-functional collaboration"]
        }
        """
        
        return await self.llm_service.generate_structured_response(
            prompt=prompt,
            schema_description=schema,
            temperature=0.3
        )
    
    async def _find_current_learning_resources(self, topic: str, experience_level: str) -> Dict[str, Any]:
        """Find FRESH learning resources updated for late 2024/early 2025"""
        prompt = f"""
        Find the most CURRENT and updated learning resources for {topic} at {experience_level} level 
        for Q4 2024 and Q1 2025.
        
        Prioritize:
        1. Courses launched or updated in 2024
        2. YouTube channels with recent (2024) content
        3. Books published in 2024 or with 2024 editions
        4. New certification programs launched in 2024
        5. Learning platforms with fresh 2024 content
        6. Free resources updated in the last 6 months
        7. Industry-specific bootcamps and programs starting in 2025
        
        Focus on resources that reflect current industry practices and tools used in late 2024.
        """
        
        schema = """
        {
          "fresh_courses_2024": [
            {
              "title": "Course Title (2024 Edition)",
              "provider": "Platform Name",
              "launch_date": "2024-Q4",
              "cost": "$79",
              "rating": 4.8,
              "url": "https://...",
              "what_makes_it_fresh": "Updated for latest frameworks",
              "completion_rate": "87%",
              "instructor_credibility": "Industry expert at Company"
            }
          ],
          "trending_youtube_2024": [
            {
              "channel": "Channel Name",
              "latest_series": "2024 Modern Development",
              "subscriber_growth_2024": "+200K",
              "recent_video_quality": "Excellent",
              "focus_areas": ["Latest tools", "Current practices"]
            }
          ],
          "new_books_2024": [
            {
              "title": "Book Title (2024)",
              "author": "Author Name",
              "publication_date": "2024-11",
              "why_essential": "Covers latest industry standards",
              "reader_reviews_2024": "Highly practical"
            }
          ],
          "emerging_certifications_2024": [
            {
              "name": "New Certification 2024",
              "provider": "Industry Leader",
              "launched": "2024-Q3",
              "industry_adoption": "Rapid",
              "job_relevance": "Very High",
              "cost": "$299"
            }
          ]
        }
        """
        
        return await self.llm_service.generate_structured_response(
            prompt=prompt,
            schema_description=schema,
            temperature=0.2
        )
    
    async def _research_industry_developments(self, topic: str) -> Dict[str, Any]:
        """Research recent industry developments and news affecting the field"""
        prompt = f"""
        Research the most significant industry developments in {topic} field during Q4 2024.
        
        Focus on:
        1. Major technology releases or updates in Q4 2024
        2. Industry acquisitions and their impact on job market
        3. New regulations or compliance requirements introduced in 2024
        4. Significant funding rounds or startup developments
        5. Conference announcements and industry predictions for 2025
        6. Open source projects that gained traction in 2024
        7. Industry leader statements about future directions
        
        Analyze how these developments impact learning priorities and career paths.
        """
        
        schema = """
        {
          "major_releases_q4_2024": [
            {
              "technology": "Technology Name",
              "company": "Company",
              "release_date": "2024-12",
              "impact_on_jobs": "High - creates new skill demands",
              "learning_priority": "Should be included in 2025 learning plans"
            }
          ],
          "industry_shifts": [
            {
              "shift": "AI Integration Acceleration",
              "timeline": "Q4 2024 - Q2 2025",
              "skill_implications": ["AI prompt engineering", "Model integration"],
              "career_impact": "Critical for advancement"
            }
          ],
          "funding_and_growth": [
            {
              "area": "AI Development Tools",
              "investment_q4_2024": "$2.3B",
              "job_creation_projection": "25,000 new roles in 2025"
            }
          ],
          "regulatory_changes": [
            {
              "regulation": "AI Safety Standards",
              "effective_date": "2024-Q4",
              "compliance_skills_needed": ["AI auditing", "Bias detection"]
            }
          ]
        }
        """
        
        return await self.llm_service.generate_structured_response(
            prompt=prompt,
            schema_description=schema,
            temperature=0.3
        )
    
    async def _synthesize_fresh_research(
        self, 
        demand_research: Dict[str, Any],
        skills_analysis: Dict[str, Any],
        career_research: Dict[str, Any],
        learning_resources: Dict[str, Any],
        industry_news: Dict[str, Any],
        topic: str
    ) -> Dict[str, Any]:
        """Synthesize all FRESH research into actionable market insights for December 2024"""
        
        research_summary = {
            "job_demand_q4_2024": demand_research.get("demand_level", "Medium"),
            "growth_rate": demand_research.get("growth_rate_percentage", 0),
            "high_demand_skills": [skill["skill"] for skill in skills_analysis.get("high_demand_skills", [])[:5]],
            "emerging_tech_2024": [tech["technology"] for tech in skills_analysis.get("emerging_technologies", [])[:3]],
            "hot_career_paths": career_research.get("hot_career_paths", []),
            "fresh_resources": len(learning_resources.get("fresh_courses_2024", [])),
            "major_industry_developments": len(industry_news.get("major_releases_q4_2024", [])),
            "market_shifts": industry_news.get("industry_shifts", [])
        }
        
        prompt = f"""
        Based on FRESH, comprehensive market research for {topic} as of December 2024, 
        synthesize key insights and create actionable recommendations for immediate implementation.
        
        Fresh Research Summary:
        {json.dumps(research_summary, indent=2)}
        
        Provide Q4 2024/Q1 2025 focused insights:
        1. Top 3 immediate market opportunities (December 2024 - March 2025)
        2. Critical skills to learn RIGHT NOW for Q1 2025 job market
        3. Accelerated learning timeline for current market conditions
        4. Career advancement strategies leveraging 2024 developments
        5. Market risks and opportunities specific to early 2025
        6. Skills that will be obsolete by mid-2025
        7. Technologies to prioritize for 2025 career growth
        
        Focus on actionable, time-sensitive recommendations based on current market intelligence.
        """
        
        schema = """
        {
          "immediate_opportunities_q1_2025": [
            {
              "opportunity": "Specific Q1 2025 opportunity",
              "market_timing": "December 2024 - March 2025", 
              "potential": "High|Medium|Low",
              "immediate_actions": ["Start learning X this week", "Apply to Y roles in January"],
              "expected_roi": "Salary increase potential"
            }
          ],
          "critical_skills_now": [
            {
              "skill": "Skill name",
              "urgency": "Learn by January 2025|Learn by March 2025",
              "market_demand": "Companies actively hiring for this",
              "learning_timeline": "2-4 weeks intensive",
              "specific_resources": ["Exact course name", "Specific YouTube series"]
            }
          ],
          "accelerated_roadmap_2025": {
            "immediate_sprint": {"duration": "December 2024 - January 2025", "focus": "Hot market skills", "deliverables": ["Portfolio project", "Certification"]},
            "consolidation": {"duration": "February - April 2025", "focus": "Applied experience", "deliverables": ["Real project", "Network building"]},
            "specialization": {"duration": "May - August 2025", "focus": "Advanced/Niche skills", "deliverables": ["Expert status", "Leadership role"]}
          },
          "career_strategies_2025": [
            {
              "strategy": "Leverage 2024 tech developments",
              "execution": "How to implement immediately",
              "timeline": "Start in December 2024",
              "success_indicators": ["Metric 1", "Interview callbacks"]
            }
          ],
          "market_risks_early_2025": [
            {
              "risk": "Skill becoming obsolete by mid-2025",
              "probability": "High|Medium|Low",
              "mitigation": "Transition strategy",
              "timeline": "Act before Q2 2025"
            }
          ],
          "technologies_prioritize_2025": [
            {
              "technology": "Technology name",
              "adoption_timeline": "Mainstream by Q2 2025",
              "learning_urgency": "Start immediately",
              "career_impact": "Job requirement vs competitive advantage"
            }
          ]
        }
        """
        
        return await self.llm_service.generate_structured_response(
            prompt=prompt,
            schema_description=schema,
            temperature=0.4
        )

# Global instance
market_research_agent = MarketResearchAgent()
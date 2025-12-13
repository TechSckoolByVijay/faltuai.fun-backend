import json
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
from app.services.common import llm_service
from app.services.market_research_agent import market_research_agent
from app.services.learning_plan_agent import learning_plan_agent
from app.schemas.skill_assessment import (
    ExperienceLevel, 
    DifficultyLevel, 
    QuizQuestionResponse,
    QuizOption,
    EvaluationSummary,
    LearningPlanResponse,
    SkillAreaScore,
    LearningModule,
    LearningResource,
    ProjectIdea,
    MarketTrend
)
import logging

logger = logging.getLogger(__name__)

class SkillAssessmentAIService:
    """Service for AI-powered skill assessment operations using common LLM service"""
    
    def __init__(self):
        # Use common LLM service
        self.llm_service = llm_service
    
    async def generate_quiz_questions(
        self, 
        topic: str, 
        experience_level: ExperienceLevel, 
        num_questions: Optional[int] = None
    ) -> List[QuizQuestionResponse]:
        """Generate dynamic quiz questions based on topic and experience level"""
        
        # Make question count adaptive based on experience level and topic complexity
        if num_questions is None:
            num_questions = self._calculate_optimal_question_count(topic, experience_level)
        
        prompt = self._build_quiz_generation_prompt(topic, experience_level, num_questions)
        
        schema_description = """
        {
          "questions": [
            {
              "question": "Question text here",
              "options": ["Option A", "Option B", "Option C", "Option D"],
              "difficulty": "easy|medium|hard",
              "category": "subcategory of the topic"
            }
          ]
        }
        """
        
        try:
            response_data = await self.llm_service.generate_structured_response(
                prompt=prompt,
                schema_description=schema_description,
                temperature=0.7
            )
            
            # Convert to response schema
            questions = []
            questions_list = response_data.get("questions", [])
            
            for i, q_data in enumerate(questions_list):
                options = [
                    QuizOption(id=f"opt_{j}", text=opt) 
                    for j, opt in enumerate(q_data.get("options", []))
                ]
                
                question = QuizQuestionResponse(
                    id=i + 1,  # Temporary ID, will be replaced with DB ID
                    question_text=q_data.get("question", ""),
                    options=options,
                    difficulty_level=self._map_to_difficulty_level(q_data.get("difficulty", "medium")),
                    question_order=i + 1
                )
                questions.append(question)
            
            return questions
            
        except Exception as e:
            logger.error(f"Error generating quiz questions: {e}")
            # Return fallback questions if AI fails
            return self._get_fallback_questions(topic, num_questions)
    
    async def evaluate_quiz_answers(
        self, 
        topic: str,
        questions: List[Dict[str, Any]],
        answers: List[Dict[str, Any]],
        experience_level: ExperienceLevel
    ) -> EvaluationSummary:
        """Evaluate user answers and generate skill assessment"""
        
        prompt = self._build_evaluation_prompt(topic, questions, answers, experience_level)
        
        try:
            schema_description = """
            {
              "overall_score": 85.5,
              "expertise_level": "intermediate",
              "strengths": ["Area 1", "Area 2"],
              "weaknesses": ["Area 3", "Area 4"],
              "skill_breakdown": [
                {"area": "Fundamentals", "score": 80.0, "feedback": "Good understanding"}
              ]
            }
            """
            
            evaluation_data = await self.llm_service.generate_structured_response(
                prompt=prompt,
                schema_description=schema_description,
                temperature=0.3
            )
            
            # Build evaluation summary
            summary = EvaluationSummary(
                assessment_id=0,  # Will be set by caller
                overall_score=evaluation_data.get("overall_score", 60.0),
                expertise_level=evaluation_data.get("expertise_level", "intermediate"),
                strengths=evaluation_data.get("strengths", []),
                weaknesses=evaluation_data.get("weaknesses", []),
                skill_breakdown=self._build_skill_breakdown(evaluation_data.get("skill_areas", {}))
            )
            
            return summary
            
        except Exception as e:
            logger.error(f"Error evaluating quiz answers: {e}")
            return self._get_fallback_evaluation()
    
    async def generate_learning_plan(
        self,
        topic: str,
        evaluation: EvaluationSummary,
        user_experience_level: ExperienceLevel
    ) -> LearningPlanResponse:
        """
        Generate comprehensive personalized learning plan using LangGraph agent.
        
        This uses a multi-stage research and planning workflow to create
        detailed, actionable learning plans with real market insights.
        """
        
        try:
            logger.info(f"Starting comprehensive learning plan generation for {topic}")
            
            # Extract data from evaluation
            experience_level_str = user_experience_level.value if hasattr(user_experience_level, 'value') else user_experience_level
            
            strengths = evaluation.strengths if hasattr(evaluation, 'strengths') else []
            weaknesses = evaluation.weaknesses if hasattr(evaluation, 'weaknesses') else []
            overall_score = evaluation.overall_score if hasattr(evaluation, 'overall_score') else 70
            
            # Use the comprehensive LangGraph agent
            plan_data = await learning_plan_agent.generate_comprehensive_plan(
                topic=topic,
                experience_level=experience_level_str,
                strengths=strengths,
                weaknesses=weaknesses,
                overall_score=overall_score
            )
            
            # Convert plan data to response schema
            learning_modules = []
            for mod in plan_data.get('learning_modules', []):
                resources = []
                for res in mod.get('resources', []):
                    resource = LearningResource(
                        title=res.get('title', ''),
                        type=res.get('type', 'course'),
                        url=res.get('url', '#'),
                        difficulty=self._map_to_difficulty_level(res.get('difficulty', 'intermediate')),
                        estimated_hours=res.get('estimated_hours', 10)
                    )
                    resources.append(resource)
                
                module = LearningModule(
                    title=mod.get('title', ''),
                    description=mod.get('description', ''),
                    duration_weeks=mod.get('duration_weeks', 2),
                    resources=resources,
                    learning_objectives=mod.get('learning_objectives', []),
                    weekly_breakdown=mod.get('weekly_breakdown', [])
                )
                learning_modules.append(module)
            
            # Convert project ideas
            project_ideas = []
            for proj in plan_data.get('project_ideas', []):
                project = ProjectIdea(
                    title=proj.get('title', ''),
                    description=proj.get('description', ''),
                    difficulty=self._map_to_difficulty_level(proj.get('difficulty', 'intermediate')),
                    duration_weeks=proj.get('duration_weeks', 2),
                    technologies=proj.get('technologies', []),
                    learning_objectives=proj.get('learning_objectives', [])
                )
                project_ideas.append(project)
            
            # Convert market trends
            market_trends = []
            for trend in plan_data.get('market_trends', []):
                market_trend = MarketTrend(
                    trend_name=trend.get('trend_name', ''),
                    relevance_score=trend.get('relevance_score', 80),
                    time_to_learn_weeks=trend.get('time_to_learn_weeks', 4),
                    job_market_impact=trend.get('job_market_impact', ''),
                    resources=trend.get('resources', [])
                )
                market_trends.append(market_trend)
            
            # Build final learning plan
            learning_plan = LearningPlanResponse(
                assessment_id=evaluation.assessment_id,
                plan_id=0,  # Will be set by caller
                timeline_weeks=plan_data.get('timeline_weeks', 12),
                learning_modules=learning_modules,
                priority_skills=plan_data.get('priority_skills', []),
                project_ideas=project_ideas,
                market_trends=market_trends,
                learning_resources=plan_data.get('learning_resources', []),
                career_progression=plan_data.get('career_progression'),
                market_research_insights=plan_data.get('market_research_insights'),
                created_at=datetime.utcnow()
            )
            
            logger.info(f"Successfully generated comprehensive learning plan with {len(learning_modules)} modules, {len(project_ideas)} projects, {len(market_trends)} trends")
            
            return learning_plan
            
        except Exception as e:
            logger.error(f"Error generating enhanced learning plan: {e}")
            return self._get_fallback_learning_plan(topic)
    
    # Private helper methods
    
    def _calculate_optimal_question_count(self, topic: str, experience_level: ExperienceLevel) -> int:
        """Calculate optimal number of questions based on topic complexity and experience level"""
        base_questions = {
            ExperienceLevel.BEGINNER: 8,
            ExperienceLevel.INTERMEDIATE: 12,
            ExperienceLevel.ADVANCED: 15
        }
        
        # Topic complexity multipliers
        complex_topics = ['ai-ml', 'devops', 'cybersecurity', 'data-engineering', 'backend']
        simple_topics = ['frontend', 'mobile']
        
        questions_count = base_questions[experience_level]
        
        if topic.lower() in complex_topics:
            questions_count += 2
        elif topic.lower() in simple_topics:
            questions_count -= 1
            
        return max(6, min(20, questions_count))  # Ensure between 6-20 questions
    
    def _build_quiz_generation_prompt(self, topic: str, experience_level: ExperienceLevel, num_questions: int) -> str:
        """Build prompt for quiz question generation"""
        experience_level_str = experience_level.value if hasattr(experience_level, 'value') else experience_level
        return f"""
Generate {num_questions} quiz questions for assessing {topic} skills.
Experience Level: {experience_level_str}

Requirements:
- Mix of fundamentals, practical scenarios, and current trends
- Questions should be specific to {topic} domain
- Include both conceptual and practical questions
- For {experience_level_str} level: 
  - Beginner: Focus on basics, definitions, simple concepts
  - Intermediate: Include problem-solving, tools, best practices  
  - Advanced: Complex scenarios, architecture, optimization, leadership

- Provide 4 multiple choice options per question
- Include difficulty level for each question (easy/medium/hard)
- Questions should test real-world application, not just theory

Return response as JSON array:
[
  {{
    "question": "Question text here?",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_answer": "Option B",
    "difficulty": "medium",
    "explanation": "Brief explanation of correct answer"
  }}
]

Focus on current industry trends and in-demand skills for {topic}.
Make questions engaging and practical, not just theoretical.
"""
    
    def _build_evaluation_prompt(self, topic: str, questions: List[Dict], answers: List[Dict], experience_level: ExperienceLevel) -> str:
        """Build prompt for answer evaluation"""
        
        qa_pairs = []
        for i, (q, a) in enumerate(zip(questions, answers)):
            qa_pairs.append(f"Q{i+1}: {q.get('question_text', '')}")
            qa_pairs.append(f"User Answer: {a.get('user_answer', '')}")
            qa_pairs.append("---")
        
        qa_text = "\n".join(qa_pairs)
        
        experience_level_str = experience_level.value if hasattr(experience_level, 'value') else experience_level
        return f"""
Evaluate this {topic} skill assessment for a {experience_level_str} level developer.

QUESTIONS AND ANSWERS:
{qa_text}

Provide evaluation analysis as JSON:
{{
  "overall_score": 75.5,
  "expertise_level": "intermediate",
  "strengths": ["Area 1", "Area 2", "Area 3"],
  "weaknesses": ["Area 1", "Area 2"],
  "skill_areas": {{
    "Fundamentals": {{"score": 80, "level": "good"}},
    "Tools & Frameworks": {{"score": 70, "level": "intermediate"}},
    "Best Practices": {{"score": 65, "level": "developing"}},
    "Problem Solving": {{"score": 85, "level": "strong"}}
  }},
  "detailed_feedback": "Overall analysis of performance...",
  "next_steps": ["Specific recommendation 1", "Specific recommendation 2"]
}}

Consider:
- Depth of understanding shown in answers
- Practical vs theoretical knowledge
- Current market relevance of skills demonstrated
- Areas for immediate improvement
- Readiness for next skill level

Be constructive but honest in assessment.
"""
    
    def _build_learning_plan_prompt(self, topic: str, evaluation: EvaluationSummary, experience_level: ExperienceLevel) -> str:
        """Build prompt for learning plan generation"""
        
        strengths_text = ", ".join(evaluation.strengths)
        weaknesses_text = ", ".join(evaluation.weaknesses)
        
        experience_level_str = experience_level.value if hasattr(experience_level, 'value') else experience_level
        return f"""
Create a personalized {topic} learning plan for 3-6 months.

CURRENT PROFILE:
- Experience Level: {experience_level_str}
- Overall Score: {evaluation.overall_score}%
- Expertise Level: {evaluation.expertise_level}
- Strengths: {strengths_text}
- Weaknesses: {weaknesses_text}

Generate comprehensive learning roadmap as JSON:
{{
  "timeline_weeks": 16,
  "priority_skills": ["Skill 1", "Skill 2", "Skill 3"],
  "modules": [
    {{
      "title": "Module Name",
      "description": "What you'll learn",
      "priority": "High",
      "estimated_weeks": 3,
      "resources": [
        {{
          "title": "Resource Name",
          "type": "course",
          "url": "https://example.com",
          "cost": "Free",
          "difficulty": "medium",
          "estimated_hours": 20
        }}
      ]
    }}
  ],
  "projects": [
    {{
      "title": "Project Name", 
      "description": "Build something practical",
      "difficulty": "medium",
      "skills_practiced": ["Skill 1", "Skill 2"],
      "estimated_hours": 40
    }}
  ],
  "market_insights": [
    {{
      "trend": "Current market trend",
      "relevance": "How it applies to user",
      "growth_rate": "Market growth info",
      "salary_impact": "Potential salary impact"
    }}
  ]
}}

FOCUS ON:
- Addressing identified weaknesses first
- Building on existing strengths  
- Current market demand and trends
- Practical, hands-on learning
- Mix of free and premium resources
- Progressive skill building
- Real-world project applications
- Job market relevance

Include specific tools, frameworks, and technologies that are in high demand.
Prioritize skills that will have immediate career impact.
"""
    
    # Removed _call_langchain_async - now using common LLM service
    
    def _parse_quiz_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse AI response for quiz questions"""
        try:
            # Try to extract JSON from response
            start_idx = response.find('[')
            end_idx = response.rfind(']') + 1
            if start_idx != -1 and end_idx != 0:
                json_str = response[start_idx:end_idx]
                return json.loads(json_str)
        except Exception as e:
            logger.error(f"Error parsing quiz response: {e}")
        
        return []
    
    def _parse_evaluation_response(self, response: str) -> Dict[str, Any]:
        """Parse AI response for evaluation"""
        try:
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            if start_idx != -1 and end_idx != 0:
                json_str = response[start_idx:end_idx]
                return json.loads(json_str)
        except Exception as e:
            logger.error(f"Error parsing evaluation response: {e}")
        
        return {}
    
    def _parse_learning_plan_response(self, response: str) -> Dict[str, Any]:
        """Parse AI response for learning plan"""
        try:
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            if start_idx != -1 and end_idx != 0:
                json_str = response[start_idx:end_idx]
                return json.loads(json_str)
        except Exception as e:
            logger.error(f"Error parsing learning plan response: {e}")
        
        return {}
    
    def _build_skill_breakdown(self, skill_areas: Dict[str, Dict]) -> List[SkillAreaScore]:
        """Build skill area breakdown from AI response"""
        breakdown = []
        for area, data in skill_areas.items():
            breakdown.append(SkillAreaScore(
                area=area,
                score=float(data.get("score", 60.0)),
                level=data.get("level", "developing")
            ))
        return breakdown
    
    def _build_learning_modules(self, modules_data: List[Dict]) -> List[LearningModule]:
        """Build learning modules from AI response"""
        modules = []
        for mod_data in modules_data:
            resources = []
            for res_data in mod_data.get("resources", []):
                resource = LearningResource(
                    title=res_data.get("title", ""),
                    type=res_data.get("type", "course"),
                    url=res_data.get("url"),
                    cost=res_data.get("cost", "Unknown"),
                    difficulty=self._map_to_difficulty_level(res_data.get("difficulty", "medium")),
                    estimated_hours=res_data.get("estimated_hours")
                )
            
            modules.append(LearningModule(
                title=mod_data.get("title", ""),
                description=mod_data.get("description", ""),
                priority=mod_data.get("priority", "Medium"),
                estimated_weeks=mod_data.get("estimated_weeks", 2),
                resources=resources
            ))
        
        return modules
    
    def _build_project_ideas(self, projects_data: List[Dict]) -> List[ProjectIdea]:
        """Build project ideas from AI response"""
        projects = []
        for proj_data in projects_data:
            projects.append(ProjectIdea(
                title=proj_data.get("title", ""),
                description=proj_data.get("description", ""),
                difficulty=self._map_to_difficulty_level(proj_data.get("difficulty", "medium")),
                skills_practiced=proj_data.get("skills_practiced", []),
                estimated_hours=proj_data.get("estimated_hours", 20)
            ))
        return projects
    
    def _build_market_trends(self, trends_data: List[Dict]) -> List[MarketTrend]:
        """Build market trends from AI response"""
        trends = []
        for trend_data in trends_data:
            trends.append(MarketTrend(
                trend=trend_data.get("trend", ""),
                relevance=trend_data.get("relevance", ""),
                growth_rate=trend_data.get("growth_rate"),
                salary_impact=trend_data.get("salary_impact")
            ))
        return trends
    
    # Fallback methods for when AI fails
    
    def _get_fallback_questions(self, topic: str, num_questions: int) -> List[QuizQuestionResponse]:
        """Return fallback questions when AI generation fails"""
        # TODO: Implement fallback question database
        return []
    
    def _get_fallback_evaluation(self) -> EvaluationSummary:
        """Return fallback evaluation when AI fails"""
        return EvaluationSummary(
            assessment_id=0,
            overall_score=60.0,
            expertise_level="intermediate",
            strengths=["Basic concepts"],
            weaknesses=["Advanced topics"],
            skill_breakdown=[]
        )
    
    def _get_fallback_learning_plan(self, topic: str) -> LearningPlanResponse:
        """Return fallback learning plan when AI fails"""
        return LearningPlanResponse(
            assessment_id=0,
            plan_id=0,
            timeline_weeks=12,
            learning_modules=[],
            priority_skills=[f"{topic} fundamentals"],
            project_ideas=[],
            market_trends=[],
            created_at=datetime.utcnow()
        )
    
    # Enhanced helper methods for market research integration
    
    def _map_to_difficulty_level(self, difficulty_str: str) -> DifficultyLevel:
        """Map various difficulty strings to valid DifficultyLevel enum values"""
        difficulty_mapping = {
            "beginner": DifficultyLevel.EASY,
            "easy": DifficultyLevel.EASY,
            "intermediate": DifficultyLevel.MEDIUM,
            "medium": DifficultyLevel.MEDIUM,
            "advanced": DifficultyLevel.HARD,
            "hard": DifficultyLevel.HARD,
            "expert": DifficultyLevel.HARD
        }
        return difficulty_mapping.get(difficulty_str.lower(), DifficultyLevel.MEDIUM)
    
    def _build_enhanced_learning_plan_prompt(
        self, 
        topic: str, 
        evaluation: EvaluationSummary, 
        experience_level: ExperienceLevel,
        market_research: Dict[str, Any]
    ) -> str:
        """Build enhanced learning plan prompt with market research insights"""
        
        strengths_text = ", ".join(evaluation.strengths)
        weaknesses_text = ", ".join(evaluation.weaknesses)
        
        # Extract key market insights
        demand_level = market_research.get("market_demand", {}).get("demand_level", "Medium")
        high_demand_skills = market_research.get("skill_gaps", {}).get("high_demand_skills", [])
        top_resources = market_research.get("learning_resources", {}).get("online_courses", [])
        
        high_demand_skills_text = ", ".join([skill.get("skill", "") for skill in high_demand_skills[:5]])
        
        experience_level_str = experience_level.value if hasattr(experience_level, 'value') else experience_level
        return f"""
🚀 Create a COMPREHENSIVE, research-driven {topic} learning plan for DECEMBER 2025 career advancement.

📊 CURRENT PROFILE:
- Experience Level: {experience_level_str}
- Overall Score: {evaluation.overall_score}%
- Expertise Level: {evaluation.expertise_level}
- Strengths: {strengths_text}
- Weaknesses: {weaknesses_text}

🔥 FRESH MARKET INSIGHTS (Q4 2025):
- Job Market Demand: {demand_level}
- High-Demand Skills: {high_demand_skills_text}
- Market Growth Rate: {market_research.get("market_demand", {}).get("growth_rate_percentage", 0)}%

⚡ DECEMBER 2025 REQUIREMENTS:
1. Create a DETAILED 12-WEEK BREAKDOWN with specific weekly objectives
2. Address weaknesses systematically with LATEST 2025 resources
3. Build on strengths for Q1 2026 career opportunities  
4. Include TRENDING market-demanded skills (December 2025)
5. Provide comprehensive learning resources with detailed descriptions
6. Focus on Q1 2026 job-ready skills and portfolio projects
7. Include 2025 salary data and career progression insights
8. Create weekly milestones and deliverables
9. Target systematic skill acquisition for Q1 2026 opportunities
10. Include hands-on projects aligned with market demands

📋 DETAILED REQUIREMENTS:
- Weekly Breakdown: Each week should have 3-5 specific objectives
- Learning Resources: Include courses, videos, books, and practice platforms
- Projects: Real-world portfolio projects that demonstrate skills
- Career Progression: Clear path from current level to target roles
- Market Research: Include salary expectations and skill demand analysis
- Time Investment: 10-15 hours per week with clear hour allocation

🎯 URGENT FOCUS: Generate a comprehensive, week-by-week learning roadmap for SYSTEMATIC skill development.
Focus on cutting-edge skills, latest frameworks/tools, and Q1 2026 market demands.
Timeline: Structured 12-week intensive program for Q1 2026 job market readiness.
"""
    
    def _build_enhanced_learning_modules(
        self, 
        modules_data: List[Dict], 
        learning_resources: Dict[str, Any]
    ) -> List[LearningModule]:
        """Build enhanced learning modules with real resources"""
        modules = []
        online_courses = learning_resources.get("online_courses", [])
        youtube_resources = learning_resources.get("youtube_resources", [])
        
        for mod_data in modules_data:
            resources = []
            
            # Combine planned resources with researched ones
            for res_data in mod_data.get("resources", []):
                # Try to match with real researched resources
                matching_course = None
                matching_youtube = None
                
                for course in online_courses:
                    if any(topic.lower() in course.get("title", "").lower() 
                          for topic in mod_data.get("learning_objectives", [])):
                        matching_course = course
                        break
                
                for youtube in youtube_resources:
                    if any(topic.lower() in youtube.get("playlist_title", "").lower() 
                          for topic in mod_data.get("learning_objectives", [])):
                        matching_youtube = youtube
                        break
                
                # Use real resource data if available
                resource = LearningResource(
                    title=matching_course.get("title") if matching_course else res_data.get("title", ""),
                    type=res_data.get("type", "course"),
                    url=matching_course.get("url") if matching_course else res_data.get("url", ""),
                    difficulty=self._map_to_difficulty_level(res_data.get("difficulty", "medium")),
                    estimated_hours=res_data.get("duration", 10)
                )
                resources.append(resource)
            
            module = LearningModule(
                title=mod_data.get("title", ""),
                description=mod_data.get("description", ""),
                duration_weeks=mod_data.get("duration_weeks", 2),
                resources=resources,
                learning_objectives=mod_data.get("learning_objectives", [])
            )
            modules.append(module)
        
        return modules
    
    def _build_priority_skills_with_market_context(
        self, 
        priority_skills_data: List[Dict],
        skill_gaps: Dict[str, Any]
    ) -> List[str]:
        """Build priority skills list enhanced with market context"""
        skills = []
        market_skills = [skill.get("skill", "") for skill in skill_gaps.get("high_demand_skills", [])]
        
        for skill_data in priority_skills_data:
            if isinstance(skill_data, dict):
                skill_name = skill_data.get("skill", "")
                importance = skill_data.get("importance", "")
                # Add market context to skill description
                if skill_name in market_skills:
                    skills.append(f"{skill_name} (HIGH MARKET DEMAND)")
                else:
                    skills.append(skill_name)
            else:
                skills.append(str(skill_data))
        
        # Add top market skills that weren't already included
        for market_skill in market_skills[:3]:
            if not any(market_skill.lower() in skill.lower() for skill in skills):
                skills.append(f"{market_skill} (EMERGING MARKET OPPORTUNITY)")
        
        return skills
    
    def _build_enhanced_project_ideas(self, projects_data: List[Dict]) -> List[ProjectIdea]:
        """Build enhanced project ideas with market relevance"""
        projects = []
        for proj_data in projects_data:
            # Enhanced project with industry relevance
            description = proj_data.get("description", "")
            industry_relevance = proj_data.get("industry_relevance", "")
            if industry_relevance:
                description += f" (Industry Impact: {industry_relevance})"
            
            projects.append(ProjectIdea(
                title=proj_data.get("title", ""),
                description=description,
                difficulty=self._map_to_difficulty_level(proj_data.get("difficulty", "medium")),
                skills_practiced=proj_data.get("skills_practiced", []),
                estimated_hours=proj_data.get("estimated_hours", 20)
            ))
        return projects
    
    def _build_enhanced_market_trends(
        self, 
        trends_data: List[Dict],
        market_insights: Dict[str, Any]
    ) -> List[MarketTrend]:
        """Build enhanced market trends with research insights"""
        trends = []
        
        # Add AI-generated trends
        for trend_data in trends_data:
            trends.append(MarketTrend(
                trend=trend_data.get("trend", ""),
                relevance=trend_data.get("impact", ""),
                growth_rate=None,
                salary_impact=trend_data.get("salary_impact", "")
            ))
        
        # Add researched market opportunities
        market_opportunities = market_insights.get("market_opportunities", [])
        for opportunity in market_opportunities[:3]:
            trends.append(MarketTrend(
                trend=opportunity.get("opportunity", ""),
                relevance=opportunity.get("potential", ""),
                growth_rate=None,
                salary_impact=opportunity.get("timeframe", "")
            ))
        
        return trends
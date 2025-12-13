import json
import asyncio
from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from langchain.callbacks import get_openai_callback
from app.config import settings
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
    """Service for AI-powered skill assessment operations using LangChain"""
    
    def __init__(self):
        # Initialize LangChain ChatOpenAI
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.7,
            openai_api_key=settings.OPENAI_API_KEY,
            max_tokens=3000
        )
    
    async def generate_quiz_questions(
        self, 
        topic: str, 
        experience_level: ExperienceLevel, 
        num_questions: int = 12
    ) -> List[QuizQuestionResponse]:
        """Generate dynamic quiz questions based on topic and experience level"""
        
        prompt = self._build_quiz_generation_prompt(topic, experience_level, num_questions)
        
        try:
            response = await self._call_langchain_async(
                prompt=prompt,
                temperature=0.7,
                max_tokens=3000
            )
            
            # Parse AI response into structured questions
            questions_data = self._parse_quiz_response(response)
            
            # Convert to response schema
            questions = []
            for i, q_data in enumerate(questions_data):
                options = [
                    QuizOption(id=f"opt_{j}", text=opt) 
                    for j, opt in enumerate(q_data.get("options", []))
                ]
                
                question = QuizQuestionResponse(
                    id=i + 1,  # Temporary ID, will be replaced with DB ID
                    question_text=q_data.get("question", ""),
                    options=options,
                    difficulty_level=DifficultyLevel(q_data.get("difficulty", "medium")),
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
            response = await self._call_langchain_async(
                prompt=prompt,
                temperature=0.3,
                max_tokens=2000
            )
            
            evaluation_data = self._parse_evaluation_response(response)
            
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
        """Generate personalized learning plan based on assessment results"""
        
        prompt = self._build_learning_plan_prompt(topic, evaluation, user_experience_level)
        
        try:
            response = await self._call_langchain_async(
                prompt=prompt,
                temperature=0.6,
                max_tokens=3500
            )
            
            plan_data = self._parse_learning_plan_response(response)
            
            learning_plan = LearningPlanResponse(
                assessment_id=evaluation.assessment_id,
                plan_id=0,  # Will be set by caller
                timeline_weeks=plan_data.get("timeline_weeks", 12),
                learning_modules=self._build_learning_modules(plan_data.get("modules", [])),
                priority_skills=plan_data.get("priority_skills", []),
                project_ideas=self._build_project_ideas(plan_data.get("projects", [])),
                market_trends=self._build_market_trends(plan_data.get("market_insights", [])),
                created_at=None  # Will be set by caller
            )
            
            return learning_plan
            
        except Exception as e:
            logger.error(f"Error generating learning plan: {e}")
            return self._get_fallback_learning_plan(topic)
    
    # Private helper methods
    
    def _build_quiz_generation_prompt(self, topic: str, experience_level: ExperienceLevel, num_questions: int) -> str:
        """Build prompt for quiz question generation"""
        return f"""
Generate {num_questions} quiz questions for assessing {topic} skills.
Experience Level: {experience_level.value}

Requirements:
- Mix of fundamentals, practical scenarios, and current trends
- Questions should be specific to {topic} domain
- Include both conceptual and practical questions
- For {experience_level.value} level: 
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
        
        return f"""
Evaluate this {topic} skill assessment for a {experience_level.value} level developer.

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
        
        return f"""
Create a personalized {topic} learning plan for 3-6 months.

CURRENT PROFILE:
- Experience Level: {experience_level.value}
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
    
    async def _call_langchain_async(self, prompt: str, temperature: float, max_tokens: int) -> str:
        """Make async call to LangChain ChatOpenAI"""
        try:
            # Create a new LLM instance with specific parameters for this call
            llm = ChatOpenAI(
                model="gpt-4",
                temperature=temperature,
                openai_api_key=settings.OPENAI_API_KEY,
                max_tokens=max_tokens
            )
            
            # Create messages
            messages = [
                SystemMessage(content="You are an expert technical skill assessor and career mentor. Provide accurate, practical, and actionable advice."),
                HumanMessage(content=prompt)
            ]
            
            # Make async call with callback tracking
            with get_openai_callback() as cb:
                response = await llm.ainvoke(messages)
                logger.info(f"LangChain API call - Tokens: {cb.total_tokens}, Cost: ${cb.total_cost}")
            
            return response.content
            
        except Exception as e:
            logger.error(f"LangChain API call failed: {e}")
            raise
    
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
                resources.append(LearningResource(
                    title=res_data.get("title", ""),
                    type=res_data.get("type", "course"),
                    url=res_data.get("url"),
                    cost=res_data.get("cost", "Unknown"),
                    difficulty=DifficultyLevel(res_data.get("difficulty", "medium")),
                    estimated_hours=res_data.get("estimated_hours")
                ))
            
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
                difficulty=DifficultyLevel(proj_data.get("difficulty", "medium")),
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
            created_at=None
        )
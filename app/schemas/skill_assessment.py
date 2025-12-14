from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum

# Enums
class ExperienceLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

class DifficultyLevel(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

class QuestionType(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    SCENARIO_BASED = "scenario_based"

class ExpertiseLevel(str, Enum):
    NOVICE = "novice"
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"

# Request Schemas
class AssessmentStartRequest(BaseModel):
    topic: str = Field(..., min_length=2, max_length=100, description="Skill topic to assess")
    experience_level: ExperienceLevel = Field(..., description="Self-reported experience level")

class QuizSubmissionRequest(BaseModel):
    answers: List[Dict[str, Any]] = Field(..., description="User answers to quiz questions")
    
    class Config:
        schema_extra = {
            "example": {
                "answers": [
                    {"question_id": 1, "user_answer": "Option A", "time_taken": 30, "is_skipped": False, "is_unsure": False},
                    {"question_id": 2, "user_answer": "Not Sure", "time_taken": 15, "is_skipped": False, "is_unsure": True},
                    {"question_id": 3, "user_answer": "SKIPPED", "time_taken": 5, "is_skipped": True, "is_unsure": False}
                ]
            }
        }

# Response Schemas
class QuizOption(BaseModel):
    id: str = Field(..., description="Option identifier")
    text: str = Field(..., description="Option text")

class QuizQuestionResponse(BaseModel):
    id: int = Field(..., description="Question ID")
    question_text: str = Field(..., description="Question content")
    options: List[QuizOption] = Field(..., description="Answer options")
    difficulty_level: DifficultyLevel = Field(..., description="Question difficulty")
    question_type: QuestionType = Field(default=QuestionType.MULTIPLE_CHOICE, description="Type of question")
    scenario_context: Optional[str] = Field(None, description="Context for scenario-based questions")
    question_order: int = Field(..., description="Question sequence number")

class AssessmentStartResponse(BaseModel):
    assessment_id: int = Field(..., description="Assessment session ID")
    topic: str = Field(..., description="Assessment topic")
    total_questions: int = Field(..., description="Number of questions")
    estimated_minutes: int = Field(..., description="Estimated completion time")
    questions: List[QuizQuestionResponse] = Field(..., description="Quiz questions")

class SkillAreaScore(BaseModel):
    area: str = Field(..., description="Skill area name")
    score: float = Field(..., ge=0, le=100, description="Score percentage")
    level: str = Field(..., description="Proficiency level")

class EvaluationSummary(BaseModel):
    assessment_id: int = Field(..., description="Assessment ID")
    overall_score: float = Field(..., ge=0, le=100, description="Overall score percentage")
    expertise_level: ExpertiseLevel = Field(..., description="Calculated expertise level")
    strengths: List[str] = Field(..., description="Strong skill areas")
    weaknesses: List[str] = Field(..., description="Areas needing improvement")
    skill_breakdown: List[SkillAreaScore] = Field(..., description="Detailed skill area scores")

class LearningResource(BaseModel):
    title: str = Field(..., description="Resource title")
    type: str = Field(..., description="Resource type (course, book, tutorial, etc.)")
    url: Optional[str] = Field(None, description="Resource URL")
    cost: str = Field(..., description="Cost information (Free, $X, etc.)")
    difficulty: DifficultyLevel = Field(..., description="Resource difficulty level")
    estimated_hours: Optional[float] = Field(None, description="Estimated study hours (can be fractional)")

class LearningModule(BaseModel):
    title: str = Field(..., description="Module title")
    description: str = Field(..., description="Module description")
    duration_weeks: int = Field(..., ge=1, description="Module duration in weeks")
    resources: List[LearningResource] = Field(default=[], description="Recommended resources")
    learning_objectives: List[str] = Field(default=[], description="Learning objectives for this module")
    weekly_breakdown: List[Dict[str, Any]] = Field(default=[], description="Week-by-week breakdown of the module")

class ProjectIdea(BaseModel):
    title: str = Field(..., description="Project title")
    description: str = Field(..., description="Project description")
    difficulty: DifficultyLevel = Field(..., description="Project difficulty")
    duration_weeks: int = Field(default=2, description="Estimated project duration in weeks")
    technologies: List[str] = Field(default=[], description="Technologies used in project")
    learning_objectives: List[str] = Field(default=[], description="Skills this project helps develop")

class MarketTrend(BaseModel):
    trend_name: str = Field(..., description="Market trend name")
    relevance_score: int = Field(..., ge=0, le=100, description="Relevance score 0-100")
    time_to_learn_weeks: int = Field(..., ge=1, description="Estimated time to learn in weeks")
    job_market_impact: str = Field(..., description="Impact on job market")
    resources: List[str] = Field(default=[], description="Learning resources for this trend")

class LearningPlanResponse(BaseModel):
    assessment_id: int = Field(..., description="Assessment ID")
    plan_id: int = Field(..., description="Learning plan ID")
    timeline_weeks: int = Field(..., description="Recommended timeline in weeks")
    learning_modules: List[LearningModule] = Field(..., description="Structured learning modules")
    priority_skills: List[str] = Field(..., description="High-priority skills to focus on")
    project_ideas: List[ProjectIdea] = Field(..., description="Practical project suggestions")
    market_trends: List[MarketTrend] = Field(..., description="Relevant market insights")
    learning_resources: List[LearningResource] = Field(default=[], description="Recommended learning resources")
    career_progression: Optional[str] = Field(None, description="Career progression guidance")
    market_research_insights: Optional[Dict] = Field(None, description="Market research insights")
    created_at: datetime = Field(..., description="Plan creation timestamp")

class DashboardData(BaseModel):
    assessment_id: int = Field(..., description="Assessment ID")
    topic: str = Field(..., description="Assessment topic")
    evaluation: Optional[EvaluationSummary] = Field(None, description="Assessment evaluation results")
    learning_plan: Optional[LearningPlanResponse] = Field(None, description="Learning plan if generated")
    completion_status: str = Field(..., description="Assessment completion status")
    created_at: datetime = Field(..., description="Assessment creation date")

# Database model response schemas
class SkillAssessmentResponse(BaseModel):
    id: int
    user_id: int
    topic: str
    experience_level: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class QuizAnswerResponse(BaseModel):
    id: int
    question_id: int
    user_answer: str
    is_correct: Optional[bool]
    score: Optional[float]
    answered_at: datetime
    
    class Config:
        from_attributes = True
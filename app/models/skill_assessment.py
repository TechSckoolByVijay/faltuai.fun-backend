from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, ForeignKey, Boolean, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base

class ExperienceLevel(str, enum.Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

class DifficultyLevel(str, enum.Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

class SkillAssessment(Base):
    """Skill assessment table with descriptive naming"""
    __tablename__ = "sa_skill_assessments"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    topic = Column(String(100), nullable=False, index=True)
    experience_level = Column(String(20), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    questions = relationship("QuizQuestion", back_populates="assessment", cascade="all, delete-orphan")
    evaluation_result = relationship("SkillEvaluationResult", back_populates="assessment", uselist=False, cascade="all, delete-orphan")
    learning_plan = relationship("LearningPlan", back_populates="assessment", uselist=False, cascade="all, delete-orphan")

class QuizQuestion(Base):
    """Quiz questions table"""
    __tablename__ = "sa_quiz_questions"
    
    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(Integer, ForeignKey("sa_skill_assessments.id"), nullable=False, index=True)
    question_text = Column(Text, nullable=False)
    options = Column(JSON, nullable=False)  # Array of options
    correct_answer = Column(String(500), nullable=True)  # AI-generated, can be null for subjective
    difficulty_level = Column(String(20), nullable=False, default="medium")
    question_order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    assessment = relationship("SkillAssessment", back_populates="questions")
    answers = relationship("QuizAnswer", back_populates="question", cascade="all, delete-orphan")

class QuizAnswer(Base):
    """User answers to quiz questions"""
    __tablename__ = "sa_quiz_answers"
    
    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("sa_quiz_questions.id"), nullable=False, index=True)
    user_answer = Column(String(500), nullable=False)
    is_correct = Column(Boolean, nullable=True)  # Can be null for AI evaluation
    score = Column(Float, nullable=True, default=0.0)  # Partial scoring for complex answers
    answered_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    question = relationship("QuizQuestion", back_populates="answers")

class SkillEvaluationResult(Base):
    """AI evaluation results for skill assessment"""
    __tablename__ = "sa_skill_evaluation_results"
    
    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(Integer, ForeignKey("sa_skill_assessments.id"), nullable=False, unique=True, index=True)
    strengths = Column(JSON, nullable=False)  # Array of strength areas
    weaknesses = Column(JSON, nullable=False)  # Array of weak areas
    overall_score = Column(Float, nullable=False)  # 0-100 scale
    expertise_level = Column(String(20), nullable=False)  # Calculated expertise
    detailed_analysis = Column(JSON, nullable=True)  # Detailed breakdown by skill area
    market_insights = Column(JSON, nullable=True)  # Current market trends relevance
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    assessment = relationship("SkillAssessment", back_populates="evaluation_result")

class LearningPlan(Base):
    """Personalized learning plan based on assessment"""
    __tablename__ = "sa_learning_plans"
    
    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(Integer, ForeignKey("sa_skill_assessments.id"), nullable=False, unique=True, index=True)
    plan_content = Column(JSON, nullable=False)  # Structured learning roadmap
    timeline_weeks = Column(Integer, nullable=True, default=12)  # Estimated completion time
    priority_skills = Column(JSON, nullable=False)  # High-priority skills to focus on
    recommended_resources = Column(JSON, nullable=False)  # Curated resources (free + paid)
    project_ideas = Column(JSON, nullable=True)  # Practical project suggestions
    market_trends = Column(JSON, nullable=True)  # Current market demand insights
    export_count = Column(Integer, nullable=False, default=0)  # PDF export tracking
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    assessment = relationship("SkillAssessment", back_populates="learning_plan")
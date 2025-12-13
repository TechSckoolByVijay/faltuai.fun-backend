from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List, Dict, Any
import json
import asyncio
from datetime import datetime

# Local imports
from app.core.database import get_db
from app.core.security import get_current_active_user
from app.services.common import db_service
from app.models.user import User
from app.models.skill_assessment import (
    SkillAssessment, 
    QuizQuestion, 
    QuizAnswer, 
    SkillEvaluationResult, 
    LearningPlan
)
from app.schemas.skill_assessment import (
    AssessmentStartRequest,
    AssessmentStartResponse,
    QuizSubmissionRequest,
    EvaluationSummary,
    LearningPlanResponse,
    DashboardData,
    QuizQuestionResponse,
    QuizOption,
    ExperienceLevel
)
from app.services.skill_assessment_ai_service import SkillAssessmentAIService

import logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/skill-assessment", tags=["Skill Assessment"])

# Initialize AI service
ai_service = SkillAssessmentAIService()

@router.post("/start", response_model=AssessmentStartResponse)
async def start_assessment(
    request: AssessmentStartRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Start a new skill assessment
    1. Create assessment record
    2. Generate AI quiz questions
    3. Save questions to database
    4. Return assessment ID and questions
    """
    try:
        user_id = current_user.id
        
        # Create assessment record
        assessment = SkillAssessment(
            user_id=user_id,
            topic=request.topic,
            experience_level=request.experience_level.value
        )
        
        db.add(assessment)
        await db.flush()  # Get the assessment ID
        
        # Generate quiz questions using AI (dynamic count based on topic/experience)
        ai_questions = await ai_service.generate_quiz_questions(
            topic=request.topic,
            experience_level=request.experience_level
            # num_questions is now calculated automatically
        )
        
        # Save questions to database
        db_questions = []
        for i, q in enumerate(ai_questions):
            db_question = QuizQuestion(
                assessment_id=assessment.id,
                question_text=q.question_text,
                options=json.dumps([opt.dict() for opt in q.options]),  # Store as JSON
                correct_answer=None,  # Will be determined during evaluation
                difficulty_level=q.difficulty_level.value,
                question_order=i + 1
            )
            db.add(db_question)
            db_questions.append(db_question)
        
        await db.commit()
        
        # Refresh to get IDs
        for db_q in db_questions:
            await db.refresh(db_q)
        
        # Update response with actual database IDs
        questions_response = []
        for db_q, ai_q in zip(db_questions, ai_questions):
            questions_response.append(QuizQuestionResponse(
                id=db_q.id,
                question_text=db_q.question_text,
                options=ai_q.options,
                difficulty_level=ai_q.difficulty_level,
                question_order=db_q.question_order
            ))
        
        return AssessmentStartResponse(
            assessment_id=assessment.id,
            topic=assessment.topic,
            total_questions=len(questions_response),
            estimated_minutes=len(questions_response) * 2,  # 2 minutes per question
            questions=questions_response
        )
        
    except Exception as e:
        logger.error(f"Error starting assessment: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to start assessment")

@router.post("/assessment/{assessment_id}/submit", response_model=EvaluationSummary)
async def submit_quiz_answers(
    assessment_id: int,
    request: QuizSubmissionRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Submit quiz answers and get evaluation
    1. Validate assessment ownership
    2. Save user answers
    3. Use AI to evaluate answers
    4. Save evaluation results
    5. Return evaluation summary
    """
    try:
        user_id = current_user.id
        
        # Get assessment with questions
        result = await db.execute(
            select(SkillAssessment)
            .options(selectinload(SkillAssessment.questions))
            .filter(SkillAssessment.id == assessment_id, SkillAssessment.user_id == user_id)
        )
        assessment = result.scalar_one_or_none()
        
        if not assessment:
            raise HTTPException(status_code=404, detail="Assessment not found")
        
        # Save user answers
        for answer_data in request.answers:
            quiz_answer = QuizAnswer(
                question_id=answer_data["question_id"],
                user_answer=answer_data["user_answer"],
                is_correct=None,  # Will be determined by AI
                score=None  # Will be determined by AI
            )
            db.add(quiz_answer)
        
        await db.flush()
        
        # Prepare data for AI evaluation
        questions_data = []
        for question in assessment.questions:
            questions_data.append({
                "id": question.id,
                "question_text": question.question_text,
                "options": json.loads(question.options),
                "difficulty_level": question.difficulty_level
            })
        
        # Use AI to evaluate answers
        # Convert string back to enum for AI service
        experience_level_enum = ExperienceLevel(assessment.experience_level)
        evaluation = await ai_service.evaluate_quiz_answers(
            topic=assessment.topic,
            questions=questions_data,
            answers=request.answers,
            experience_level=experience_level_enum
        )
        
        # Save evaluation results
        evaluation_result = SkillEvaluationResult(
            assessment_id=assessment.id,
            strengths=json.dumps(evaluation.strengths),
            weaknesses=json.dumps(evaluation.weaknesses),
            overall_score=evaluation.overall_score,
            expertise_level=evaluation.expertise_level.value,
            detailed_analysis=json.dumps([sb.dict() for sb in evaluation.skill_breakdown]),
            market_insights=json.dumps([])  # TODO: Add market insights
        )
        
        db.add(evaluation_result)
        await db.commit()
        
        # Update evaluation with assessment ID
        evaluation.assessment_id = assessment_id
        
        return evaluation
        
    except Exception as e:
        logger.error(f"Error submitting quiz answers: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to evaluate quiz answers")

@router.post("/assessment/{assessment_id}/learning-plan", response_model=LearningPlanResponse)
async def generate_learning_plan(
    assessment_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate personalized learning plan
    1. Get assessment and evaluation results
    2. Use AI to create learning plan
    3. Save learning plan
    4. Return structured plan
    """
    try:
        user_id = current_user.id
        
        # Get assessment with evaluation
        result = await db.execute(
            select(SkillAssessment)
            .options(selectinload(SkillAssessment.evaluation_result))
            .filter(SkillAssessment.id == assessment_id, SkillAssessment.user_id == user_id)
        )
        assessment = result.scalar_one_or_none()
        
        if not assessment or not assessment.evaluation_result:
            raise HTTPException(status_code=404, detail="Assessment or evaluation not found")
        
        # Convert stored evaluation to schema
        eval_result = assessment.evaluation_result
        evaluation = EvaluationSummary(
            assessment_id=assessment.id,
            overall_score=eval_result.overall_score,
            expertise_level=eval_result.expertise_level,
            strengths=json.loads(eval_result.strengths),
            weaknesses=json.loads(eval_result.weaknesses),
            skill_breakdown=[]  # TODO: Parse from detailed_analysis
        )
        
        # Generate learning plan using AI
        learning_plan = await ai_service.generate_learning_plan(
            topic=assessment.topic,
            evaluation=evaluation,
            user_experience_level=assessment.experience_level
        )
        
        # Debug logging
        logger.info(f"Generated learning plan: modules={len(learning_plan.learning_modules)}, projects={len(learning_plan.project_ideas)}, trends={len(learning_plan.market_trends)}")
        
        # Save learning plan to database
        # Store the complete plan in plan_content for retrieval
        plan_content = {
            "learning_modules": [mod.dict() for mod in learning_plan.learning_modules],
            "project_ideas": [proj.dict() for proj in learning_plan.project_ideas],
            "market_trends": [trend.dict() for trend in learning_plan.market_trends],
            "learning_resources": [res.dict() for res in learning_plan.learning_resources] if hasattr(learning_plan, 'learning_resources') else [],
            "career_progression": learning_plan.career_progression if hasattr(learning_plan, 'career_progression') else None,
            "market_research_insights": learning_plan.market_research_insights if hasattr(learning_plan, 'market_research_insights') else None
        }
        
        db_learning_plan = LearningPlan(
            assessment_id=assessment.id,
            plan_content=json.dumps(plan_content),
            timeline_weeks=learning_plan.timeline_weeks,
            priority_skills=json.dumps(learning_plan.priority_skills),
            recommended_resources=json.dumps([]),  # Deprecated - keeping for backward compatibility
            project_ideas=json.dumps([]),  # Deprecated - data now in plan_content
            market_trends=json.dumps([])  # Deprecated - data now in plan_content
        )
        
        db.add(db_learning_plan)
        await db.commit()
        await db.refresh(db_learning_plan)
        
        # Update response with database info
        learning_plan.assessment_id = assessment.id
        learning_plan.plan_id = db_learning_plan.id
        learning_plan.created_at = db_learning_plan.created_at
        
        return learning_plan
        
    except Exception as e:
        logger.error(f"Error generating learning plan: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to generate learning plan")

@router.get("/assessment/{assessment_id}/dashboard", response_model=DashboardData)
async def get_assessment_dashboard(
    assessment_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get comprehensive dashboard data for assessment
    1. Assessment details
    2. Evaluation results
    3. Learning plan (if generated)
    4. Progress tracking
    """
    try:
        user_id = current_user.id
        
        # Get complete assessment data
        result = await db.execute(
            select(SkillAssessment)
            .options(
                selectinload(SkillAssessment.evaluation_result),
                selectinload(SkillAssessment.learning_plan)
            )
            .filter(SkillAssessment.id == assessment_id, SkillAssessment.user_id == user_id)
        )
        assessment = result.scalar_one_or_none()
        
        if not assessment:
            raise HTTPException(status_code=404, detail="Assessment not found")
        
        # Build evaluation summary
        evaluation = None
        if assessment.evaluation_result:
            eval_result = assessment.evaluation_result
            evaluation = EvaluationSummary(
                assessment_id=assessment.id,
                overall_score=eval_result.overall_score,
                expertise_level=eval_result.expertise_level,
                strengths=json.loads(eval_result.strengths),
                weaknesses=json.loads(eval_result.weaknesses),
                skill_breakdown=[]
            )
        
        # Build learning plan response
        learning_plan = None
        if assessment.learning_plan:
            plan_data = json.loads(assessment.learning_plan.plan_content)
            learning_plan = LearningPlanResponse(
                assessment_id=assessment.id,
                plan_id=assessment.learning_plan.id,
                timeline_weeks=assessment.learning_plan.timeline_weeks,
                learning_modules=plan_data.get("learning_modules", []),
                priority_skills=json.loads(assessment.learning_plan.priority_skills),
                project_ideas=plan_data.get("project_ideas", []),
                market_trends=plan_data.get("market_trends", []),
                learning_resources=plan_data.get("learning_resources", []),
                career_progression=plan_data.get("career_progression"),
                market_research_insights=plan_data.get("market_research_insights"),
                created_at=assessment.learning_plan.created_at
            )
        
        # Determine completion status
        completion_status = "started"
        if assessment.evaluation_result:
            completion_status = "evaluated"
        if assessment.learning_plan:
            completion_status = "completed"
        
        dashboard_data = DashboardData(
            assessment_id=assessment.id,
            topic=assessment.topic,
            evaluation=evaluation,
            learning_plan=learning_plan,
            completion_status=completion_status,
            created_at=assessment.created_at
        )
        
        return dashboard_data
        
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        raise HTTPException(status_code=500, detail="Failed to get dashboard data")

@router.get("/assessment/{assessment_id}/export/pdf")
async def export_learning_plan_pdf(
    assessment_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Export learning plan as PDF
    1. Get learning plan data
    2. Generate PDF document
    3. Track export count
    4. Return PDF file
    """
    try:
        from app.services.pdf_service import PDFService
        from fastapi.responses import Response
        
        user_id = current_user.id
        
        # Get assessment with learning plan and evaluation result
        result = await db.execute(
            select(SkillAssessment)
            .options(
                selectinload(SkillAssessment.learning_plan),
                selectinload(SkillAssessment.evaluation_result)
            )
            .filter(SkillAssessment.id == assessment_id, SkillAssessment.user_id == user_id)
        )
        assessment = result.scalar_one_or_none()
        
        if not assessment or not assessment.learning_plan or not assessment.evaluation_result:
            raise HTTPException(status_code=404, detail="Learning plan or evaluation result not found")
        
        # Prepare assessment data for PDF
        plan_data = json.loads(assessment.learning_plan.plan_content)
        assessment_data = {
            "id": assessment.id,
            "topic": assessment.topic,
            "experience_level": assessment.experience_level,
            "overall_score": assessment.evaluation_result.overall_score,
            "strengths": assessment.evaluation_result.strengths or [],
            "areas_for_improvement": assessment.evaluation_result.weaknesses or [],
            "created_at": assessment.created_at.strftime('%Y-%m-%d %H:%M'),
            "learning_plan": plan_data
        }
        
        # Generate PDF
        pdf_service = PDFService()
        pdf_data = pdf_service.generate_learning_plan_pdf(assessment_data)
        
        # Update export count
        assessment.learning_plan.export_count += 1
        await db.commit()
        
        # Return PDF file
        filename = f"learning_plan_{assessment.topic.replace(' ', '_')}_{assessment.id}.pdf"
        return Response(
            content=pdf_data,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": "application/pdf"
            }
        )
        
    except Exception as e:
        logger.error(f"Error exporting PDF: {e}")
        raise HTTPException(status_code=500, detail="Failed to export PDF")

@router.get("/assessments", response_model=List[DashboardData])
async def get_user_assessments(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all assessments for current user
    """
    try:
        user_id = current_user.id
        
        # Get all user assessments
        result = await db.execute(
            select(SkillAssessment)
            .options(
                selectinload(SkillAssessment.evaluation_result),
                selectinload(SkillAssessment.learning_plan)
            )
            .filter(SkillAssessment.user_id == user_id)
            .order_by(SkillAssessment.created_at.desc())
        )
        assessments = result.scalars().all()
        
        dashboard_list = []
        for assessment in assessments:
            # Build evaluation summary
            evaluation = None
            if assessment.evaluation_result:
                eval_result = assessment.evaluation_result
                evaluation = EvaluationSummary(
                    assessment_id=assessment.id,
                    overall_score=eval_result.overall_score,
                    expertise_level=eval_result.expertise_level,
                    strengths=json.loads(eval_result.strengths),
                    weaknesses=json.loads(eval_result.weaknesses),
                    skill_breakdown=[]
                )
            
            # Determine completion status
            completion_status = "started"
            if assessment.evaluation_result:
                completion_status = "evaluated"
            if assessment.learning_plan:
                completion_status = "completed"
            
            dashboard_data = DashboardData(
                assessment_id=assessment.id,
                topic=assessment.topic,
                evaluation=evaluation,
                learning_plan=None,  # Don't include full plan in list
                completion_status=completion_status,
                created_at=assessment.created_at
            )
            dashboard_list.append(dashboard_data)
        
        return dashboard_list
        
    except Exception as e:
        logger.error(f"Error getting user assessments: {e}")
        raise HTTPException(status_code=500, detail="Failed to get assessments")

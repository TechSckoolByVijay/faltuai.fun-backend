"""
LangGraph-based Learning Plan Generation Agent

This agent uses a multi-stage research and generation process to create
comprehensive, personalized learning plans with real-world market research.
"""

import json
import asyncio
from typing import TypedDict, List, Dict, Any, Annotated
from datetime import datetime
import logging

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.services.common import llm_service
from app.services.market_research_agent import market_research_agent
from app.utils.date_utils import current_period
from app.schemas.skill_assessment import (
    ExperienceLevel,
    LearningPlanResponse,
    LearningModule,
    LearningResource,
    ProjectIdea,
    MarketTrend,
    DifficultyLevel
)

logger = logging.getLogger(__name__)


class LearningPlanState(TypedDict):
    """State for learning plan generation workflow"""
    topic: str
    experience_level: str
    strengths: List[str]
    weaknesses: List[str]
    overall_score: int
    
    # Research phase outputs
    market_research: Dict[str, Any]
    skill_gaps: List[str]
    trending_technologies: List[str]
    
    # Planning phase outputs
    learning_objectives: List[str]
    timeline_weeks: int
    priority_skills: List[str]
    
    # Content generation outputs
    learning_modules: List[Dict[str, Any]]
    project_ideas: List[Dict[str, Any]]
    resources: List[Dict[str, Any]]
    
    # Final output
    learning_plan: Dict[str, Any]
    error: str


class LearningPlanAgent:
    """
    Multi-stage agent for generating comprehensive learning plans.
    
    Workflow:
    1. Market Research: Analyze current trends, job market, salary data
    2. Skill Gap Analysis: Identify what user needs to learn
    3. Learning Path Design: Create structured curriculum
    4. Resource Curation: Find specific courses, tutorials, projects
    5. Timeline Planning: Break down into weekly goals
    6. Assembly: Combine all into comprehensive plan
    """
    
    def __init__(self):
        self.market_agent = market_research_agent
        self.graph = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow for learning plan generation"""
        workflow = StateGraph(LearningPlanState)
        
        # Add nodes for each stage
        workflow.add_node("research_market", self._market_research_node)
        workflow.add_node("analyze_gaps", self._skill_gap_analysis_node)
        workflow.add_node("define_objectives", self._learning_objectives_node)
        workflow.add_node("design_curriculum", self._curriculum_design_node)
        workflow.add_node("curate_resources", self._resource_curation_node)
        workflow.add_node("generate_projects", self._project_generation_node)
        workflow.add_node("plan_timeline", self._timeline_planning_node)
        workflow.add_node("assemble_plan", self._final_assembly_node)
        
        # Define workflow edges
        workflow.set_entry_point("research_market")
        workflow.add_edge("research_market", "analyze_gaps")
        workflow.add_edge("analyze_gaps", "define_objectives")
        workflow.add_edge("define_objectives", "design_curriculum")
        workflow.add_edge("design_curriculum", "curate_resources")
        workflow.add_edge("curate_resources", "generate_projects")
        workflow.add_edge("generate_projects", "plan_timeline")
        workflow.add_edge("plan_timeline", "assemble_plan")
        workflow.add_edge("assemble_plan", END)
        
        return workflow.compile()
    
    async def _market_research_node(self, state: LearningPlanState) -> LearningPlanState:
        """Node 1: Conduct market research for the skill area"""
        logger.info(f"Starting market research for {state['topic']}")
        
        try:
            # Use existing market research agent
            research_result = await self.market_agent.research_market_trends(
                topic=state['topic'],
                experience_level=state['experience_level']
            )
            
            state['market_research'] = research_result
            
            # Extract trending technologies
            market_insights = research_result.get('market_insights', {})
            state['trending_technologies'] = market_insights.get('emerging_technologies', [])
            
            logger.info(f"Market research completed. Found {len(state['trending_technologies'])} trending technologies")
            
        except Exception as e:
            logger.error(f"Market research failed: {e}")
            state['error'] = f"Market research failed: {str(e)}"
            state['market_research'] = {}
            state['trending_technologies'] = []
        
        return state
    
    async def _skill_gap_analysis_node(self, state: LearningPlanState) -> LearningPlanState:
        """Node 2: Analyze skill gaps based on assessment and market data"""
        logger.info("Analyzing skill gaps")
        
        prompt = f"""
You are a career development expert analyzing skill gaps for a {state['experience_level']} level professional in {state['topic']}.

Assessment Results:
- Overall Score: {state['overall_score']}/100
- Strengths: {', '.join(state['strengths'])}
- Weaknesses: {', '.join(state['weaknesses'])}

Market Trends:
- Trending Technologies: {', '.join(state['trending_technologies'][:5])}

Based on this information, identify:
1. Critical skill gaps that need immediate attention
2. Emerging skills for future career growth
3. Foundational skills that need strengthening

Provide a prioritized list of 8-12 specific skills to learn.

Return as JSON:
{{
    "critical_gaps": ["skill1", "skill2", "skill3"],
    "emerging_skills": ["skill1", "skill2", "skill3"],
    "foundational_skills": ["skill1", "skill2"]
}}
"""
        
        try:
            response = await llm_service.generate_structured_response(
                prompt=prompt,
                schema_description="JSON with critical_gaps, emerging_skills, and foundational_skills arrays",
                temperature=0.7
            )
            
            # Combine all skill gaps
            all_gaps = (
                response.get('critical_gaps', []) +
                response.get('emerging_skills', []) +
                response.get('foundational_skills', [])
            )
            
            state['skill_gaps'] = all_gaps[:12]  # Limit to top 12
            state['priority_skills'] = response.get('critical_gaps', [])[:5]
            
            logger.info(f"Identified {len(state['skill_gaps'])} skill gaps")
            
        except Exception as e:
            logger.error(f"Skill gap analysis failed: {e}")
            state['skill_gaps'] = state['weaknesses'][:5]
            state['priority_skills'] = state['weaknesses'][:3]
        
        return state
    
    async def _learning_objectives_node(self, state: LearningPlanState) -> LearningPlanState:
        """Node 3: Define clear, measurable learning objectives"""
        logger.info("Defining learning objectives")
        
        prompt = f"""
You are an instructional designer creating learning objectives for a {state['experience_level']} {state['topic']} professional.

Skills to Learn:
{chr(10).join(f"- {skill}" for skill in state['skill_gaps'])}

Create 6-10 SMART learning objectives that:
1. Are specific and measurable
2. Build progressively from fundamentals to advanced
3. Align with current industry needs ({current_period['quarter_full']})
4. Can be achieved within 12-16 weeks

Return as JSON:
{{
    "objectives": [
        {{
            "title": "Objective title",
            "description": "Detailed description",
            "skills_covered": ["skill1", "skill2"],
            "success_criteria": "How to measure achievement",
            "estimated_weeks": 2
        }}
    ]
}}
"""
        
        try:
            response = await llm_service.generate_structured_response(
                prompt=prompt,
                schema_description="JSON with objectives array containing learning objectives",
                temperature=0.7
            )
            
            state['learning_objectives'] = response.get('objectives', [])
            
            # Calculate total timeline
            total_weeks = sum(obj.get('estimated_weeks', 2) for obj in state['learning_objectives'])
            state['timeline_weeks'] = min(max(total_weeks, 8), 16)  # 8-16 weeks
            
            logger.info(f"Created {len(state['learning_objectives'])} learning objectives, {state['timeline_weeks']} weeks timeline")
            
        except Exception as e:
            logger.error(f"Learning objectives generation failed: {e}")
            state['learning_objectives'] = []
            state['timeline_weeks'] = 12
        
        return state
    
    async def _curriculum_design_node(self, state: LearningPlanState) -> LearningPlanState:
        """Node 4: Design structured curriculum with modules"""
        logger.info("Designing curriculum structure")
        
        # Build detailed skill analysis for context
        strengths_context = "\n".join(f"- STRENGTH: {s}" for s in state['strengths'][:5])
        weaknesses_context = "\n".join(f"- WEAKNESS: {w}" for w in state['weaknesses'][:5])
        # Handle skill_gaps - could be list of strings or list of dicts
        skill_gaps_list = state['skill_gaps'][:8]
        gaps_context = "\n".join(
            f"- GAP: {gap.get('skill', gap) if isinstance(gap, dict) else gap}" 
            for gap in skill_gaps_list
        )
        
        prompt = f"""
You are an expert curriculum designer creating an IN-DEPTH, COMPREHENSIVE learning path for {state['topic']} at {state['experience_level']} level.

Student's Current Profile:
{strengths_context}

{weaknesses_context}

{gaps_context}

Learning Objectives:
{chr(10).join(f"- {obj.get('title', '')}: {obj.get('description', '')}" for obj in state['learning_objectives'])}

Timeline: {state['timeline_weeks']} weeks
Trending Technologies to Integrate: {', '.join(state['trending_technologies'][:5])}
Market Insights: {state.get('market_insights', {}).get('summary', 'Focus on practical, job-ready skills')}

Design 4-6 HIGHLY DETAILED learning modules that:
1. Build progressively from basics to advanced concepts
2. Each module spans 2-3 weeks
3. For EACH module, provide:
   - A 2-3 sentence description (max 250 characters) explaining what students learn and why
   - How this module addresses their specific weaknesses
   - List 5-8 specific topics
   - Define 3-5 clear, measurable learning outcomes
   - Provide detailed week-by-week breakdown (see requirements below)

WEEKLY BREAKDOWN REQUIREMENTS (MOST IMPORTANT):
For each week in the module:
- Theme: Clear weekly focus area
- Focus Area: Which specific student weakness this week addresses  
- Why This Week: 1-2 sentences (max 200 chars) explaining connection to weaknesses and trends
- Goals: 3 specific, measurable learning goals
- Daily Breakdown: Array of 3 strings for Day 1-2, Day 3-4, Day 5-7
- Deliverables: Array of 2 concrete outputs
- Resources: Array of 1-2 resource names
- Time Commitment: Hours per week (number)

IMPORTANT JSON RULES:
- Keep all text fields under 200 characters to avoid length limits
- Use proper JSON escaping for quotes
- Ensure all strings are properly closed
- Prioritize clarity over verbosity

CRITICAL REQUIREMENTS:
- Make descriptions 3X MORE DETAILED than typical course outlines
- Include specific technical concepts, not vague statements
- Explain the "WHY" behind each module (career relevance, industry demand)
- Reference real technologies, frameworks, and tools by name
- Connect to student's strengths and weaknesses explicitly
- Make it actionable with concrete examples
- WEEKLY BREAKDOWN IS MANDATORY - each module must have detailed week-by-week plan

CRITICAL: Return ONLY valid JSON. NO markdown code blocks, NO explanations, ONLY the JSON object.

Return as JSON:
{{
    "modules": [
        {{
            "title": "Descriptive Module Title",
            "description": "DETAILED 3-5 sentence description explaining: (1) What concepts are covered, (2) Why they're important for career growth, (3) How they address specific weaknesses, (4) Real-world applications, (5) Industry relevance. Be SPECIFIC with technology names and concepts.",
            "duration_weeks": 2,
            "topics": ["Specific Topic 1 with details", "Topic 2: Subtopic A and B", "Advanced Topic 3", "etc..."],
            "learning_objectives": [
                "Specific, measurable objective 1 with technical detail",
                "Objective 2 that addresses a weakness",
                "Objective 3 with real-world application"
            ],
            "practical_exercises": [
                "Hands-on exercise 1 with detailed steps",
                "Real-world project exercise 2"
            ],
            "weekly_breakdown": [
                {{
                    "week": 1,
                    "theme": "Specific weekly theme",
                    "focus_area": "Primary skill/weakness being addressed this week",
                    "why_this_week": "2-3 sentence justification: How this week's content addresses specific student weaknesses and aligns with market trends. Connect to their assessment results.",
                    "goals": ["Detailed learning goal 1", "Goal 2 with technical specifics", "Goal 3"],
                    "daily_breakdown": [
                        "Day 1-2: Specific activities and concepts",
                        "Day 3-4: Hands-on practice tasks",
                        "Day 5-7: Project work and review"
                    ],
                    "deliverables": ["Concrete deliverable 1 with success criteria", "Mini-project/exercise"],
                    "resources_to_use": ["Specific resource recommendation"],
                    "time_commitment_hours": 8
                }}
            ]
        }}
    ]
}}
"""
        
        # Retry logic for malformed JSON
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = await llm_service.generate_structured_response(
                    prompt=prompt,
                    schema_description="JSON with modules array containing detailed curriculum structure",
                    temperature=0.7 - (attempt * 0.1)  # Reduce temperature on retries
                )
                
                modules = response.get('modules', [])
                if modules:  # Only accept if we got modules
                    state['learning_modules'] = modules
                    logger.info(f"Created {len(state['learning_modules'])} learning modules")
                    break
                else:
                    logger.warning(f"Attempt {attempt + 1}: Empty modules array")
                    
            except Exception as e:
                logger.error(f"Curriculum design attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    logger.error("All retry attempts failed, using fallback")
                    state['learning_modules'] = []
        
        return state
    
    async def _resource_curation_node(self, state: LearningPlanState) -> LearningPlanState:
        """Node 5: Curate specific learning resources for each module"""
        logger.info("Curating learning resources")
        
        all_resources = []
        
        for module in state['learning_modules']:
            prompt = f"""
You are a learning resource curator finding the best online resources for {current_period['quarter_full']}.

Module: {module.get('title', '')}
Topics: {', '.join(module.get('topics', []))}
Level: {state['experience_level']}

Find 3-5 high-quality resources for this module:
1. Include mix of courses, tutorials, documentation, videos
2. Prefer free or affordable options
3. Use real, popular platforms (Coursera, Udemy, freeCodeCamp, YouTube, official docs)
4. Provide actual resource names that likely exist

Return as JSON:
{{
    "resources": [
        {{
            "title": "Actual course/tutorial name",
            "type": "course|tutorial|video|documentation|book",
            "platform": "Platform name",
            "url_pattern": "Likely URL pattern",
            "difficulty": "beginner|intermediate|advanced",
            "estimated_hours": 10,
            "cost": "free|paid",
            "topics_covered": ["topic1", "topic2"],
            "why_recommended": "Brief explanation"
        }}
    ]
}}
"""
            
            try:
                response = await llm_service.generate_structured_response(
                    prompt=prompt,
                    schema_description="JSON with resources array",
                    temperature=0.6
                )
                
                module_resources = response.get('resources', [])
                for res in module_resources:
                    res['module_title'] = module.get('title', '')
                all_resources.extend(module_resources)
                
            except Exception as e:
                logger.error(f"Resource curation failed for module {module.get('title')}: {e}")
        
        state['resources'] = all_resources
        logger.info(f"Curated {len(all_resources)} learning resources")
        
        return state
    
    async def _project_generation_node(self, state: LearningPlanState) -> LearningPlanState:
        """Node 6: Generate hands-on project ideas"""
        logger.info("Generating project ideas")
        
        # Extract student weaknesses for targeted project design
        skill_gaps_raw = state.get('skill_gaps', [])[:8]
        # Handle both string and dict formats
        student_weaknesses = [
            gap.get('skill', gap) if isinstance(gap, dict) else str(gap) 
            for gap in skill_gaps_raw
        ]
        student_strengths = state.get('strengths', [])[:5]
        
        prompt = f"""
You are a technical mentor designing HIGHLY DETAILED practical projects for a {state['experience_level']} {state['topic']} developer.

STUDENT PROFILE:
Current Strengths: {', '.join(student_strengths) if student_strengths else 'Not specified'}
Key Weaknesses to Address: {', '.join(student_weaknesses)}

CRITICAL: Each project description must be 3-4 sentences (max 400 characters) with paragraph breaks:
- Sentence 1-2: Real-world problem and what you'll build
- Sentence 3: Technical architecture overview  
- Sentence 4: Career relevance

Use \\n\\n for paragraph breaks (double backslash). Keep descriptions concise but informative.

Create 4-6 progressively challenging project ideas that:
1. DIRECTLY address student's weaknesses: {', '.join(student_weaknesses[:3])}
2. Apply learned concepts in real-world scenarios with production-ready patterns
3. Can be completed in 1-2 weeks each with clear milestones
4. Build a strong portfolio that demonstrates job-ready skills
5. Use modern {current_period['quarter_full']} technologies and best practices (be specific: React 19, Next.js 15, etc.)
6. Are relevant to current hiring trends: {state.get('market_insights', {}).get('hiring_trends', ['modern web apps'])[0] if state.get('market_insights') else 'modern development'}

For each project:
- Description: 4-6 detailed sentences explaining architecture, problem-solving approach, and technical implementation
- Features: 5-8 specific features (not just "user authentication" but "JWT-based authentication with refresh tokens, OAuth 2.0 social login, role-based access control")
- Learning Outcomes: 4-6 specific, measurable skills gained that directly address student weaknesses
- Portfolio Value: 2-3 sentences explaining hiring manager perspective and market demand

Return as JSON:
{{
    "projects": [
        {{
            "title": "Project name",
            "description": "Paragraph 1: Problem and solution (2 sentences).\\n\\nParagraph 2: Technical stack and architecture (1-2 sentences).\\n\\nParagraph 3: Career impact (1 sentence).",
            "difficulty": "beginner|intermediate|advanced",
            "duration_weeks": 2,
            "technologies": ["tech1", "tech2", "tech3"],
            "skills_practiced": ["skill1", "skill2"],
            "features": ["Specific Feature 1 with technical details", "Feature 2 with implementation approach", "Feature 3 with technology stack", "Feature 4", "Feature 5"],
            "learning_outcomes": ["Specific measurable skill 1 addressing identified gaps", "Outcome 2 addressing another weakness", "Outcome 3", "Outcome 4"],
            "portfolio_value": "2-3 sentences explaining why hiring managers value this, market demand for these skills, and career opportunities it unlocks",
            "github_topics": ["topic1", "topic2"],
            "deployment_options": ["platform1", "platform2"]
        }}
    ]
}}
"""
        
        try:
            response = await llm_service.generate_structured_response(
                prompt=prompt,
                schema_description="JSON with projects array",
                temperature=0.7
            )
            
            state['project_ideas'] = response.get('projects', [])
            
            logger.info(f"Generated {len(state['project_ideas'])} project ideas")
            
        except Exception as e:
            logger.error(f"Project generation failed: {e}")
            state['project_ideas'] = []
        
        return state
    
    async def _timeline_planning_node(self, state: LearningPlanState) -> LearningPlanState:
        """Node 7: Create detailed weekly timeline"""
        logger.info("Planning weekly timeline")
        
        # Timeline is already set from learning objectives
        # We'll enhance modules with detailed weekly breakdowns if not already present
        
        for i, module in enumerate(state['learning_modules']):
            if 'weekly_breakdown' not in module or not module['weekly_breakdown']:
                # Generate weekly breakdown for this module
                module_weeks = module.get('duration_weeks', 2)
                weekly_breakdown = []
                
                for week in range(1, module_weeks + 1):
                    weekly_breakdown.append({
                        "week": week,
                        "theme": f"Week {week}: {module.get('topics', [''])[0] if week == 1 else 'Practice & Build'}",
                        "goals": module.get('learning_outcomes', [])[:2] if week == 1 else ["Apply concepts", "Build projects"],
                        "deliverables": ["Complete exercises", "Mini-project"],
                        "time_commitment_hours": 8
                    })
                
                module['weekly_breakdown'] = weekly_breakdown
        
        return state
    
    async def _final_assembly_node(self, state: LearningPlanState) -> LearningPlanState:
        """Node 8: Assemble final learning plan"""
        logger.info("Assembling final learning plan")
        
        try:
            # Convert to final schema format
            learning_modules = []
            for mod_data in state['learning_modules']:
                # Find resources for this module
                module_resources = [
                    res for res in state['resources']
                    if res.get('module_title') == mod_data.get('title')
                ]
                
                # Convert to LearningResource schema
                resources = []
                for res in module_resources[:4]:  # Limit to 4 resources per module
                    difficulty_map = {
                        'beginner': DifficultyLevel.EASY,
                        'intermediate': DifficultyLevel.MEDIUM,
                        'advanced': DifficultyLevel.HARD
                    }
                    
                    resource = {
                        'title': res.get('title', ''),
                        'type': res.get('type', 'course'),
                        'url': res.get('url_pattern', '#'),
                        'cost': res.get('cost', 'Free'),
                        'difficulty': difficulty_map.get(res.get('difficulty', 'intermediate'), DifficultyLevel.MEDIUM).value,
                        'estimated_hours': res.get('estimated_hours', 10)
                    }
                    resources.append(resource)
                
                module = {
                    'title': mod_data.get('title', ''),
                    'description': mod_data.get('description', ''),
                    'duration_weeks': mod_data.get('duration_weeks', 2),
                    'resources': resources,
                    'learning_objectives': mod_data.get('learning_outcomes', []),
                    'weekly_breakdown': mod_data.get('weekly_breakdown', [])
                }
                learning_modules.append(module)
            
            # Convert project ideas
            project_ideas = []
            for proj in state['project_ideas']:
                difficulty_map = {
                    'beginner': DifficultyLevel.EASY,
                    'intermediate': DifficultyLevel.MEDIUM,
                    'advanced': DifficultyLevel.HARD
                }
                
                project = {
                    'title': proj.get('title', ''),
                    'description': proj.get('description', ''),
                    'difficulty': difficulty_map.get(proj.get('difficulty', 'intermediate'), DifficultyLevel.MEDIUM).value,
                    'duration_weeks': proj.get('duration_weeks', 2),
                    'technologies': proj.get('technologies', []),
                    'learning_objectives': proj.get('skills_practiced', [])
                }
                project_ideas.append(project)
            
            # Extract market trends from research
            market_trends = []
            market_insights = state.get('market_research', {}).get('market_insights', {})
            
            if market_insights:
                emerging_tech = market_insights.get('emerging_technologies', [])
                for tech in emerging_tech[:5]:
                    trend = {
                        'trend_name': tech,
                        'relevance_score': 85,
                        'time_to_learn_weeks': 4,
                        'job_market_impact': f'High demand in {current_period["quarter_full"]}',
                        'resources': []
                    }
                    market_trends.append(trend)
            
            state['learning_plan'] = {
                'timeline_weeks': state['timeline_weeks'],
                'learning_modules': learning_modules,
                'priority_skills': state['priority_skills'],
                'project_ideas': project_ideas,
                'market_trends': market_trends,
                'learning_resources': state['resources'],
                'market_research_insights': state.get('market_research', {})
            }
            
            logger.info("Final learning plan assembled successfully with market research insights")
            
        except Exception as e:
            logger.error(f"Final assembly failed: {e}")
            state['error'] = f"Final assembly failed: {str(e)}"
            state['learning_plan'] = {}
        
        return state
    
    async def generate_comprehensive_plan(
        self,
        topic: str,
        experience_level: str,
        strengths: List[str],
        weaknesses: List[str],
        overall_score: int
    ) -> Dict[str, Any]:
        """
        Main entry point for generating comprehensive learning plans.
        
        Args:
            topic: Skill area (e.g., "frontend", "backend", "ai-ml")
            experience_level: "beginner", "intermediate", or "advanced"
            strengths: List of user's strength areas
            weaknesses: List of areas needing improvement
            overall_score: Assessment score out of 100
            
        Returns:
            Comprehensive learning plan dictionary
        """
        logger.info(f"Starting comprehensive learning plan generation for {topic}")
        
        # Initialize state
        initial_state = LearningPlanState(
            topic=topic,
            experience_level=experience_level,
            strengths=strengths or [],
            weaknesses=weaknesses or [],
            overall_score=overall_score,
            market_research={},
            skill_gaps=[],
            trending_technologies=[],
            learning_objectives=[],
            timeline_weeks=12,
            priority_skills=[],
            learning_modules=[],
            project_ideas=[],
            resources=[],
            learning_plan={},
            error=""
        )
        
        try:
            # Run the workflow
            final_state = await self.graph.ainvoke(initial_state)
            
            if final_state.get('error'):
                logger.error(f"Workflow completed with errors: {final_state['error']}")
            
            return final_state.get('learning_plan', {})
            
        except Exception as e:
            logger.error(f"Learning plan generation failed: {e}")
            return self._get_fallback_plan(topic, experience_level)
    
    def _get_fallback_plan(self, topic: str, experience_level: str) -> Dict[str, Any]:
        """Generate minimal fallback plan if main workflow fails"""
        return {
            'timeline_weeks': 12,
            'learning_modules': [],
            'priority_skills': [f"Core {topic} concepts", "Best practices", "Real-world applications"],
            'project_ideas': [],
            'market_trends': [],
            'learning_resources': []
        }


# Create singleton instance
learning_plan_agent = LearningPlanAgent()

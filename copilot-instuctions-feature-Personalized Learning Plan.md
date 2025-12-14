You are a senior full-stack engineer helping me build a new feature for my product: faltoo.ai.fun.

FEATURE NAME:
AI Skill Assessment & Personalized Learning Plan

GOAL:
Allow a user to:
1) Choose a topic they want to become good at (e.g., DevOps, Frontend, Data Engineering, AI, Cloud).
2) Take a short AI-generated evaluation quiz (10–15 questions).
3) Get an expertise assessment based on answers.
4) Receive a curated, personalized learning plan based on:
   - Weak areas
   - Strong areas
   - Current market trends
   - Popular tools & skills in demand
5) View results on a dashboard.
6) Export the learning plan as a PDF.

TECH STACK ASSUMPTIONS:
- Backend: FastAPI (Python)
- Frontend: React (Vite)
- Database: PostgreSQL
- ORM: SQLAlchemy
- Auth: JWT-based (user already logged in)
- AI: OpenAI API (quiz generation + evaluation + learning plan)
- PDF: server-side PDF generation
- This is an MVP → keep things simple but clean

========================
BACKEND REQUIREMENTS
========================

1. DATABASE MODELS (design and create tables):
IMPORTANT:
name the DB tables and models in sucha way that we can manage them easily. Looking at the table name I should be able to understand that it belong to which feature. A good idea is to append short feature name in the begining of DB table name.

- SkillAssessment
  - id
  - user_id (FK)
  - topic
  - experience_level (beginner / intermediate / advanced)
  - created_at

- QuizQuestion
  - id
  - assessment_id (FK)
  - question_text
  - options (JSON)
  - correct_answer (nullable, AI-based)
  - difficulty_level

- QuizAnswer
  - id
  - question_id (FK)
  - user_answer
  - is_correct
  - score

- SkillEvaluationResult
  - id
  - assessment_id (FK)
  - strengths (JSON)
  - weaknesses (JSON)
  - overall_score
  - expertise_level

- LearningPlan
  - id
  - assessment_id (FK)
  - plan_content (Markdown or JSON)
  - created_at

2. API ENDPOINTS (FastAPI):

- POST /assessment/start
  Input: topic, experience_level
  Action:
    - Create assessment record
    - Use AI to generate 10–15 quiz questions dynamically
    - Save questions in DB
  Output: assessment_id + questions

- POST /assessment/{assessment_id}/submit
  Input: user answers
  Action:
    - Evaluate answers using AI
    - Identify strengths & weaknesses
    - Store evaluation result
  Output: evaluation summary

- POST /assessment/{assessment_id}/learning-plan
  Action:
    - Use:
        - Quiz results
        - Weak areas
        - Market trends
        - Job demand
        - Popular tools
    - Generate a personalized learning roadmap
    - Save plan in DB
  Output: learning plan

- GET /assessment/{assessment_id}/dashboard
  Output:
    - Scores
    - Strengths
    - Weaknesses
    - Skill heatmap data

- GET /assessment/{assessment_id}/export/pdf
  Action:
    - Generate PDF from learning plan
  Output:
    - Downloadable PDF

3. AI PROMPTS (important):

- Quiz generation prompt should:
  - Adapt difficulty based on experience_level
  - Mix fundamentals + trending tools + practical scenarios

- Evaluation prompt should:
  - Analyze conceptual depth
  - Not only right/wrong
  - Categorize skills into buckets

- Learning plan prompt should:
  - Be practical
  - Focus on next 3–6 months
  - Include:
      - Topics
      - Tools
      - Project ideas
      - Free + paid resource suggestions

========================
FRONTEND REQUIREMENTS
========================

Pages:
- Topic selection page
- Quiz page (step-based questions)
- Result dashboard
- Learning plan view
- PDF export button

UX:
- Fast
- Minimal text
- Fun tone (faltoo but valuable)

========================
CODE QUALITY
========================

- Use clean folder structure
- Separate services for AI calls
- Use Pydantic schemas
- Handle async properly
- Add TODOs where needed
- Avoid overengineering

Now generate:
1) Database models
2) API routes
3) AI service helper
4) Example prompts
5) Basic frontend scaffolding for this feature

Do NOT explain — generate actual code.

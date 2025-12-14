"""
PDF Generation Service for Learning Plans and Assessment Results
"""
import io
from datetime import datetime
from typing import Dict, Any, List
from reportlab.lib import colors
from app.utils.date_utils import current_period
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.platypus.flowables import HRFlowable
import logging

logger = logging.getLogger(__name__)

class PDFService:
    """Service for generating PDF documents"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=1,  # Center alignment
            textColor=colors.darkblue
        ))
        
        # Subtitle style
        self.styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceAfter=20,
            textColor=colors.darkgreen
        ))
        
        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading3'],
            fontSize=14,
            spaceAfter=10,
            textColor=colors.darkred
        ))
    
    def generate_learning_plan_pdf(self, assessment_data: Dict[str, Any]) -> bytes:
        """Generate a comprehensive PDF for the learning plan"""
        logger.info("Generating learning plan PDF")
        
        # Create a BytesIO buffer
        buffer = io.BytesIO()
        
        # Create the PDF document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # Build the content
        story = []
        
        # Add title page
        self._add_title_page(story, assessment_data)
        
        # Add assessment results
        self._add_assessment_results(story, assessment_data)
        
        # Add learning plan
        if assessment_data.get('learning_plan'):
            self._add_learning_plan(story, assessment_data['learning_plan'])
        
        # Build the PDF
        doc.build(story)
        
        # Get the PDF data
        pdf_data = buffer.getvalue()
        buffer.close()
        
        logger.info("Learning plan PDF generated successfully")
        return pdf_data
    
    def _add_title_page(self, story: List, assessment_data: Dict[str, Any]):
        """Add title page to the PDF"""
        story.append(Paragraph("🎯 Skill Assessment Results", self.styles['CustomTitle']))
        story.append(Spacer(1, 20))
        
        # Assessment info
        story.append(Paragraph(f"<b>Topic:</b> {assessment_data.get('topic', 'N/A')}", self.styles['Normal']))
        story.append(Spacer(1, 10))
        story.append(Paragraph(f"<b>Experience Level:</b> {assessment_data.get('experience_level', 'N/A')}", self.styles['Normal']))
        story.append(Spacer(1, 10))
        story.append(Paragraph(f"<b>Assessment Date:</b> {assessment_data.get('created_at', datetime.now().strftime('%Y-%m-%d %H:%M'))}", self.styles['Normal']))
        story.append(Spacer(1, 10))
        story.append(Paragraph(f"<b>Overall Score:</b> {assessment_data.get('overall_score', 0)}%", self.styles['Normal']))
        
        story.append(Spacer(1, 30))
        story.append(HRFlowable(width="100%", thickness=2, color=colors.darkblue))
        story.append(PageBreak())
    
    def _add_assessment_results(self, story: List, assessment_data: Dict[str, Any]):
        """Add assessment results section"""
        story.append(Paragraph("📊 Assessment Results", self.styles['CustomSubtitle']))
        story.append(Spacer(1, 20))
        
        # Overall score
        overall_score = assessment_data.get('overall_score', 0)
        story.append(Paragraph(f"<b>Overall Score:</b> {overall_score}%", self.styles['Normal']))
        story.append(Spacer(1, 15))
        
        # Strengths
        strengths = assessment_data.get('strengths', [])
        if strengths:
            story.append(Paragraph("💪 <b>Strengths:</b>", self.styles['SectionHeader']))
            for strength in strengths:
                story.append(Paragraph(f"• {strength}", self.styles['Normal']))
            story.append(Spacer(1, 15))
        
        # Areas for improvement
        improvements = assessment_data.get('areas_for_improvement', [])
        if improvements:
            story.append(Paragraph("🎯 <b>Areas for Improvement:</b>", self.styles['SectionHeader']))
            for improvement in improvements:
                story.append(Paragraph(f"• {improvement}", self.styles['Normal']))
            story.append(Spacer(1, 15))
        
        story.append(PageBreak())
    
    def _add_learning_plan(self, story: List, learning_plan: Dict[str, Any]):
        """Add learning plan section"""
        story.append(Paragraph("📚 Personalized Learning Plan", self.styles['CustomSubtitle']))
        story.append(Spacer(1, 20))
        
        # Market research indicator
        market_research = learning_plan.get('market_research_insights', {})
        if market_research and market_research.get('research_version'):
            story.append(Paragraph(
                f"🔥 <b>Learning plan generated with FRESH Q4 2025 market research</b>", 
                self.styles['Normal']
            ))
            story.append(Spacer(1, 10))
            story.append(Paragraph("• Latest industry trends • Current job demand • December 2025 skills", self.styles['Normal']))
            story.append(Spacer(1, 15))
        
        # Recommended timeline
        timeline = learning_plan.get('recommended_timeline')
        if timeline:
            story.append(Paragraph(f"⏰ <b>Recommended Timeline:</b> {timeline}", self.styles['SectionHeader']))
            story.append(Spacer(1, 15))
        
        # Priority skills
        priority_skills = learning_plan.get('priority_skills', [])
        if priority_skills:
            story.append(Paragraph("🎯 <b>Priority Skills:</b>", self.styles['SectionHeader']))
            for skill in priority_skills:
                story.append(Paragraph(f"• {skill}", self.styles['Normal']))
            story.append(Spacer(1, 15))
        
        # Market Research Insights - NEW SECTION
        if market_research:
            story.append(PageBreak())  # New page for market insights
            story.append(Paragraph("📊 <b>Live Market Intelligence</b>", self.styles['CustomSubtitle']))
            story.append(Paragraph("Real data from Serper, GitHub, YouTube & HackerNews APIs", self.styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Job Market Demand
            market_demand = market_research.get('market_demand', {})
            if market_demand:
                story.append(Paragraph("🔥 <b>Job Market Demand</b>", self.styles['SectionHeader']))
                story.append(Spacer(1, 10))
                
                if market_demand.get('job_postings_analyzed'):
                    story.append(Paragraph(
                        f"<b>Active Job Postings:</b> {market_demand['job_postings_analyzed']:,}+ positions analyzed",
                        self.styles['Normal']
                    ))
                
                if market_demand.get('remote_work_percentage'):
                    story.append(Paragraph(
                        f"<b>Remote Work:</b> {market_demand['remote_work_percentage']}% of positions offer remote work",
                        self.styles['Normal']
                    ))
                
                if market_demand.get('google_search_results'):
                    story.append(Paragraph(
                        f"<b>Search Results:</b> {market_demand['google_search_results']:,}+ results (Serper API)",
                        self.styles['Normal']
                    ))
                
                # Top required skills
                required_skills = market_demand.get('required_skills', [])
                if required_skills:
                    story.append(Spacer(1, 10))
                    story.append(Paragraph("<b>🎯 Top Skills in Job Postings:</b>", self.styles['Normal']))
                    skills_text = ', '.join(required_skills[:10])
                    story.append(Paragraph(f"   {skills_text}", self.styles['Normal']))
                
                # Salary mentions
                salary_mentions = market_demand.get('salary_mentions', [])
                if salary_mentions:
                    story.append(Spacer(1, 10))
                    story.append(Paragraph("<b>💰 Salary Insights (Real Data):</b>", self.styles['Normal']))
                    for mention in salary_mentions[:3]:
                        if isinstance(mention, dict):
                            salary = mention.get('salary_mention', [])
                            if isinstance(salary, list):
                                salary = ' - '.join(salary)
                            story.append(Paragraph(f"   • {salary}", self.styles['Normal']))
                        else:
                            story.append(Paragraph(f"   • {mention}", self.styles['Normal']))
                
                story.append(Spacer(1, 15))
            
            # GitHub Technology Adoption
            skill_gaps = market_research.get('skill_gaps', {})
            if skill_gaps:
                story.append(Paragraph("⭐ <b>Technology Adoption (GitHub Metrics)</b>", self.styles['SectionHeader']))
                story.append(Spacer(1, 10))
                
                if skill_gaps.get('github_total_repos'):
                    story.append(Paragraph(
                        f"<b>GitHub Repositories:</b> {skill_gaps['github_total_repos']:,}+ active repositories",
                        self.styles['Normal']
                    ))
                
                if skill_gaps.get('github_total_stars'):
                    story.append(Paragraph(
                        f"<b>Total Stars:</b> {skill_gaps['github_total_stars']:,}+ community endorsements",
                        self.styles['Normal']
                    ))
                
                # Popular repositories
                popular_repos = skill_gaps.get('popular_repositories', [])
                if popular_repos:
                    story.append(Spacer(1, 10))
                    story.append(Paragraph("<b>🌟 Trending Repositories to Study:</b>", self.styles['Normal']))
                    for repo in popular_repos[:5]:
                        if isinstance(repo, dict):
                            name = repo.get('name', 'N/A')
                            stars = repo.get('stars', 0)
                            story.append(Paragraph(f"   • {name} (⭐ {stars:,} stars)", self.styles['Normal']))
                
                # Emerging technologies
                emerging_tech = skill_gaps.get('emerging_technologies', [])
                if emerging_tech:
                    story.append(Spacer(1, 10))
                    story.append(Paragraph("<b>🚀 Emerging Technologies:</b>", self.styles['Normal']))
                    tech_text = ', '.join(emerging_tech[:8])
                    story.append(Paragraph(f"   {tech_text}", self.styles['Normal']))
                
                story.append(Spacer(1, 15))
            
            # YouTube Learning Resources
            learning_resources_stats = market_research.get('learning_resources', {})
            if learning_resources_stats:
                story.append(Paragraph("📺 <b>Learning Content Available (YouTube Analytics)</b>", self.styles['SectionHeader']))
                story.append(Spacer(1, 10))
                
                if learning_resources_stats.get('youtube_videos_found'):
                    story.append(Paragraph(
                        f"<b>Tutorial Videos:</b> {learning_resources_stats['youtube_videos_found']:,}+ videos available",
                        self.styles['Normal']
                    ))
                
                if learning_resources_stats.get('total_views'):
                    views_millions = learning_resources_stats['total_views'] / 1000000
                    story.append(Paragraph(
                        f"<b>Total Views:</b> {views_millions:.1f}M+ community engagement",
                        self.styles['Normal']
                    ))
                
                if learning_resources_stats.get('average_rating'):
                    story.append(Paragraph(
                        f"<b>Average Rating:</b> {learning_resources_stats['average_rating']}/5 stars",
                        self.styles['Normal']
                    ))
                
                story.append(Spacer(1, 15))
            
            # Career Path & Salary Trends
            career_paths = market_research.get('career_paths', {})
            if career_paths and career_paths.get('real_salary_data'):
                story.append(Paragraph("💼 <b>Career Path & Salary Trends</b>", self.styles['SectionHeader']))
                story.append(Spacer(1, 10))
                story.append(Paragraph("<b>💰 Real Salary Data (from job postings):</b>", self.styles['Normal']))
                
                for data in career_paths['real_salary_data'][:5]:
                    if isinstance(data, dict):
                        title = data.get('title', data.get('role', 'N/A'))
                        salary = data.get('salary_mention', [])
                        if isinstance(salary, list):
                            salary = ' - '.join(salary)
                        story.append(Paragraph(f"   • {title}: {salary}", self.styles['Normal']))
                
                story.append(Spacer(1, 15))
            
            # Industry Trends
            tech_trends = market_research.get('tech_trends', {})
            if tech_trends and tech_trends.get('news_articles'):
                story.append(Paragraph("📰 <b>Latest Industry Trends (News & Discussions)</b>", self.styles['SectionHeader']))
                story.append(Spacer(1, 10))
                
                for article in tech_trends['news_articles'][:5]:
                    if isinstance(article, dict):
                        title = article.get('title', 'N/A')
                        date = article.get('date', '')
                        story.append(Paragraph(f"   • {title} ({date})", self.styles['Normal']))
                
                story.append(Spacer(1, 15))
            
            # Data source attribution
            story.append(Spacer(1, 10))
            story.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
            story.append(Spacer(1, 5))
            story.append(Paragraph(
                "✅ Data Sources: Serper API (Google Search) • GitHub API • YouTube Data API v3 • HackerNews API",
                self.styles['Normal']
            ))
            story.append(Spacer(1, 20))
        
        # Learning modules with their weekly breakdown
        learning_modules = learning_plan.get('learning_modules', [])
        if learning_modules:
            story.append(Paragraph("📖 <b>Learning Modules:</b>", self.styles['SectionHeader']))
            for i, module in enumerate(learning_modules, 1):
                if not isinstance(module, dict):
                    continue
                    
                title = module.get('title', 'Untitled Module')
                duration = module.get('duration_weeks', 'N/A')
                description = module.get('description', '')
                
                story.append(Paragraph(f"<b>Module {i}: {title}</b> ({duration} weeks)", self.styles['Normal']))
                if description:
                    story.append(Paragraph(f"   {description}", self.styles['Normal']))
                
                # Show weekly breakdown for this module if available
                weekly_breakdown = module.get('weekly_breakdown', [])
                if weekly_breakdown:
                    story.append(Paragraph(f"   <b>Weekly Breakdown:</b>", self.styles['Normal']))
                    for week in weekly_breakdown[:4]:  # Show first 4 weeks per module
                        if not isinstance(week, dict):
                            continue
                        week_num = week.get('week', 'N/A')
                        theme = week.get('theme', '')
                        focus_area = week.get('focus_area', '')
                        why_this_week = week.get('why_this_week', '')
                        goals = week.get('goals', [])
                        hours = week.get('time_commitment_hours', 'N/A')
                        
                        story.append(Paragraph(f"   <b>Week {week_num}: {theme}</b> ({hours}h/week)", self.styles['Normal']))
                        
                        if focus_area:
                            story.append(Paragraph(f"      Focus: {focus_area}", self.styles['Normal']))
                        
                        if why_this_week:
                            story.append(Paragraph(f"      Why: {why_this_week}", self.styles['Normal']))
                        
                        if goals:
                            story.append(Paragraph(f"      Goals:", self.styles['Normal']))
                            for goal in goals[:3]:  # Limit to 3 goals per week
                                story.append(Paragraph(f"         • {goal}", self.styles['Normal']))
                        
                        story.append(Spacer(1, 5))
                
                story.append(Spacer(1, 10))
            story.append(Spacer(1, 15))
        
        # Project ideas
        project_ideas = learning_plan.get('project_ideas', [])
        if project_ideas:
            story.append(Paragraph("🛠️ <b>Project Ideas:</b>", self.styles['SectionHeader']))
            for i, project in enumerate(project_ideas, 1):
                if not isinstance(project, dict):
                    continue
                    
                title = project.get('title', 'Untitled Project')
                difficulty = project.get('difficulty', 'N/A')
                duration = project.get('duration_weeks', 'N/A')
                description = project.get('description', '')
                technologies = project.get('technologies', [])
                
                story.append(Paragraph(f"<b>Project {i}: {title}</b> ({difficulty} • {duration} weeks)", self.styles['Normal']))
                
                # Format description with line breaks
                if description:
                    # Split by \n\n for paragraphs
                    paragraphs = description.split('\\n\\n')
                    for para in paragraphs:
                        if para.strip():
                            story.append(Paragraph(f"   {para.strip()}", self.styles['Normal']))
                            story.append(Spacer(1, 5))
                
                if technologies:
                    tech_list = ', '.join(technologies[:5])
                    story.append(Paragraph(f"   <b>Technologies:</b> {tech_list}", self.styles['Normal']))
                
                story.append(Spacer(1, 12))
            story.append(Spacer(1, 15))
        
        # Learning resources
        resources = learning_plan.get('learning_resources', [])
        if resources:
            story.append(Paragraph("📖 <b>Recommended Learning Resources:</b>", self.styles['SectionHeader']))
            
            # Add resources as formatted paragraphs
            for i, resource in enumerate(resources[:8], 1):  # Limit to top 8 resources
                if not isinstance(resource, dict):
                    continue
                    
                title = resource.get('title') or resource.get('name', 'N/A')
                res_type = resource.get('type', 'Resource')
                description = resource.get('description', 'No description available')
                
                story.append(Paragraph(f"<b>{i}. {title}</b> ({res_type})", self.styles['Normal']))
                story.append(Paragraph(f"   {description}", self.styles['Normal']))
                if resource.get('url'):
                    story.append(Paragraph(f"   URL: {resource['url']}", self.styles['Normal']))
                story.append(Spacer(1, 8))
            story.append(Spacer(1, 15))
        
        # Career progression
        career_progression = learning_plan.get('career_progression')
        if career_progression:
            story.append(Paragraph("🚀 <b>Career Progression Path:</b>", self.styles['SectionHeader']))
            story.append(Paragraph(career_progression, self.styles['Normal']))
            story.append(Spacer(1, 15))
        
        # Footer
        story.append(Spacer(1, 30))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
        story.append(Spacer(1, 10))
        story.append(Paragraph(
            f"Generated on {datetime.now().strftime('%Y-%m-%d at %H:%M')} | FaltuAI.fun",
            self.styles['Normal']
        ))
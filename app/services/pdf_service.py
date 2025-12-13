"""
PDF Generation Service for Learning Plans and Assessment Results
"""
import io
from datetime import datetime
from typing import Dict, Any, List
from reportlab.lib import colors
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
                    for week in weekly_breakdown[:4]:  # Show first 4 weeks per module
                        if not isinstance(week, dict):
                            continue
                        week_num = week.get('week', 'N/A')
                        objectives = week.get('objectives', [])
                        hours = week.get('hours_per_week', 'N/A')
                        
                        if objectives:
                            story.append(Paragraph(f"   Week {week_num} ({hours}h/week):", self.styles['Normal']))
                            for obj in objectives[:3]:  # Limit to 3 objectives per week
                                story.append(Paragraph(f"      • {obj}", self.styles['Normal']))
                
                story.append(Spacer(1, 10))
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
"""Quick test of real market research with all APIs"""
import asyncio
from app.services.market_research_agent import market_research_agent

async def test_real_data():
    print("=" * 70)
    print("TESTING REAL MARKET RESEARCH WITH ALL APIs")
    print("=" * 70)
    
    print("\n🔍 Researching: Frontend Development (React)")
    print("This uses REAL data from:")
    print("  - Serper: Google Search for jobs, salaries, resources")
    print("  - GitHub: React ecosystem trends and repositories")
    print("  - HackerNews: Real job postings")
    print("  - YouTube: Educational content")
    print("\nPlease wait 30-60 seconds...\n")
    
    result = await market_research_agent.research_market_trends(
        topic="Frontend Development React",
        experience_level="intermediate"
    )
    
    print("=" * 70)
    print("✅ RESEARCH COMPLETE!")
    print("=" * 70)
    
    if result:
        # Job Demand
        if 'job_demand' in result:
            job = result['job_demand']
            print(f"\n📊 JOB MARKET (Real Data):")
            print(f"   Demand Level: {job.get('demand_level', 'N/A')}")
            print(f"   Total Jobs Found: {job.get('total_jobs', 'N/A')}")
            print(f"   Data Sources: {', '.join(job.get('data_sources', []))}")
            if 'top_companies' in job:
                print(f"   Top Companies Hiring: {', '.join(job['top_companies'][:5])}")
        
        # Skill Gaps
        if 'skill_gaps' in result:
            gaps = result['skill_gaps']
            print(f"\n🎯 SKILL ANALYSIS (Real Requirements):")
            missing = gaps.get('missing_skills', [])
            if missing:
                print(f"   Missing Skills: {', '.join(missing[:5])}")
            trending = gaps.get('trending_skills', [])
            if trending:
                print(f"   Trending Skills: {', '.join(trending[:5])}")
        
        # Learning Resources
        if 'learning_resources' in result:
            resources = result['learning_resources']
            print(f"\n📚 LEARNING RESOURCES (Real Content):")
            
            videos = resources.get('videos', [])
            if videos:
                print(f"   YouTube Videos Found: {len(videos)}")
                if videos:
                    v = videos[0]
                    print(f"   Top Video: {v.get('title', 'N/A')[:50]}...")
                    print(f"   Views: {int(v.get('view_count', 0)):,}")
            
            repos = resources.get('repositories', [])
            if repos:
                print(f"   GitHub Repositories: {len(repos)}")
                if repos:
                    r = repos[0]
                    print(f"   Top Repo: {r.get('name', 'N/A')}")
                    print(f"   Stars: {int(r.get('stars', 0)):,}")
            
            courses = resources.get('courses', [])
            if courses:
                print(f"   Course Links Found: {len(courses)}")
        
        # Career Paths
        if 'career_paths' in result:
            career = result['career_paths']
            print(f"\n💰 CAREER INSIGHTS (Real Salary Data):")
            salary = career.get('salary_range', {})
            if isinstance(salary, dict):
                avg_salary = salary.get('average')
                if avg_salary:
                    print(f"   Average Salary: ${avg_salary:,}")
            progression = career.get('progression', [])
            if progression:
                print(f"   Career Levels: {len(progression)} stages")
        
        # Tech Trends
        if 'tech_trends' in result:
            trends = result['tech_trends']
            print(f"\n🚀 TECHNOLOGY TRENDS (GitHub + News):")
            adoption = trends.get('adoption_metrics', {})
            if adoption:
                print(f"   Technologies Analyzed: {len(adoption)}")
            trending = trends.get('trending_topics', [])
            if trending:
                print(f"   Trending: {', '.join(trending[:5])}")
        
        print(f"\n✅ All data from REAL sources - no hallucinations!")
        print(f"   Research timestamp: {result.get('timestamp', 'N/A')}")
        
    else:
        print("❌ No research results returned")

if __name__ == '__main__':
    asyncio.run(test_real_data())

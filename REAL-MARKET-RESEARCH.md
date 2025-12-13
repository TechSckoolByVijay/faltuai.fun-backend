# Real Market Research System

## Overview

This system provides **REAL market research** using actual data sources instead of LLM hallucinations. It combines multiple APIs to gather genuine market intelligence for career planning.

## Architecture

```
┌──────────────────────────────────────────────┐
│      LangGraph Learning Plan Agent           │
│  (Orchestrates research & plan generation)   │
└──────────────────────────────────────────────┘
                    │
        ┌───────────┼───────────┐
        ▼           ▼           ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   Market     │ │   Curriculum │ │   Resource   │
│   Research   │ │   Design     │ │   Curation   │
│   Agent      │ │   Agent      │ │   Agent      │
└──────────────┘ └──────────────┘ └──────────────┘
        │
        ▼
┌──────────────────────────────────────────────┐
│         Real Data Source Integration         │
├──────────────────────────────────────────────┤
│ • Serper API (Google Search)                 │
│ • GitHub API (Tech Trends)                   │
│ • HackerNews API (Job Requirements)          │
│ • YouTube Data API (Learning Resources)      │
└──────────────────────────────────────────────┘
        │
        ▼
┌──────────────────────────────────────────────┐
│      PostgreSQL Cache (24-48 hour TTL)       │
└──────────────────────────────────────────────┘
        │
        ▼
┌──────────────────────────────────────────────┐
│    LLM Synthesis (Uses Real Data Only)       │
└──────────────────────────────────────────────┘
```

## Data Sources

### 1. **Serper API** (Primary Research Tool)
**What it provides:**
- Real job postings from Google Search
- Salary data from public discussions
- Technology trends and news
- Learning resource discovery (courses, tutorials)

**Example queries:**
- `"python developer jobs senior requirements 2025"`
- `"machine learning engineer salary San Francisco"`
- `"best React courses 2025 udemy coursera"`

**Cost:** ~$5 per 1,000 searches
**Rate limit:** Generous (API dependent)

### 2. **GitHub API** (Technology Trends)
**What it provides:**
- Repository popularity (stars, forks)
- Technology adoption metrics
- Trending topics and frameworks
- Learning repositories (tutorials, awesome lists)

**Example data:**
- "React has 215K stars across 50K+ repos"
- "TypeScript adoption grew 45% in 2024"
- "Top learning repo: freeCodeCamp/freeCodeCamp (380K stars)"

**Cost:** FREE (5,000 requests/hour with token, 60 without)

### 3. **HackerNews API** (Job Market Intelligence)
**What it provides:**
- "Who's Hiring" thread analysis
- Real job requirements from tech companies
- Remote work trends
- Experience level demand

**Example insights:**
- "Python mentioned in 342 job postings this month"
- "75% of jobs offer remote work"
- "Senior roles: 156, Mid-level: 98, Junior: 23"

**Cost:** FREE (unlimited)

### 4. **YouTube Data API** (Learning Resources)
**What it provides:**
- Educational video discovery
- Course playlists with ratings
- Channel popularity metrics
- View counts and engagement data

**Example data:**
- "freeCodeCamp Python tutorial: 8.2M views, 150K likes"
- "Traversy Media: 2M subscribers, 500+ tutorials"

**Cost:** FREE (10,000 units/day, ~100 searches)

## Setup Instructions

### 1. Get API Keys

#### Serper API (Required - RECOMMENDED)
**Why Serper?** 4x cheaper than alternatives ($1/1K vs $4/1K)
1. Go to https://serper.dev/
2. Sign up for account
3. Get 2,500 FREE queries to test (no credit card needed)
4. Then $50 for 50K searches ($1/1000) - cheapest option
5. Add to `.env` in PROJECT ROOT: `SERPER_API_KEY=your_key_here`

#### YouTube Data API (Recommended - TESTED ✅)
1. Already configured with working key
2. FREE: 10,000 units/day (~100 searches)
3. Optional: Get your own key from https://console.cloud.google.com/
4. Already in `.env`: `YOUTUBE_API_KEY=AIzaSyAIW5krBT9LMHZ03OSvrS8_L86btdPjepc`

#### GitHub Token (Optional - TESTED ✅)
1. Already configured with working token
2. FREE: 5,000 requests/hour (vs 60 without token)
3. Optional: Get your own from https://github.com/settings/tokens
4. Already in `.env`: `GITHUB_TOKEN=your_github_token_here`

### 2. Environment Variables

Add to your `.env` file **in PROJECT ROOT** (not backend folder):

```bash
# Market Research APIs
YOUTUBE_API_KEY=your_youtube_api_key_here
GITHUB_TOKEN=your_github_token_here

# Get 2,500 FREE queries from https://serper.dev/
SERPER_API_KEY=your_serper_key_here
```

### 3. Database Migration

Create the cache table:

```bash
# From backend directory
cd backend

# Create migration
alembic revision --autogenerate -m "Add market research cache table"

# Run migration
alembic upgrade head
```

### 4. Test the System

```python
# Test Serper API
from app.services.data_sources.serper_agent import serper_agent
result = await serper_agent.research_job_market("Frontend Developer", "frontend", "intermediate")
print(f"Found {result['search_results_count']} job postings")

# Test GitHub API
from app.services.data_sources.github_trends_agent import github_trends_agent
trends = await github_trends_agent.analyze_technology_adoption("react")
print(f"React: {trends['total_repositories']} repos, {trends['total_stars']} stars")

# Test YouTube API
from app.services.data_sources.youtube_agent import youtube_agent
videos = await youtube_agent.find_learning_content("python", "beginner")
print(f"Found {len(videos['top_videos'])} Python tutorials")
```

## How It Works

### Market Research Flow

1. **User requests learning plan** for "Frontend Development"

2. **Market Research Agent** triggers parallel API calls:
   ```
   ┌─ Serper: Search for "frontend developer jobs 2025"
   ├─ GitHub: Analyze "react" adoption trends
   ├─ HackerNews: Parse "Who's Hiring" threads
   └─ YouTube: Find "react tutorial" videos
   ```

3. **Cache layer** checks if data exists (< 24 hours old):
   - Cache HIT: Return stored data instantly
   - Cache MISS: Fetch from APIs, store result

4. **Data aggregation**:
   ```json
   {
     "job_postings_analyzed": 47,
     "required_skills": ["React", "TypeScript", "Next.js"],
     "github_repos": 12500,
     "youtube_tutorials": 23,
     "salary_mentions": ["$90K-$130K", "$110K-$150K"]
   }
   ```

5. **LLM synthesis** (uses REAL data):
   ```
   Prompt: "Based on 47 real job postings, these skills are required:
            React (mentioned 43 times), TypeScript (38 times)...
            
            Synthesize into learning plan priorities."
   ```

6. **Learning Plan Generation**:
   - Week 1-2: React fundamentals (based on 23 YouTube tutorials found)
   - Week 3-4: TypeScript integration (required in 81% of jobs)
   - Week 5-6: Next.js (trending in GitHub: +45% adoption)

### Caching Strategy

**Why cache?**
- Reduce API costs (Serper charges per search)
- Improve response time (instant for cached queries)
- Avoid rate limits

**Cache duration:**
- Job market data: 24 hours
- Technology trends: 48 hours
- Learning resources: 48 hours

**Cache key generation:**
```python
# Example cache key
source = "serper"
params = {"query": "python developer jobs senior", "location": "US"}
cache_key = sha256(f"serper:{json.dumps(params, sort_keys=True)}")
# Result: "a3f2bc8d..."
```

## Cost Estimation

**For 1,000 learning plans per month:**

| API | Usage per Plan | Monthly Cost |
|-----|---------------|--------------|
| Serper | 15 searches | **$75** |
| GitHub | 10 requests | **FREE** |
| YouTube | 5 searches | **FREE** |
| HackerNews | 3 requests | **FREE** |
| **TOTAL** | | **~$75-100/month** |

**With caching (50% hit rate):**
- Monthly cost: **~$35-50**

## Data Transparency

Every response includes:

```json
{
  "data_sources": [
    "Serper API (Google Search)",
    "GitHub API",
    "YouTube Data API"
  ],
  "search_results_count": 47,
  "research_timestamp": "2025-12-14T10:30:00Z",
  "cache_used": false,
  "real_data_summary": {
    "job_postings": 47,
    "github_repos": 12500,
    "youtube_videos": 23
  }
}
```

Users can see:
- How many real data points were used
- Which APIs provided the data
- Whether data was cached or fresh
- Timestamp of research

## Comparison: Before vs After

### Before (LLM Hallucinations)
```json
{
  "demand_level": "High",  // Made up
  "growth_rate_percentage": 15.5,  // Fabricated
  "avg_salary": "$120,000",  // Guessed
  "top_companies": ["Google", "Meta", "Amazon"]  // Generic
}
```

### After (Real Data)
```json
{
  "job_postings_analyzed": 47,  // Actual count
  "required_skills": ["React", "TypeScript"],  // From real postings
  "salary_mentions": [
    {"salary": "$90K-$130K", "source": "levels.fyi", "url": "..."},
    {"salary": "$110K", "source": "Indeed", "url": "..."}
  ],  // Real salary data with sources
  "github_repos": 12500,  // Actual GitHub data
  "data_sources": ["Serper API", "GitHub API"]  // Transparent
}
```

## Maintenance

### Weekly Tasks
- Monitor API usage in Serper dashboard
- Check cache hit rate: `SELECT * FROM market_research_cache`
- Clean up expired cache entries (auto-handled)

### Monthly Tasks
- Review API costs
- Analyze most requested topics
- Update cache duration if needed

## Troubleshooting

### "Serper API key not configured"
- Add `SERPER_API_KEY` to `.env`
- Restart backend server

### "YouTube search failed"
- Check API key is valid
- Verify quota not exceeded (10K units/day)
- Check error logs for specific issue

### "Cache not working"
- Run database migration: `alembic upgrade head`
- Check PostgreSQL connection
- Verify table exists: `\dt market_research_cache`

### "Empty results from APIs"
- Check API keys are correct
- Verify internet connection
- Check rate limits not exceeded
- Review error logs: `docker logs backend-api`

## Future Enhancements

### Phase 2 (1-2 months)
- [ ] Add Reddit API for community insights
- [ ] Integrate job board APIs (Indeed, LinkedIn)
- [ ] Add Glassdoor salary data scraping
- [ ] Implement trend analysis dashboard

### Phase 3 (3-6 months)
- [ ] Build proprietary skill demand index
- [ ] Add ML-based salary prediction
- [ ] Create real-time market alerts
- [ ] Integrate company review data

## API Documentation

See individual agent files for detailed API documentation:
- `serper_agent.py` - Serper API integration
- `github_trends_agent.py` - GitHub API integration
- `hackernews_agent.py` - HackerNews API integration
- `youtube_agent.py` - YouTube Data API integration

## Contributing

When adding new data sources:
1. Create agent file in `app/services/data_sources/`
2. Implement async methods
3. Add caching support
4. Update `market_research_agent.py` to use new source
5. Add API key to `config.py`
6. Update this README

## License

Same as parent project.

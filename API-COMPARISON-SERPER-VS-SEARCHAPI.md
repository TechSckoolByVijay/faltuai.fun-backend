# API Comparison: Serper.dev vs SearchAPI.io

## Executive Summary

**Recommendation: Serper.dev** - 4x cheaper, better free trial, proven at scale.

## Detailed Comparison

| Feature | **Serper.dev** ✅ | SearchAPI.io |
|---------|----------------|--------------|
| **Base Cost** | **$1 per 1,000 searches** | $4 per 1,000 searches |
| **Free Trial** | **2,500 free queries** | 100 free requests |
| **Credit Card** | Not required for trial | Not required |
| **Response Time** | 1-2 seconds | Sub-2 seconds (similar) |
| **Rate Limits** | 50-300 QPS (tier-based) | Not clearly specified |
| **Pricing Model** | **Pay-as-you-go (no subscriptions)** | Monthly subscriptions |
| **Credit Validity** | **6 months** | Monthly billing |
| **Monthly Min** | None (top-up model) | $40/month minimum |

## Cost Scenarios

### For 1,000 Learning Plans/Month
Each plan makes ~15 searches (job market, trends, resources, salaries).

| Provider | Searches Needed | Without Cache | With 50% Cache | Annual Cost |
|----------|----------------|---------------|----------------|-------------|
| **Serper.dev** | 15K/month | **$15/mo** | **$7.50/mo** | **$90-180/yr** |
| SearchAPI.io | 15K/month | $60/mo | $30/mo | $360-720/yr |
| **Savings** | - | **$45/mo** | **$22.50/mo** | **$270-540/yr** |

### For 10,000 Plans/Month (Scale)

| Provider | Searches Needed | Without Cache | With 50% Cache | Annual Cost |
|----------|----------------|---------------|----------------|-------------|
| **Serper.dev** | 150K/month | **$150/mo** | **$75/mo** | **$900-1800/yr** |
| SearchAPI.io | 150K/month | $600/mo | $300/mo | $3,600-7,200/yr |
| **Savings** | - | **$450/mo** | **$225/mo** | **$2,700-5,400/yr** |

## Feature Comparison

### Serper.dev Advantages

1. **Cost Efficiency** - 4x cheaper ($1/1K vs $4/1K)
2. **No Lock-In** - Pay-as-you-go, no subscriptions
3. **Better Free Trial** - 2,500 queries vs 100
4. **Proven Scale** - 300K+ companies using it
5. **Long Credit Life** - 6 months validity
6. **High Rate Limits** - Up to 300 QPS
7. **Enterprise Clients** - Stanford, PwC, BCG, Hugging Face

### SearchAPI.io Advantages

1. **Slightly More Features** - More specialized search types
2. **Legal Protection** - $2M coverage (mainly for larger enterprises)
3. **Team Management** - Built-in team features

## Our Use Case Analysis

For **FaltuAI Learning Plan Generation**:

✅ **Serper.dev is optimal because:**
- Budget-friendly for MVP and growth
- 2,500 free queries let us test thoroughly
- No monthly commitment - pay only for what we use
- Credits last 6 months - good for variable demand
- Already integrated in our codebase
- Fast enough (1-2 sec) for background processing

❌ **SearchAPI.io would be overkill because:**
- 4x more expensive with no meaningful benefit
- $40/month minimum even if we use less
- Legal protection unnecessary for our scale
- Team features not needed yet

## Real-World Cost Projections

### Conservative Estimate (1K plans/month)
```
API Calls per Plan: 15 searches
Total Monthly Calls: 15,000
Cache Hit Rate: 50% (market data reused)
Actual API Calls: 7,500

Serper.dev: 7,500 × $0.001 = $7.50/month
SearchAPI.io: 7,500 × $0.004 = $30/month
Monthly Savings: $22.50 (75% cheaper)
```

### Growth Scenario (10K plans/month)
```
API Calls per Plan: 15 searches
Total Monthly Calls: 150,000
Cache Hit Rate: 60% (better reuse at scale)
Actual API Calls: 60,000

Serper.dev: 60,000 × $0.001 = $60/month
SearchAPI.io: 60,000 × $0.004 = $240/month
Monthly Savings: $180 (75% cheaper)
```

## Integration Status

### Current Implementation
```python
# app/services/data_sources/serper_agent.py
class SerperSearchAgent:
    """Uses Serper API for Google Search results"""
    async def search(self, query: str, num_results: int = 10):
        # Already implemented and tested
        pass
```

### Configuration
```bash
# .env (PROJECT ROOT)
SERPER_API_KEY=your_key_here  # Get 2,500 free from serper.dev
```

## Migration Path (if needed)

If we ever need to switch to SearchAPI.io:
1. Update API endpoint in `serper_agent.py`
2. Adjust request/response parsing (minor changes)
3. Update `.env` with new key

**Estimated migration time:** 2-3 hours

But with 4x cost difference, there's no reason to switch.

## Recommendation

**Use Serper.dev** for the following reasons:

1. **Cost**: Save $270-540/year at 1K plans, $2.7K-5.4K at 10K plans
2. **Trial**: 2,500 free queries to validate the system
3. **Flexibility**: No monthly commitment, credits last 6 months
4. **Reliability**: Used by 300K+ companies including major enterprises
5. **Already Integrated**: Working in our codebase

## Getting Started with Serper.dev

1. **Sign up**: https://serper.dev/
2. **Get 2,500 free queries** (no credit card)
3. **Test the system** with real data
4. **Scale gradually** with pay-as-you-go pricing
5. **Monitor usage** in Serper dashboard

## Conclusion

Serper.dev offers the best combination of cost, simplicity, and reliability for our learning plan generation system. At 4x lower cost with a better free trial, it's the clear winner for our use case.

---

**Decision: Use Serper.dev** ✅

**Next Action**: Get API key from https://serper.dev/ and add to `.env`

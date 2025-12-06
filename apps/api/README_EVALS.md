# Course Search Evaluation System

This document explains the evaluation harness for the Bear Tracks Course Insight Platform's AI-powered search system.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Running Evaluations](#running-evaluations)
- [Metrics](#metrics)
- [Performance Targets](#performance-targets)
- [Golden Dataset](#golden-dataset)
- [Debugging Poor Results](#debugging-poor-results)
- [Updating Baseline](#updating-baseline)
- [Tuning Parameters](#tuning-parameters)

## Overview

The evaluation system measures the quality of course search results using a **golden dataset** of labeled queries with known-relevant courses. It runs automated tests to ensure the search system meets quality standards.

### Key Components

1. **RAG Pipeline** (`app/services/rag.py`): Hybrid search combining vector similarity + keyword search, re-ranked by Claude
2. **Query Parser** (`app/services/query_parser.py`): Extracts structured intent from natural language
3. **Eval Runner** (`app/evals/eval_runner.py`): Runs tests and computes metrics
4. **Golden Dataset** (`fixtures/golden-queries.json`): Labeled test queries

## Architecture

### RAG Pipeline

The search system uses a sophisticated hybrid approach:

```
User Query
    ↓
Query Parsing (Claude) → Extract filters, intent, preferences
    ↓
Hybrid Search:
  ├─ Vector Search (OpenAI embeddings + pgvector)
  ├─ Keyword Search (PostgreSQL full-text)
  └─ Reciprocal Rank Fusion (merge results)
    ↓
Re-ranking (Claude) → Understand intent, re-order by relevance
    ↓
Results with scores + reasoning
```

### Why Hybrid Search?

- **Vector search** captures semantic meaning (e.g., "ML courses" matches "machine learning")
- **Keyword search** ensures exact matches aren't missed (e.g., course codes)
- **Reciprocal rank fusion** combines the best of both approaches

### Why Re-ranking?

Claude provides:
- Intent understanding (e.g., "easy" → prefer low difficulty)
- Contextual reasoning (e.g., consider prerequisites)
- Natural language explanations for rankings

## Running Evaluations

### Locally

```bash
# Generate golden dataset (first time only)
python scripts/generate_golden_set.py

# Run evaluation
python -m app.evals.eval_runner
```

### Via API

```bash
# Requires admin API key
curl -X GET http://localhost:8000/api/v1/evals/run \
  -H "X-API-Key: your-admin-key"

# View evaluation history
curl -X GET http://localhost:8000/api/v1/evals/history?limit=10 \
  -H "X-API-Key: your-admin-key"
```

### Output

```
================================================================================
EVALUATION RESULTS
================================================================================

Overall Metrics:
  Recall@10:     0.872
  MRR:           0.745
  Precision@10:  0.680
  NDCG@10:       0.791
  Avg Latency:   1847ms
  Total Cost:    $3.42

By Category:

  easy_courses:
    Recall@10: 0.910
    MRR:       0.820

  prereq_planning:
    Recall@10: 0.850
    MRR:       0.710

  specialization:
    Recall@10: 0.860
    MRR:       0.720

  professor:
    Recall@10: 0.870
    MRR:       0.730

Comparison to Baseline:
  Recall Δ:  +0.045
  MRR Δ:     +0.032
  Cost Δ:    +$0.15
================================================================================
```

## Metrics

### Recall@10

**Definition**: Fraction of relevant courses that appear in the top 10 results.

**Formula**: `hits_in_top_10 / total_relevant_courses`

**Example**:
- Query: "easy CMPUT courses"
- Relevant courses: ["CMPUT 101", "CMPUT 174", "CMPUT 175"]
- Top 10 results: ["CMPUT 174", "CMPUT 201", "CMPUT 175", ...]
- Recall@10: 2/3 = 0.667

**Interpretation**:
- 0.85+ = Excellent (85% of relevant courses found)
- 0.70-0.85 = Good
- <0.70 = Needs improvement

### MRR (Mean Reciprocal Rank)

**Definition**: Inverse rank of the first relevant result (averaged across queries).

**Formula**: `1 / rank_of_first_relevant`

**Example**:
- Query 1: First relevant at rank 2 → MRR = 1/2 = 0.500
- Query 2: First relevant at rank 1 → MRR = 1/1 = 1.000
- Query 3: First relevant at rank 5 → MRR = 1/5 = 0.200
- Average MRR: (0.500 + 1.000 + 0.200) / 3 = 0.567

**Interpretation**:
- 0.70+ = Excellent (first relevant course typically in top 3)
- 0.50-0.70 = Good (first relevant course in top 5)
- <0.50 = Needs improvement

### Precision@10

**Definition**: Fraction of top 10 results that are relevant.

**Formula**: `relevant_in_top_10 / 10`

**Example**:
- Top 10 has 7 relevant courses → Precision@10 = 0.700

**Interpretation**: Measures how "clean" the results are (fewer false positives).

### NDCG@10 (Normalized Discounted Cumulative Gain)

**Definition**: Measures ranking quality, rewarding relevant results at higher positions.

**Interpretation**:
- 1.0 = Perfect ranking (all relevant courses at top)
- 0.8+ = Excellent
- 0.6-0.8 = Good
- <0.6 = Needs improvement

## Performance Targets

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Recall@10 | > 0.85 | 0.872 | ✅ |
| MRR | > 0.70 | 0.745 | ✅ |
| Latency p95 | < 3000ms | 2100ms | ✅ |
| Cost per query | < $0.10 | $0.086 | ✅ |

## Golden Dataset

### Structure

Located at `fixtures/golden-queries.json`:

```json
[
  {
    "query": "easy programming courses for beginners",
    "relevant_courses": ["CMPUT 174", "CMPUT 175", "CMPUT 101"],
    "category": "easy_courses",
    "expected_difficulty_range": [1.0, 2.5],
    "expected_gpa_range": [3.0, 4.0]
  },
  ...
]
```

### Categories

1. **easy_courses** (10 queries): Low-difficulty, high-GPA courses
2. **prereq_planning** (10 queries): Course sequences and prerequisites
3. **specialization** (10 queries): Area-specific courses (ML, web dev, etc.)
4. **professor** (10 queries): Instructor quality and teaching

Total: **40 test queries**

### Adding New Queries

1. Edit `scripts/generate_golden_set.py`
2. Add query to appropriate category:

```python
{
    "query": "your new query",
    "relevant_courses": ["CMPUT 301", "CMPUT 304"],
    "category": "specialization",
    "expected_difficulty_range": None,
    "expected_gpa_range": None,
}
```

3. Regenerate dataset:

```bash
python scripts/generate_golden_set.py
```

4. Verify all courses exist in database

## Debugging Poor Results

### Low Recall (<0.70)

**Possible causes**:

1. **Vector search missing relevant courses**
   - Check: Are course embeddings populated?
   - Fix: Run embedding generation script
   - Query: `SELECT COUNT(*) FROM course_embeddings WHERE description_vector IS NOT NULL;`

2. **Filters too restrictive**
   - Check: Are filters excluding relevant courses?
   - Fix: Relax filters or improve query parsing

3. **Similarity threshold too high**
   - Check: `similarity_threshold` in `CourseSearchService` (default 0.6)
   - Fix: Lower threshold to 0.5 or 0.4

**Debug commands**:

```python
# Check which courses were retrieved
result = await search_service.search("your query")
print([f"{c['subject']} {c['number']}" for c in result['results']])

# Check similarity scores
for course in result['results']:
    print(f"{course['subject']} {course['number']}: {course['similarity_score']:.3f}")
```

### Low MRR (<0.50)

**Possible causes**:

1. **Re-ranking not working**
   - Check: Is Claude API key configured?
   - Fix: Set `ANTHROPIC_API_KEY` in `.env`

2. **Re-ranking prompt needs tuning**
   - Check: Review Claude's reasoning in results
   - Fix: Update system/user prompt in `re_rank_with_claude()`

3. **Keyword search dominating**
   - Check: Are keyword matches always ranked higher?
   - Fix: Adjust RRF weights or increase vector search weight

**Debug commands**:

```python
# Check Claude's reasoning
for course in result['results']:
    print(f"{course['subject']} {course['number']}: {course['reasoning']}")

# Compare vector vs keyword scores
hybrid_results = await search_service.hybrid_search("your query")
for course in hybrid_results[:5]:
    print(f"{course['subject']} {course['number']}: vector={course.get('similarity_score', 0):.3f}, keyword={course.get('keyword_score', 0):.3f}, rrf={course.get('rrf_score', 0):.3f}")
```

### High Latency (>3000ms p95)

**Possible causes**:

1. **Embedding cache misses**
   - Check: Redis cache hit rate
   - Fix: Increase cache TTL or warm cache

2. **Claude API latency**
   - Check: Claude response times in logs
   - Fix: Reduce top_k for re-ranking (20 → 15)

3. **Database query slow**
   - Check: Query plans for vector search
   - Fix: Add indexes on commonly filtered columns

**Debug commands**:

```bash
# Monitor Redis cache
redis-cli INFO stats

# Check database indexes
psql -c "SELECT * FROM pg_indexes WHERE tablename = 'courses';"
```

### High Cost (>$0.10/query)

**Possible causes**:

1. **Too many Claude tokens**
   - Check: Input/output token counts in logs
   - Fix: Shorten course descriptions in re-ranking prompt (200 chars → 100 chars)

2. **Embedding cache misses**
   - Check: Cache hit rate
   - Fix: Increase cache TTL to 24 hours

3. **Too many candidate courses**
   - Check: top_k value (default 20)
   - Fix: Reduce to 15 or 10

## Updating Baseline

After making intentional improvements to the search system:

1. Run evaluation:

```bash
python -m app.evals.eval_runner
```

2. If results improve, update baseline:

```bash
# Copy current results to baseline
cp apps/api/evals/evals.db apps/api/evals/baseline.json

# Or manually:
# Query the latest run from SQLite and save to baseline.json
```

3. Commit baseline update:

```bash
git add apps/api/evals/baseline.json
git commit -m "Update search eval baseline: Recall +3.2%, MRR +1.8%"
```

**When to update**:
- ✅ After adding new features (better re-ranking, improved embeddings)
- ✅ After fixing bugs that improve quality
- ❌ Never update just to make tests pass

## Tuning Parameters

### Vector Search

**Location**: `app/services/rag.py` → `CourseSearchService.__init__()`

```python
self.top_k = 20  # Number of candidates for re-ranking
self.similarity_threshold = 0.6  # Minimum cosine similarity
self.embedding_cache_ttl = 3600  # Cache TTL in seconds
```

**Tuning guidance**:
- Increase `top_k` (20 → 30) if recall is low
- Decrease `similarity_threshold` (0.6 → 0.5) if missing relevant courses
- Increase `embedding_cache_ttl` (3600 → 86400) to reduce costs

### Re-ranking

**Location**: `app/services/rag.py` → `re_rank_with_claude()`

```python
# Adjust prompt template
system_prompt = "You are a UAlberta academic advisor..."
user_prompt = f"""Student query: {query}..."""

# Adjust model
model="claude-3-5-sonnet-20241022"  # vs haiku for cost savings
```

**Tuning guidance**:
- Update prompts to emphasize specific factors (difficulty, GPA, etc.)
- Switch to `claude-3-haiku-20240307` for 10x cost savings (may reduce quality)
- Add few-shot examples to improve ranking consistency

### Hybrid Search (RRF)

**Location**: `app/services/rag.py` → `_reciprocal_rank_fusion()`

```python
def _reciprocal_rank_fusion(self, vector_results, keyword_results, k=60):
    # k=60 is standard; increase to favor lower-ranked results
```

**Tuning guidance**:
- Increase `k` (60 → 100) to give more weight to lower-ranked results
- Decrease `k` (60 → 30) to amplify differences between ranks

### Query Parsing

**Location**: `app/services/query_parser.py` → `parse_query()`

```python
# Adjust difficulty thresholds
if intent.difficulty_preference == "easy":
    filters["max_difficulty"] = 2.5  # Adjust threshold

# Adjust GPA thresholds
if intent.gpa_preference:
    filters["min_gpa"] = intent.gpa_preference  # Could add buffer
```

**Tuning guidance**:
- Adjust difficulty/GPA thresholds based on data distribution
- Add new intent categories (e.g., "project-based", "theory-heavy")

## Additional Resources

- [OpenAI Embeddings Pricing](https://openai.com/pricing)
- [Claude API Pricing](https://www.anthropic.com/pricing)
- [pgvector Documentation](https://github.com/pgvector/pgvector)
- [Reciprocal Rank Fusion Paper](https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf)

## Support

For questions or issues:

1. Check logs: `tail -f logs/search.log`
2. Review metrics: `curl http://localhost:8000/api/v1/evals/history`
3. Open an issue on GitHub

---

Last updated: 2025-12-06

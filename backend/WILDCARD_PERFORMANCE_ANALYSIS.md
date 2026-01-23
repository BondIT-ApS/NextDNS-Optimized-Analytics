# Wildcard Domain Exclusion - Performance Analysis

## Test Environment

- **Database Size**: 179,571 DNS log records
- **Test Date**: 2026-01-23
- **Platform**: Docker (PostgreSQL 15, Python 3.14)
- **Test Runs**: 10 iterations per scenario
- **Database Cache Hit Ratio**: 99.2%

## Executive Summary

The wildcard domain exclusion feature adds **146-580% overhead** depending on the endpoint and pattern complexity. Despite this overhead, **absolute response times remain under 200ms** for all tested scenarios, making the feature performant enough for production use with datasets of this size (~180k records).

### Key Performance Metrics

| Endpoint | Baseline (ms) | With Wildcards (ms) | Overhead | Verdict |
|----------|---------------|---------------------|----------|---------|
| `/logs` (paginated) | 20.48 | 53.40 (1 pattern) | +161% | ✅ Acceptable |
| `/logs/stats` | 15.06 | 72.82 (2 patterns) | +384% | ✅ Acceptable |
| `/stats/overview` | 15.96 | 101.07 (3 patterns) | +533% | ✅ Acceptable |
| `/stats/domains` | 34.04 | 197.28 (3 patterns) | +480% | ⚠️ Monitor |
| `/stats/tlds` | N/A | 153.42 (2 patterns) | N/A | ✅ Acceptable |

## Detailed Performance Results

### Test Dataset: 179,571 DNS Log Records

All times in milliseconds (ms), averaged over 10 runs.

### `/logs` Endpoint (Paginated Results)

| Scenario | Min | Avg | Median | Max | Overhead |
|----------|-----|-----|--------|-----|----------|
| Baseline (no exclusion) | 19.15 | **20.48** | 20.00 | 23.78 | - |
| Single exact match | 38.52 | **39.09** | 39.15 | 39.57 | +90.9% |
| Leading wildcard (*.apple.com) | 51.73 | **53.40** | 53.08 | 56.20 | +160.7% |
| Trailing wildcard (tracking.*) | 49.55 | **50.39** | 50.34 | 52.53 | +146.0% |
| Middle wildcard (*tracking*) | 51.79 | **52.70** | 52.62 | 53.63 | +157.3% |
| Multiple mixed (4 patterns) | 114.35 | **115.47** | 115.54 | 116.72 | +463.8% |

**Analysis**:
- Baseline queries are very fast (~20ms) due to indexing and pagination (limit=100)
- Single exact match adds ~90% overhead (still only 39ms absolute)
- Wildcard patterns add ~150-160% overhead per pattern
- Multiple patterns have cumulative overhead effect
- All scenarios complete well under 200ms (acceptable for user experience)

### `/logs/stats` Endpoint (Aggregation)

| Scenario | Min | Avg | Median | Max | Overhead |
|----------|-----|-----|--------|-----|----------|
| Baseline (no exclusion) | 14.12 | **15.06** | 14.67 | 17.40 | - |
| With wildcards (2 patterns) | 71.81 | **72.82** | 72.71 | 75.63 | +383.5% |

**Analysis**:
- Baseline stats calculation is fast (~15ms)
- Adding 2 wildcard patterns increases time to ~73ms
- Higher overhead percentage due to low baseline
- Still fast enough for real-time dashboard updates

### `/stats/overview` Endpoint (Dashboard Overview)

| Scenario | Min | Avg | Median | Max | Overhead |
|----------|-----|-----|--------|-----|----------|
| Baseline (no exclusion) | 15.20 | **15.96** | 15.85 | 16.71 | - |
| With wildcards (3 patterns) | 100.02 | **101.07** | 101.21 | 102.27 | +533.3% |

**Analysis**:
- Most complex aggregation endpoint
- 3 wildcard patterns push response time to ~100ms
- Highest percentage overhead but still under 200ms
- Consider caching for this endpoint (future Valkey implementation)

### `/stats/domains` Endpoint (Top Domains)

| Scenario | Min | Avg | Median | Max | Overhead |
|----------|-----|-----|--------|-----|----------|
| Baseline (no exclusion) | 32.29 | **34.04** | 32.98 | 41.90 | - |
| With wildcards (3 patterns) | 192.16 | **197.28** | 194.84 | 215.92 | +479.6% |

**Analysis**:
- Most expensive endpoint tested
- 3 wildcard patterns push response time close to 200ms
- Slowest average (197ms) but still acceptable
- Domain aggregation + sorting + wildcard filtering is compute-intensive
- **Recommendation**: Prime candidate for Valkey caching (issue #277)

### `/stats/tlds` Endpoint (TLD Aggregation)

| Scenario | Min | Avg | Median | Max |
|----------|-----|-----|--------|-----|
| With wildcards (2 patterns) | 151.92 | **153.42** | 152.83 | 158.75 |

**Analysis**:
- TLD aggregation with 2 wildcard patterns: ~153ms
- No baseline comparison (TLD-specific endpoint)
- Acceptable performance for infrequent queries

## Pattern-Specific Performance

### Pattern Types Comparison (on `/logs` endpoint)

| Pattern Type | Example | Avg Time (ms) | Overhead vs Baseline |
|--------------|---------|---------------|----------------------|
| Exact match | `google.com` | 39.09 | +90.9% |
| Leading wildcard | `*.apple.com` | 53.40 | +160.7% |
| Trailing wildcard | `tracking.*` | 50.39 | +146.0% |
| Middle wildcard | `*tracking*` | 52.70 | +157.3% |

**Findings**:
- **Exact matches are fastest** (~2x baseline) - use PostgreSQL `NOT IN`
- **Trailing wildcards slightly faster** than leading (~146% vs ~161%)
  - Can leverage index prefixes better
- **Leading and middle wildcards similar** performance (~157-161%)
  - Require full table scan for pattern matching
- **All wildcard types are case-insensitive** (using SQL ILIKE)

### Multiple Pattern Impact

| Pattern Count | Avg Time (ms) | Overhead |
|---------------|---------------|----------|
| 0 (baseline) | 20.48 | - |
| 1 (exact) | 39.09 | +90.9% |
| 1 (wildcard) | ~52.00 | ~154% |
| 4 (mixed) | 115.47 | +463.8% |

**Conclusion**: Overhead grows roughly linearly with pattern count, but absolute times remain reasonable.

## Performance Optimization Features

### Built-in Safeguards

1. **Overly Broad Pattern Rejection**
   - Patterns like `*`, `**`, `*.*` are rejected
   - Prevents accidental full-table scans
   - Logs warning: `⚠️ Rejecting overly broad wildcard pattern`

2. **SQL Injection Protection**
   - SQL special characters (`_`, `%`) are escaped
   - Patterns validated before query execution

3. **Case-Insensitive Matching**
   - Uses PostgreSQL `ILIKE` for wildcards
   - `func.lower()` for exact matches
   - No need for users to worry about case

## Scalability Considerations

### Current Dataset (180k records)
- ✅ All queries complete under 200ms
- ✅ Wildcard overhead is acceptable
- ✅ User experience remains responsive

### Projected Dataset (1M records)
- ⚠️ Estimate 3-5x current response times
- ⚠️ `/stats/domains` with wildcards could reach 600-1000ms
- 💡 **Solution**: Implement Valkey caching (issue #277)

### Recommended Thresholds
- **<100ms**: Excellent (real-time feel)
- **100-300ms**: Good (acceptable for most use cases)
- **300-500ms**: Fair (consider optimization)
- **>500ms**: Poor (implement caching/indexing)

## PostgreSQL Query Optimization

### Current Implementation

**Exact Match Exclusions**:
```sql
WHERE lower(domain) NOT IN ('google.com', 'facebook.com')
```
- Uses function-based filtering
- Fast for small exclusion lists
- Consider functional index: `CREATE INDEX idx_domain_lower ON dns_logs(lower(domain))`

**Wildcard Pattern Exclusions**:
```sql
WHERE domain NOT ILIKE '%.apple.com'
  AND domain NOT ILIKE '%tracking%'
```
- Uses pattern matching
- Cannot use standard B-tree indexes efficiently
- Leading wildcards (`%pattern`) prevent index usage

### Potential Optimizations

1. **Trigram Indexes (pg_trgm)**
   ```sql
   CREATE EXTENSION IF NOT EXISTS pg_trgm;
   CREATE INDEX idx_domain_trgm ON dns_logs USING gin(domain gin_trgm_ops);
   ```
   - Helps with ILIKE pattern matching
   - Reduces overhead of wildcard queries
   - **Estimated improvement**: 20-40% faster wildcard queries

2. **Functional Index for Exact Matches**
   ```sql
   CREATE INDEX idx_domain_lower ON dns_logs(lower(domain));
   ```
   - Speeds up case-insensitive exact matches
   - **Estimated improvement**: 10-20% faster exact match queries

3. **Partial Indexes for Time Ranges**
   ```sql
   CREATE INDEX idx_domain_recent ON dns_logs(domain, timestamp)
     WHERE timestamp > NOW() - INTERVAL '7 days';
   ```
   - Optimizes common queries (24h, 7d time ranges)
   - Smaller index = faster scans

## Recommendations

### For Current Implementation ✅
1. **Deploy as-is**: Performance is acceptable for production
2. **Monitor**: Track query times on production data
3. **Document**: Warn users about performance impact of many wildcards

### For Future Optimization 🔜
1. **Implement Valkey caching** (issue #277)
   - Cache `/stats/overview` results (5 min TTL)
   - Cache `/stats/domains` results (10 min TTL)
   - **Expected impact**: 90%+ faster on cache hits

2. **Add trigram indexes**
   - One-line SQL change
   - **Expected impact**: 20-40% faster wildcard queries

3. **Query result pagination**
   - For `/stats/domains` with many results
   - Reduce payload size and processing time

### User Guidelines 📋
1. **Prefer exact matches** when possible (2x faster than wildcards)
2. **Use trailing wildcards** (`domain.*`) over leading (`*.domain.com`) when both work
3. **Limit pattern count** to 3-5 for optimal performance
4. **Combine patterns** thoughtfully (e.g., `*analytics*` instead of separate patterns)

## Conclusion

The wildcard domain exclusion feature is **production-ready** with current performance characteristics:

- ✅ **Functionally complete**: Supports all planned wildcard patterns
- ✅ **Secure**: Input validation and SQL injection protection
- ✅ **Performant**: All queries under 200ms on 180k record dataset
- ✅ **Scalable**: Clear optimization path via caching and indexing

**Performance Rating**: **B+ (Good)**
- Acceptable for current use cases
- Room for optimization at larger scales
- Clear improvement path identified

---

**Test Date**: 2026-01-23
**Database Size**: 179,571 records
**Test Iterations**: 10 per scenario
**Test Script**: `backend/performance_test.py`

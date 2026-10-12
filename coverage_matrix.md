# Coverage matrix

Generated from the question metadata (`concepts:` tags) by `scripts/build_workbook.py`. Every required concept and every role-specific topic maps to at least one question; the build fails otherwise.

## Summary

| Difficulty | Questions | Share | Target |
|---|---:|---:|---:|
| Easy | 33 | 19.3% | 20% |
| Medium | 65 | 38.0% | 35% |
| Hard | 50 | 29.2% | 30% |
| Advanced | 23 | 13.5% | 15% |
| **Total (practice questions)** | **171** | | 150–180 |

Plus 3 capstones and 16 final-assessment questions.

| Dialect label | Questions |
|---|---:|
| BOTH | 164 |
| POSTGRESQL | 5 |
| MYSQL | 2 |

Of the BOTH questions, 34 need separate PostgreSQL and MySQL versions (both tested); the rest use one portable query.

### Role x difficulty (practice questions)

| Role | Easy | Medium | Hard | Advanced | Total |
|---|---:|---:|---:|---:|---:|
| Data Scientist | 21 | 47 | 28 | 6 | 102 |
| ML Engineer | 5 | 15 | 13 | 11 | 44 |
| AI Engineer | 8 | 18 | 16 | 9 | 51 |

Questions tagged with several roles count once per role.

### Module x difficulty

| Module | Easy | Medium | Hard | Advanced | Total |
|---|---:|---:|---:|---:|---:|
| M01 Foundations: filtering, NULLs, CASE, strings and dates | 12 | 3 | 0 | 0 | 15 |
| M02 Aggregation and grouping | 8 | 4 | 2 | 0 | 14 |
| M03 Joins and table grain | 3 | 9 | 4 | 0 | 16 |
| M04 Subqueries and CTEs (including recursive) | 1 | 6 | 4 | 1 | 12 |
| M05 Window functions | 1 | 12 | 5 | 2 | 20 |
| M06 Data Science analytics | 0 | 6 | 9 | 3 | 18 |
| M07 Machine Learning Engineering datasets | 2 | 3 | 7 | 8 | 20 |
| M08 AI Engineering: LLM operations and RAG data | 3 | 5 | 9 | 3 | 20 |
| M09 Set operations and data-quality checks | 1 | 5 | 2 | 0 | 8 |
| M10 Data manipulation, DDL, transactions and design | 2 | 5 | 3 | 0 | 10 |
| M11 Query performance and execution plans | 0 | 4 | 4 | 0 | 8 |
| M12 Advanced and dialect-specific features | 0 | 3 | 1 | 6 | 10 |
| M13 Capstone projects | 0 | 0 | 0 | 3 | 3 |
| M14 Final assessment | 3 | 6 | 4 | 3 | 16 |

## A. Foundations

| Concept | # | Questions |
|---|---:|---|
| SELECT and column aliases | 1 | SQL-001 (E) |
| DISTINCT | 2 | SQL-002 (E), SQL-136 (E) |
| WHERE | 6 | SQL-001 (E), SQL-004 (E), SQL-005 (E), SQL-006 (E), SQL-009 (M), SQL-030 (E) |
| AND, OR, NOT | 3 | SQL-003 (E), SQL-004 (E), SQL-015 (E) |
| IN and NOT IN | 4 | SQL-001 (E), SQL-004 (E), SQL-013 (M), SQL-048 (M) |
| BETWEEN | 1 | SQL-005 (E) |
| LIKE and pattern matching | 1 | SQL-015 (E) |
| ORDER BY | 5 | SQL-001 (E), SQL-006 (E), SQL-012 (E), SQL-016 (E), SQL-030 (E) |
| LIMIT and OFFSET | 2 | SQL-012 (E), SQL-160 (M) |
| NULL and three-valued logic | 7 | SQL-002 (E), SQL-003 (E), SQL-007 (E), SQL-011 (M), SQL-013 (M), SQL-123 (M), SQL-126 (E) |
| IS NULL / IS NOT NULL | 2 | SQL-003 (E), ASM-02 (E) |
| CASE expressions | 9 | SQL-006 (E), SQL-007 (E), SQL-011 (M), SQL-102 (H), SQL-120 (H), SQL-125 (E), SQL-126 (E), SQL-140 (M), SQL-143 (M) |
| COALESCE and NULLIF | 8 | SQL-002 (E), SQL-007 (E), SQL-008 (E), SQL-024 (M), SQL-032 (M), SQL-039 (M), SQL-118 (H), SQL-134 (M) |
| Type conversion and casting | 8 | SQL-001 (E), SQL-008 (E), SQL-010 (E), SQL-014 (E), SQL-018 (M), SQL-029 (M), SQL-090 (H), SQL-165 (M) |
| Arithmetic expressions | 8 | SQL-007 (E), SQL-008 (E), SQL-011 (M), SQL-014 (E), SQL-046 (E), SQL-094 (M), SQL-118 (H), SQL-134 (M) |
| String functions | 9 | SQL-009 (M), SQL-015 (E), SQL-044 (M), SQL-051 (H), SQL-081 (H), SQL-136 (E), SQL-142 (H), SQL-163 (M), SQL-165 (M) |
| Date and timestamp operations | 14 | SQL-001 (E), SQL-004 (E), SQL-005 (E), SQL-010 (E), SQL-011 (M), SQL-020 (E), SQL-028 (H), SQL-053 (M), SQL-062 (M), SQL-073 (H), SQL-095 (M), SQL-156 (H), SQL-164 (A), ASM-14 (H) |

## B. Aggregation

| Concept | # | Questions |
|---|---:|---|
| COUNT, SUM, AVG, MIN, MAX | 11 | SQL-016 (E), SQL-017 (E), SQL-020 (E), SQL-023 (E), SQL-026 (H), SQL-027 (E), SQL-028 (H), SQL-029 (M), SQL-042 (E), SQL-052 (H), ASM-01 (E) |
| GROUP BY | 6 | SQL-010 (E), SQL-016 (E), SQL-019 (E), SQL-021 (E), SQL-023 (E), SQL-026 (H) |
| HAVING / aggregate-level filtering | 10 | SQL-018 (M), SQL-019 (E), SQL-023 (E), SQL-036 (M), SQL-097 (M), SQL-111 (H), SQL-122 (H), SQL-128 (H), ASM-06 (M), ASM-13 (M) |
| Conditional aggregation | 32 | SQL-003 (E), SQL-018 (M), SQL-019 (E), SQL-021 (E), SQL-035 (M), SQL-036 (M), SQL-040 (H), SQL-045 (M), SQL-079 (H), SQL-085 (M), SQL-086 (M), SQL-091 (M), SQL-096 (E), SQL-098 (A), SQL-100 (A), SQL-105 (H), SQL-107 (A), SQL-109 (H), SQL-110 (A), SQL-112 (H), SQL-113 (A), SQL-116 (E), SQL-123 (M), SQL-129 (H), SQL-130 (M), SQL-151 (M), SQL-170 (H), ASM-02 (E), ASM-06 (M), ASM-08 (H), ASM-13 (M), ASM-15 (E) |
| COUNT DISTINCT | 15 | SQL-017 (E), SQL-022 (M), SQL-025 (E), SQL-037 (M), SQL-057 (H), SQL-078 (H), SQL-079 (H), SQL-092 (A), SQL-094 (M), SQL-097 (M), SQL-102 (H), SQL-125 (E), SQL-128 (H), SQL-168 (A), ASM-12 (A) |
| Aggregation across joins | 4 | SQL-022 (M), SQL-024 (M), SQL-031 (M), SQL-043 (H) |
| Grouping by date and time periods | 13 | SQL-010 (E), SQL-020 (E), SQL-025 (E), SQL-063 (M), SQL-069 (M), SQL-078 (H), SQL-095 (M), SQL-116 (E), SQL-118 (H), SQL-127 (A), SQL-133 (A), SQL-145 (M), SQL-164 (A) |
| Ratios and percentages | 23 | SQL-018 (M), SQL-021 (E), SQL-024 (M), SQL-025 (E), SQL-032 (M), SQL-035 (M), SQL-049 (M), SQL-068 (M), SQL-071 (M), SQL-078 (H), SQL-080 (H), SQL-084 (A), SQL-086 (M), SQL-088 (H), SQL-091 (M), SQL-096 (E), SQL-101 (A), SQL-103 (E), SQL-131 (M), CAP-DS (A), ASM-01 (E), ASM-04 (M), ASM-05 (M) |
| NULL-aware calculations | 6 | SQL-017 (E), SQL-024 (M), SQL-027 (E), SQL-103 (E), SQL-129 (H), ASM-15 (E) |
| COUNT(*) versus COUNT(column) | 3 | SQL-017 (E), SQL-027 (E), SQL-034 (M) |

## C. Joins

| Concept | # | Questions |
|---|---:|---|
| INNER JOIN | 4 | SQL-030 (E), SQL-108 (H), SQL-115 (H), SQL-125 (E) |
| LEFT JOIN | 17 | SQL-032 (M), SQL-033 (E), SQL-034 (M), SQL-038 (H), SQL-039 (M), SQL-050 (A), SQL-052 (H), SQL-053 (M), SQL-093 (H), SQL-105 (H), SQL-111 (H), SQL-112 (H), SQL-119 (H), SQL-124 (M), SQL-131 (M), SQL-142 (H), CAP-DS (A) |
| RIGHT JOIN | 2 | SQL-041 (H), SQL-042 (E) |
| CROSS JOIN | 3 | SQL-039 (M), SQL-084 (A), SQL-109 (H) |
| Self joins | 7 | SQL-036 (M), SQL-044 (M), SQL-045 (M), SQL-051 (H), SQL-088 (H), SQL-140 (M), SQL-141 (H) |
| Joining multiple tables | 9 | SQL-022 (M), SQL-031 (M), SQL-037 (M), SQL-043 (H), SQL-085 (M), SQL-127 (A), SQL-140 (M), SQL-146 (M), ASM-05 (M) |
| Many-to-many relationships | 1 | SQL-037 (M) |
| Joining tables at different granularities | 1 | SQL-038 (H) |
| Anti-joins / detecting unmatched records | 9 | SQL-033 (E), SQL-041 (H), SQL-083 (M), SQL-098 (A), SQL-104 (M), SQL-138 (M), SQL-141 (H), SQL-143 (M), ASM-03 (M) |
| Semi-joins using EXISTS | 10 | SQL-035 (M), SQL-055 (M), SQL-080 (H), SQL-113 (A), SQL-127 (A), SQL-137 (M), SQL-143 (M), SQL-151 (M), SQL-161 (H), ASM-03 (M) |
| NOT EXISTS | 5 | SQL-013 (M), SQL-033 (E), SQL-083 (M), SQL-104 (M), ASM-03 (M) |
| Joining on composite keys | 3 | SQL-040 (H), SQL-045 (M), SQL-149 (H) |
| Preventing join fan-out and duplicate counting | 5 | SQL-031 (M), SQL-038 (H), SQL-043 (H), SQL-050 (A), SQL-055 (M) |
| LEFT JOIN conditions versus WHERE conditions | 2 | SQL-034 (M), SQL-042 (E) |
| Range / interval joins | 12 | SQL-038 (H), SQL-056 (H), SQL-092 (A), SQL-099 (A), SQL-105 (H), SQL-118 (H), SQL-119 (H), SQL-132 (H), SQL-133 (A), CAP-AI (A), ASM-07 (H), ASM-16 (A) |

## D. Subqueries and CTEs

| Concept | # | Questions |
|---|---:|---|
| Scalar subqueries | 1 | SQL-046 (E) |
| Correlated subqueries | 6 | SQL-047 (M), SQL-056 (H), SQL-057 (H), SQL-127 (A), SQL-159 (H), SQL-171 (A) |
| Subqueries in WHERE | 5 | SQL-013 (M), SQL-046 (E), SQL-047 (M), SQL-048 (M), SQL-055 (M) |
| Common table expressions | 2 | SQL-049 (M), SQL-050 (A) |
| Multiple CTEs / analytical pipelines | 30 | SQL-049 (M), SQL-050 (A), SQL-078 (H), SQL-081 (H), SQL-082 (A), SQL-084 (A), SQL-088 (H), SQL-093 (H), SQL-098 (A), SQL-099 (A), SQL-100 (A), SQL-101 (A), SQL-102 (H), SQL-107 (A), SQL-108 (H), SQL-112 (H), SQL-115 (H), SQL-121 (H), SQL-122 (H), SQL-128 (H), SQL-129 (H), SQL-130 (M), SQL-132 (H), SQL-135 (A), CAP-DS (A), CAP-ML (A), CAP-AI (A), ASM-11 (A), ASM-12 (A), ASM-16 (A) |
| Recursive CTEs | 6 | SQL-051 (H), SQL-052 (H), SQL-053 (M), SQL-054 (M), SQL-065 (H), SQL-092 (A) |
| Subquery versus join trade-offs | 1 | SQL-055 (M) |
| Derived tables (subqueries in FROM) | 4 | SQL-028 (H), SQL-032 (M), SQL-043 (H), SQL-095 (M) |

## E. Window functions

| Concept | # | Questions |
|---|---:|---|
| ROW_NUMBER | 22 | SQL-058 (E), SQL-059 (M), SQL-061 (M), SQL-064 (M), SQL-073 (H), SQL-077 (A), SQL-089 (H), SQL-097 (M), SQL-099 (A), SQL-100 (A), SQL-106 (M), SQL-111 (H), SQL-117 (H), SQL-121 (H), SQL-122 (H), SQL-124 (M), SQL-131 (M), SQL-147 (M), SQL-159 (H), CAP-ML (A), ASM-04 (M), ASM-08 (H) |
| RANK | 3 | SQL-059 (M), SQL-060 (M), SQL-114 (A) |
| DENSE_RANK | 3 | SQL-057 (H), SQL-059 (M), ASM-10 (M) |
| LAG and LEAD | 10 | SQL-062 (M), SQL-066 (H), SQL-069 (M), SQL-070 (H), SQL-074 (M), SQL-075 (M), SQL-133 (A), ASM-04 (M), ASM-09 (H), ASM-14 (H) |
| Running totals | 4 | SQL-063 (M), SQL-070 (H), SQL-072 (H), SQL-087 (H) |
| Cumulative averages | 1 | SQL-072 (H) |
| Moving averages | 3 | SQL-065 (H), SQL-076 (A), SQL-120 (H) |
| PARTITION BY | 10 | SQL-058 (E), SQL-060 (M), SQL-061 (M), SQL-062 (M), SQL-064 (M), SQL-067 (M), SQL-071 (M), SQL-075 (M), SQL-090 (H), ASM-10 (M) |
| Window frames (ROWS / RANGE) | 6 | SQL-063 (M), SQL-065 (H), SQL-067 (M), SQL-075 (M), SQL-076 (A), SQL-120 (H) |
| FIRST_VALUE and LAST_VALUE | 1 | SQL-067 (M) |
| NTILE | 2 | SQL-068 (M), ASM-11 (A) |
| Top-N per group | 6 | SQL-047 (M), SQL-060 (M), SQL-061 (M), SQL-106 (M), SQL-171 (A), ASM-10 (M) |
| Deduplication with window functions | 12 | SQL-064 (M), SQL-077 (A), SQL-097 (M), SQL-106 (M), SQL-107 (A), SQL-131 (M), SQL-132 (H), SQL-135 (A), SQL-147 (M), SQL-170 (H), ASM-05 (M), ASM-16 (A) |
| Period-over-period comparisons | 4 | SQL-069 (M), SQL-133 (A), CAP-DS (A), ASM-09 (H) |
| Session and event-sequence analysis | 3 | SQL-058 (E), SQL-070 (H), SQL-074 (M) |
| Aggregate functions used as window functions | 13 | SQL-059 (M), SQL-063 (M), SQL-068 (M), SQL-071 (M), SQL-072 (H), SQL-087 (H), SQL-089 (H), SQL-090 (H), SQL-110 (A), SQL-114 (A), SQL-117 (H), SQL-121 (H), ASM-01 (E) |

## F. Advanced aggregation and analytics

| Concept | # | Questions |
|---|---:|---|
| Percentiles and median | 4 | SQL-089 (H), SQL-117 (H), SQL-121 (H), CAP-AI (A) |
| Cohort analysis | 2 | SQL-079 (H), SQL-081 (H) |
| Retention calculations | 2 | SQL-079 (H), SQL-080 (H) |
| Funnel conversion | 3 | SQL-074 (M), SQL-082 (A), SQL-083 (M) |
| Churn analysis | 4 | SQL-081 (H), SQL-091 (M), SQL-138 (M), ASM-14 (H) |
| Rolling time windows | 2 | SQL-076 (A), SQL-092 (A) |
| Time-series summaries / date spines | 6 | SQL-053 (M), SQL-065 (H), SQL-092 (A), SQL-095 (M), SQL-170 (H), ASM-07 (H) |
| Consecutive-event patterns | 2 | SQL-073 (H), SQL-077 (A) |
| Gaps and islands | 4 | SQL-066 (H), SQL-073 (H), SQL-077 (A), ASM-14 (H) |
| Pareto-style analysis | 2 | SQL-068 (M), SQL-087 (H) |
| Market basket analysis | 1 | SQL-088 (H) |
| Statistical summaries (stddev, z-scores, correlation) | 9 | SQL-029 (M), SQL-084 (A), SQL-086 (M), SQL-090 (H), SQL-093 (H), SQL-101 (A), SQL-110 (A), SQL-114 (A), SQL-135 (A) |
| Approximation versus exact calculation | 1 | SQL-094 (M) |

## G. Data manipulation and design

| Concept | # | Questions |
|---|---:|---|
| INSERT | 1 | SQL-144 (E) |
| UPDATE | 2 | SQL-146 (M), SQL-148 (H) |
| DELETE | 1 | SQL-147 (M) |
| INSERT ... SELECT | 3 | SQL-145 (M), SQL-149 (H), SQL-152 (H) |
| CREATE TABLE | 8 | SQL-144 (E), SQL-145 (M), SQL-146 (M), SQL-147 (M), SQL-148 (H), SQL-150 (E), SQL-152 (H), SQL-153 (M) |
| Constraints: PK, FK, UNIQUE, CHECK, NOT NULL | 3 | SQL-144 (E), SQL-148 (H), SQL-152 (H) |
| Transactions, COMMIT and ROLLBACK | 1 | SQL-148 (H) |
| Upserts | 2 | SQL-149 (H), SQL-169 (A) |
| Views | 1 | SQL-150 (E) |
| Temporary tables | 1 | SQL-151 (M) |
| Index creation and removal | 3 | SQL-153 (M), SQL-163 (M), SQL-167 (A) |
| Referential integrity | 4 | SQL-141 (H), SQL-143 (M), SQL-144 (E), SQL-152 (H) |
| Normalization fundamentals | 1 | SQL-152 (H) |

## H. Set operations

| Concept | # | Questions |
|---|---:|---|
| UNION | 1 | SQL-136 (E) |
| UNION ALL | 11 | SQL-041 (H), SQL-082 (A), SQL-104 (M), SQL-109 (H), SQL-115 (H), SQL-128 (H), SQL-136 (E), SQL-139 (M), SQL-141 (H), SQL-162 (M), ASM-07 (H) |
| INTERSECT | 1 | SQL-137 (M) |
| EXCEPT or equivalent | 2 | SQL-138 (M), SQL-139 (M) |
| Comparing records across datasets | 2 | SQL-041 (H), SQL-139 (M) |

## I. Query performance

| Concept | # | Questions |
|---|---:|---|
| Index fundamentals | 3 | SQL-153 (M), SQL-154 (M), SQL-156 (H) |
| Composite indexes | 4 | SQL-153 (M), SQL-155 (M), SQL-157 (H), SQL-160 (M) |
| Selectivity / when an index is not useful | 1 | SQL-158 (M) |
| Index-friendly (sargable) predicates | 2 | SQL-156 (H), SQL-157 (H) |
| Avoiding unnecessary SELECT * | 1 | SQL-155 (M) |
| Join order / filtering early (conceptual) | 1 | SQL-161 (H) |
| EXPLAIN | 7 | SQL-154 (M), SQL-155 (M), SQL-156 (H), SQL-157 (H), SQL-158 (M), SQL-160 (M), SQL-161 (H) |
| EXPLAIN ANALYZE or equivalent | 1 | SQL-159 (H) |
| Sequential scans versus index scans | 3 | SQL-154 (M), SQL-155 (M), SQL-158 (M) |
| Sorting and aggregation costs | 1 | SQL-160 (M) |
| Avoiding repeated calculations | 1 | SQL-161 (H) |
| Recognizing expensive correlated subqueries | 2 | SQL-056 (H), SQL-159 (H) |

## J. Advanced database features

| Concept | # | Questions |
|---|---:|---|
| JSON storage and querying | 4 | SQL-123 (M), SQL-134 (M), SQL-162 (M), SQL-168 (A) |
| Generated columns | 1 | SQL-163 (M) |
| Full-text search | 2 | SQL-166 (A), SQL-167 (A) |
| Date/time zone handling | 1 | SQL-164 (A) |
| Regular expressions | 1 | SQL-165 (M) |
| Database-specific analytical functions | 13 | SQL-026 (H), SQL-089 (H), SQL-093 (H), SQL-117 (H), SQL-142 (H), SQL-162 (M), SQL-164 (A), SQL-166 (A), SQL-167 (A), SQL-168 (A), SQL-169 (A), SQL-170 (H), SQL-171 (A) |

## Data Scientist problem set

| Concept | # | Questions |
|---|---:|---|
| Monthly active users | 5 | SQL-025 (E), SQL-065 (H), SQL-078 (H), SQL-092 (A), SQL-094 (M) |
| Top-performing customer segments | 8 | SQL-031 (M), SQL-049 (M), SQL-068 (M), SQL-071 (M), SQL-087 (H), SQL-137 (M), CAP-DS (A), ASM-03 (M) |
| Purchase conversion rates | 5 | SQL-032 (M), SQL-082 (A), SQL-151 (M), ASM-04 (M), ASM-13 (M) |
| Users who abandoned a funnel | 4 | SQL-074 (M), SQL-082 (A), SQL-083 (M), SQL-162 (M) |
| 7-day and 30-day retention | 2 | SQL-079 (H), SQL-080 (H) |
| Subscription churn by cohort | 5 | SQL-048 (M), SQL-066 (H), SQL-081 (H), CAP-DS (A), ASM-07 (H) |
| Top products by revenue within each category | 5 | SQL-022 (M), SQL-052 (H), SQL-060 (M), SQL-061 (M), SQL-088 (H) |
| Current vs previous month revenue | 3 | SQL-056 (H), SQL-069 (M), SQL-145 (M) |
| Average order value | 3 | SQL-020 (E), SQL-089 (H), CAP-DS (A) |
| Unusual spending patterns | 1 | SQL-090 (H) |
| Users whose activity declined | 3 | SQL-073 (H), SQL-091 (M), SQL-138 (M) |
| Experiment conversion rates | 5 | SQL-045 (M), SQL-084 (A), SQL-085 (M), SQL-086 (M), SQL-135 (A) |
| Experiment outcomes across segments | 1 | SQL-085 (M) |
| Duplicate and inconsistent records | 13 | SQL-009 (M), SQL-033 (E), SQL-038 (H), SQL-044 (M), SQL-048 (M), SQL-064 (M), SQL-066 (H), SQL-139 (M), SQL-140 (M), SQL-141 (H), SQL-142 (H), SQL-146 (M), SQL-163 (M) |
| Aggregated dataset for statistical analysis | 6 | SQL-028 (H), SQL-050 (A), SQL-062 (M), SQL-072 (H), SQL-093 (H), CAP-DS (A) |

## ML Engineer problem set

| Concept | # | Questions |
|---|---:|---|
| Training dataset from features and labels | 2 | SQL-099 (A), CAP-ML (A) |
| Binary classification target | 2 | SQL-096 (E), SQL-098 (A) |
| Class distribution and imbalance ratio | 3 | SQL-096 (E), CAP-ML (A), ASM-05 (M) |
| Missing features / incomplete feature records | 3 | SQL-103 (E), SQL-104 (M), CAP-ML (A) |
| Duplicate training examples | 4 | SQL-044 (M), SQL-064 (M), SQL-097 (M), SQL-142 (H) |
| Historical features from event timestamps | 4 | SQL-014 (E), SQL-050 (A), SQL-070 (H), SQL-105 (H) |
| Time-based train/validation/test split | 2 | SQL-102 (H), CAP-ML (A) |
| Target leakage detection | 3 | SQL-100 (A), SQL-101 (A), SQL-113 (A) |
| Point-in-time-correct feature joins | 7 | SQL-099 (A), SQL-100 (A), SQL-101 (A), SQL-111 (H), SQL-113 (A), CAP-ML (A), ASM-08 (H) |
| Latest valid prediction per entity | 1 | SQL-106 (M) |
| Precision, recall, accuracy, F1 from tables | 6 | SQL-107 (A), SQL-108 (H), SQL-109 (H), SQL-114 (A), SQL-115 (H), ASM-11 (A) |
| Comparing model versions | 6 | SQL-054 (M), SQL-107 (A), SQL-108 (H), SQL-114 (A), SQL-115 (H), ASM-11 (A) |
| Prediction distribution changes | 2 | SQL-075 (M), SQL-110 (A) |
| Feature missingness by date or source | 1 | SQL-103 (E) |
| Batch inference dataset | 2 | SQL-111 (H), ASM-15 (E) |
| Stale features and delayed labels | 1 | SQL-112 (H) |
| Features updated after prediction time | 2 | SQL-113 (A), ASM-08 (H) |
| Data pipeline validation | 5 | SQL-041 (H), SQL-077 (A), SQL-098 (A), SQL-105 (H), SQL-141 (H) |

## AI Engineer problem set

| Concept | # | Questions |
|---|---:|---|
| Daily LLM request volume | 7 | SQL-026 (H), SQL-035 (M), SQL-039 (M), SQL-076 (A), SQL-116 (E), SQL-137 (M), SQL-149 (H) |
| Success and failure rates | 6 | SQL-021 (E), SQL-120 (H), SQL-122 (H), SQL-158 (M), CAP-AI (A), ASM-09 (H) |
| Most expensive prompts / model versions | 1 | SQL-119 (H) |
| Token cost from a pricing table | 6 | SQL-076 (A), SQL-118 (H), SQL-119 (H), SQL-133 (A), CAP-AI (A), ASM-16 (A) |
| Average, median and percentile latency | 2 | SQL-117 (H), CAP-AI (A) |
| Latency across models and dates | 2 | SQL-029 (M), SQL-157 (H) |
| Unusually high token consumption | 3 | SQL-027 (E), SQL-121 (H), SQL-171 (A) |
| Users with repeated failures | 1 | SQL-122 (H) |
| Stale or superseded document versions | 6 | SQL-125 (E), SQL-126 (E), SQL-127 (A), SQL-150 (E), CAP-AI (A), ASM-06 (M) |
| Duplicate document chunks | 1 | SQL-128 (H) |
| Chunks of the latest document version | 3 | SQL-124 (M), SQL-150 (E), SQL-166 (A) |
| Retrieval hit rate at K / MRR | 4 | SQL-129 (H), SQL-130 (M), SQL-143 (M), ASM-12 (A) |
| Retrieval quality across configurations | 6 | SQL-040 (H), SQL-129 (H), SQL-130 (M), SQL-166 (A), SQL-167 (A), ASM-12 (A) |
| Answer acceptance rate from feedback | 6 | SQL-131 (M), SQL-132 (H), SQL-135 (A), SQL-170 (H), CAP-AI (A), ASM-16 (A) |
| Prompt versions compared by outcomes | 2 | SQL-132 (H), SQL-135 (A) |
| Missing trace IDs / incomplete metadata | 3 | SQL-123 (M), SQL-154 (M), ASM-02 (E) |
| Increases in failure rate or cost | 3 | SQL-120 (H), SQL-133 (A), ASM-09 (H) |
| Documents not re-indexed after update | 3 | SQL-126 (E), SQL-134 (M), SQL-169 (A) |
| Metadata records for a RAG ingestion pipeline | 8 | SQL-012 (E), SQL-015 (E), SQL-037 (M), SQL-124 (M), SQL-134 (M), SQL-165 (M), SQL-168 (A), SQL-169 (A) |

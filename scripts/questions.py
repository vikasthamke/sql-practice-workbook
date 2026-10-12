"""
Question source parser + controlled vocabularies.

Question files live in questions/*.txt. Format:

    ### SQL-001
    title: ...
    difficulty: Easy | Medium | Hard | Advanced
    primary: <primary concept, free text>
    secondary: <comma separated, free text>
    concepts: <comma separated tags from CONCEPTS>
    roles: DS, MLE, AI            (any subset; "Multiple" is derived)
    time: <minutes>
    dialect: BOTH | POSTGRESQL | MYSQL
    tables: users(user_id, email); orders(order_id, user_id)
    columns: col_a, col_b          (expected result columns, in order)
    compare: ordered | unordered | none
    @context
    ...
    @problem
    ...
    (more @sections, see SECTIONS)

Sections whose name starts with "solution", "alternative", "equivalent",
"verify", "setup" or "cleanup" contain SQL. Everything else is Markdown.
"""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QDIR = os.path.join(ROOT, "questions")

HEADER_FIELDS = ["title", "difficulty", "primary", "secondary", "concepts", "roles", "time",
                 "dialect", "tables", "columns", "compare"]
TEXT_SECTIONS = ["context", "problem", "expected", "edge_cases", "hint1", "hint2", "hint3",
                 "explanation", "mistakes", "performance", "interview", "dialect_note",
                 "alternative_note", "assert", "rubric"]
SQL_SECTIONS = ["setup", "setup_pg", "setup_mysql", "solution", "solution_pg", "solution_mysql",
                "alternative", "alternative_pg", "alternative_mysql", "equivalent_pg",
                "equivalent_mysql", "verify", "verify_pg", "verify_mysql", "cleanup",
                "cleanup_pg", "cleanup_mysql"]
REQUIRED = ["context", "problem", "expected", "edge_cases", "hint1", "hint2", "hint3",
            "explanation", "mistakes", "interview"]
DIFFICULTIES = ["Easy", "Medium", "Hard", "Advanced"]
DIALECTS = ["BOTH", "POSTGRESQL", "MYSQL"]
ROLE_NAMES = {"DS": "Data Scientist", "MLE": "ML Engineer", "AI": "AI Engineer"}

MODULES = [
    ("M01", "Foundations: filtering, NULLs, CASE, strings and dates"),
    ("M02", "Aggregation and grouping"),
    ("M03", "Joins and table grain"),
    ("M04", "Subqueries and CTEs (including recursive)"),
    ("M05", "Window functions"),
    ("M06", "Data Science analytics"),
    ("M07", "Machine Learning Engineering datasets"),
    ("M08", "AI Engineering: LLM operations and RAG data"),
    ("M09", "Set operations and data-quality checks"),
    ("M10", "Data manipulation, DDL, transactions and design"),
    ("M11", "Query performance and execution plans"),
    ("M12", "Advanced and dialect-specific features"),
    ("M13", "Capstone projects"),
    ("M14", "Final assessment"),
]

# Required concept tags (prompt section 6) grouped A-J, then role topics (section 7).
CONCEPTS = {
    # A. Foundations
    "select_alias": ("A", "SELECT and column aliases"),
    "distinct": ("A", "DISTINCT"),
    "where": ("A", "WHERE"),
    "boolean_logic": ("A", "AND, OR, NOT"),
    "in_not_in": ("A", "IN and NOT IN"),
    "between": ("A", "BETWEEN"),
    "like": ("A", "LIKE and pattern matching"),
    "order_by": ("A", "ORDER BY"),
    "limit_offset": ("A", "LIMIT and OFFSET"),
    "null_logic": ("A", "NULL and three-valued logic"),
    "is_null": ("A", "IS NULL / IS NOT NULL"),
    "case": ("A", "CASE expressions"),
    "coalesce_nullif": ("A", "COALESCE and NULLIF"),
    "cast": ("A", "Type conversion and casting"),
    "arithmetic": ("A", "Arithmetic expressions"),
    "string_functions": ("A", "String functions"),
    "date_functions": ("A", "Date and timestamp operations"),
    # B. Aggregation
    "aggregates": ("B", "COUNT, SUM, AVG, MIN, MAX"),
    "group_by": ("B", "GROUP BY"),
    "having": ("B", "HAVING / aggregate-level filtering"),
    "conditional_aggregation": ("B", "Conditional aggregation"),
    "count_distinct": ("B", "COUNT DISTINCT"),
    "agg_across_joins": ("B", "Aggregation across joins"),
    "date_bucketing": ("B", "Grouping by date and time periods"),
    "ratios": ("B", "Ratios and percentages"),
    "null_aware_agg": ("B", "NULL-aware calculations"),
    "count_star_vs_col": ("B", "COUNT(*) versus COUNT(column)"),
    # C. Joins
    "inner_join": ("C", "INNER JOIN"),
    "left_join": ("C", "LEFT JOIN"),
    "right_join": ("C", "RIGHT JOIN"),
    "cross_join": ("C", "CROSS JOIN"),
    "self_join": ("C", "Self joins"),
    "multi_join": ("C", "Joining multiple tables"),
    "many_to_many": ("C", "Many-to-many relationships"),
    "grain_mismatch": ("C", "Joining tables at different granularities"),
    "anti_join": ("C", "Anti-joins / detecting unmatched records"),
    "semi_join": ("C", "Semi-joins using EXISTS"),
    "not_exists": ("C", "NOT EXISTS"),
    "composite_key": ("C", "Joining on composite keys"),
    "fanout": ("C", "Preventing join fan-out and duplicate counting"),
    "join_on_vs_where": ("C", "LEFT JOIN conditions versus WHERE conditions"),
    "range_join": ("C", "Range / interval joins"),
    # D. Subqueries and CTEs
    "scalar_subquery": ("D", "Scalar subqueries"),
    "correlated_subquery": ("D", "Correlated subqueries"),
    "subquery_where": ("D", "Subqueries in WHERE"),
    "cte": ("D", "Common table expressions"),
    "multiple_ctes": ("D", "Multiple CTEs / analytical pipelines"),
    "recursive_cte": ("D", "Recursive CTEs"),
    "subquery_vs_join": ("D", "Subquery versus join trade-offs"),
    "derived_table": ("D", "Derived tables (subqueries in FROM)"),
    # E. Window functions
    "row_number": ("E", "ROW_NUMBER"),
    "rank": ("E", "RANK"),
    "dense_rank": ("E", "DENSE_RANK"),
    "lag_lead": ("E", "LAG and LEAD"),
    "running_total": ("E", "Running totals"),
    "cumulative_avg": ("E", "Cumulative averages"),
    "moving_avg": ("E", "Moving averages"),
    "partition_by": ("E", "PARTITION BY"),
    "window_frame": ("E", "Window frames (ROWS / RANGE)"),
    "first_last_value": ("E", "FIRST_VALUE and LAST_VALUE"),
    "ntile": ("E", "NTILE"),
    "top_n_per_group": ("E", "Top-N per group"),
    "dedup_window": ("E", "Deduplication with window functions"),
    "period_over_period": ("E", "Period-over-period comparisons"),
    "sessionization": ("E", "Session and event-sequence analysis"),
    "window_agg": ("E", "Aggregate functions used as window functions"),
    # F. Advanced analytics
    "percentile": ("F", "Percentiles and median"),
    "cohort": ("F", "Cohort analysis"),
    "retention": ("F", "Retention calculations"),
    "funnel": ("F", "Funnel conversion"),
    "churn": ("F", "Churn analysis"),
    "rolling_window": ("F", "Rolling time windows"),
    "time_series": ("F", "Time-series summaries / date spines"),
    "consecutive": ("F", "Consecutive-event patterns"),
    "gaps_islands": ("F", "Gaps and islands"),
    "pareto": ("F", "Pareto-style analysis"),
    "market_basket": ("F", "Market basket analysis"),
    "stats_summary": ("F", "Statistical summaries (stddev, z-scores, correlation)"),
    "approx_vs_exact": ("F", "Approximation versus exact calculation"),
    # G. DML and design
    "insert": ("G", "INSERT"),
    "update": ("G", "UPDATE"),
    "delete": ("G", "DELETE"),
    "insert_select": ("G", "INSERT ... SELECT"),
    "create_table": ("G", "CREATE TABLE"),
    "constraints": ("G", "Constraints: PK, FK, UNIQUE, CHECK, NOT NULL"),
    "transactions": ("G", "Transactions, COMMIT and ROLLBACK"),
    "upsert": ("G", "Upserts"),
    "views": ("G", "Views"),
    "temp_tables": ("G", "Temporary tables"),
    "index_ddl": ("G", "Index creation and removal"),
    "referential_integrity": ("G", "Referential integrity"),
    "normalization": ("G", "Normalization fundamentals"),
    # H. Set operations
    "union": ("H", "UNION"),
    "union_all": ("H", "UNION ALL"),
    "intersect": ("H", "INTERSECT"),
    "except": ("H", "EXCEPT or equivalent"),
    "compare_datasets": ("H", "Comparing records across datasets"),
    # I. Performance
    "index_basics": ("I", "Index fundamentals"),
    "composite_index": ("I", "Composite indexes"),
    "selectivity": ("I", "Selectivity / when an index is not useful"),
    "sargable": ("I", "Index-friendly (sargable) predicates"),
    "select_star": ("I", "Avoiding unnecessary SELECT *"),
    "join_order": ("I", "Join order / filtering early (conceptual)"),
    "explain": ("I", "EXPLAIN"),
    "explain_analyze": ("I", "EXPLAIN ANALYZE or equivalent"),
    "scan_types": ("I", "Sequential scans versus index scans"),
    "sort_agg_cost": ("I", "Sorting and aggregation costs"),
    "repeated_calc": ("I", "Avoiding repeated calculations"),
    "correlated_cost": ("I", "Recognizing expensive correlated subqueries"),
    # J. Advanced features
    "json": ("J", "JSON storage and querying"),
    "generated_columns": ("J", "Generated columns"),
    "full_text": ("J", "Full-text search"),
    "time_zones": ("J", "Date/time zone handling"),
    "regex": ("J", "Regular expressions"),
    "dialect_functions": ("J", "Database-specific analytical functions"),
    # Role topics: Data Scientist
    "ds_mau": ("DS", "Monthly active users"),
    "ds_segments": ("DS", "Top-performing customer segments"),
    "ds_conversion": ("DS", "Purchase conversion rates"),
    "ds_funnel_abandon": ("DS", "Users who abandoned a funnel"),
    "ds_retention": ("DS", "7-day and 30-day retention"),
    "ds_churn_cohort": ("DS", "Subscription churn by cohort"),
    "ds_top_products": ("DS", "Top products by revenue within each category"),
    "ds_mom_revenue": ("DS", "Current vs previous month revenue"),
    "ds_aov": ("DS", "Average order value"),
    "ds_unusual_spend": ("DS", "Unusual spending patterns"),
    "ds_activity_decline": ("DS", "Users whose activity declined"),
    "ds_experiment": ("DS", "Experiment conversion rates"),
    "ds_experiment_segments": ("DS", "Experiment outcomes across segments"),
    "ds_duplicates": ("DS", "Duplicate and inconsistent records"),
    "ds_analysis_dataset": ("DS", "Aggregated dataset for statistical analysis"),
    # Role topics: ML Engineer
    "ml_training_set": ("MLE", "Training dataset from features and labels"),
    "ml_binary_target": ("MLE", "Binary classification target"),
    "ml_class_balance": ("MLE", "Class distribution and imbalance ratio"),
    "ml_missing_features": ("MLE", "Missing features / incomplete feature records"),
    "ml_duplicate_examples": ("MLE", "Duplicate training examples"),
    "ml_historical_features": ("MLE", "Historical features from event timestamps"),
    "ml_time_split": ("MLE", "Time-based train/validation/test split"),
    "ml_leakage": ("MLE", "Target leakage detection"),
    "ml_point_in_time": ("MLE", "Point-in-time-correct feature joins"),
    "ml_latest_prediction": ("MLE", "Latest valid prediction per entity"),
    "ml_metrics": ("MLE", "Precision, recall, accuracy, F1 from tables"),
    "ml_model_compare": ("MLE", "Comparing model versions"),
    "ml_prediction_drift": ("MLE", "Prediction distribution changes"),
    "ml_missingness_by_date": ("MLE", "Feature missingness by date or source"),
    "ml_batch_inference": ("MLE", "Batch inference dataset"),
    "ml_stale_delayed": ("MLE", "Stale features and delayed labels"),
    "ml_features_after_pred": ("MLE", "Features updated after prediction time"),
    "ml_pipeline_validation": ("MLE", "Data pipeline validation"),
    # Role topics: AI Engineer
    "ai_volume": ("AI", "Daily LLM request volume"),
    "ai_success_rate": ("AI", "Success and failure rates"),
    "ai_expensive": ("AI", "Most expensive prompts / model versions"),
    "ai_token_cost": ("AI", "Token cost from a pricing table"),
    "ai_latency_pct": ("AI", "Average, median and percentile latency"),
    "ai_latency_compare": ("AI", "Latency across models and dates"),
    "ai_high_tokens": ("AI", "Unusually high token consumption"),
    "ai_repeated_failures": ("AI", "Users with repeated failures"),
    "ai_stale_docs": ("AI", "Stale or superseded document versions"),
    "ai_duplicate_chunks": ("AI", "Duplicate document chunks"),
    "ai_latest_version_chunks": ("AI", "Chunks of the latest document version"),
    "ai_hit_rate": ("AI", "Retrieval hit rate at K / MRR"),
    "ai_retrieval_compare": ("AI", "Retrieval quality across configurations"),
    "ai_acceptance": ("AI", "Answer acceptance rate from feedback"),
    "ai_prompt_compare": ("AI", "Prompt versions compared by outcomes"),
    "ai_missing_metadata": ("AI", "Missing trace IDs / incomplete metadata"),
    "ai_regression": ("AI", "Increases in failure rate or cost"),
    "ai_not_reindexed": ("AI", "Documents not re-indexed after update"),
    "ai_rag_ingestion": ("AI", "Metadata records for a RAG ingestion pipeline"),
}

GROUP_NAMES = {
    "A": "A. Foundations", "B": "B. Aggregation", "C": "C. Joins", "D": "D. Subqueries and CTEs",
    "E": "E. Window functions", "F": "F. Advanced aggregation and analytics",
    "G": "G. Data manipulation and design", "H": "H. Set operations", "I": "I. Query performance",
    "J": "J. Advanced database features", "DS": "Data Scientist problem set",
    "MLE": "ML Engineer problem set", "AI": "AI Engineer problem set",
}


def parse_file(path):
    text = open(path, encoding="utf-8").read()
    blocks = re.split(r"^### ", text, flags=re.M)[1:]
    out = []
    for b in blocks:
        lines = b.split("\n")
        qid = lines[0].strip()
        q = {"id": qid, "file": os.path.basename(path), "sections": {}}
        i = 1
        while i < len(lines) and not lines[i].startswith("@"):
            ln = lines[i]
            if ln.strip():
                k, _, v = ln.partition(":")
                q[k.strip()] = v.strip()
            i += 1
        cur = None
        buf = []
        for ln in lines[i:]:
            if ln.startswith("@") and re.match(r"^@[a-z0-9_]+\s*$", ln):
                if cur:
                    q["sections"][cur] = "\n".join(buf).strip("\n")
                cur = ln[1:].strip()
                buf = []
            else:
                buf.append(ln)
        if cur:
            q["sections"][cur] = "\n".join(buf).strip("\n")
        out.append(q)
    return out


def parse_tables(spec):
    """'users(user_id, email); orders(order_id)' -> {'users': ['user_id','email'], ...}"""
    res = {}
    for part in [p.strip() for p in spec.split(";") if p.strip()]:
        m = re.match(r"^([a-z_]+)\s*\((.*)\)$", part)
        if not m:
            res[part] = []
            continue
        res[m.group(1)] = [c.strip() for c in m.group(2).split(",") if c.strip()]
    return res


def load_all(prefix=None):
    files = sorted(f for f in os.listdir(QDIR) if f.endswith(".txt"))
    qs = []
    for f in files:
        if prefix and not f.startswith(prefix):
            continue
        qs.extend(parse_file(os.path.join(QDIR, f)))
    return qs


def module_of(q):
    return q.get("module") or q["file"][:3].upper()


def lint(q, schema_tables):
    """Return a list of problems with a parsed question (metadata only)."""
    errs = []
    for f in HEADER_FIELDS:
        if not q.get(f):
            errs.append(f"missing header field '{f}'")
    if q.get("difficulty") not in DIFFICULTIES:
        errs.append(f"bad difficulty {q.get('difficulty')}")
    if q.get("dialect") not in DIALECTS:
        errs.append(f"bad dialect {q.get('dialect')}")
    for s in REQUIRED:
        if not q["sections"].get(s):
            errs.append(f"missing section @{s}")
    for s in q["sections"]:
        if s not in TEXT_SECTIONS + SQL_SECTIONS:
            errs.append(f"unknown section @{s}")
    has = q["sections"]
    d = q.get("dialect")
    if d == "BOTH" and not (has.get("solution") or (has.get("solution_pg") and has.get("solution_mysql"))):
        errs.append("BOTH needs @solution or @solution_pg + @solution_mysql")
    if d == "POSTGRESQL" and not (has.get("solution") or has.get("solution_pg")):
        errs.append("POSTGRESQL needs @solution(_pg)")
    if d == "MYSQL" and not (has.get("solution") or has.get("solution_mysql")):
        errs.append("MYSQL needs @solution(_mysql)")
    for tag in [t.strip() for t in q.get("concepts", "").split(",") if t.strip()]:
        if tag not in CONCEPTS:
            errs.append(f"unknown concept tag '{tag}'")
    for r in [r.strip() for r in q.get("roles", "").split(",") if r.strip()]:
        if r not in ROLE_NAMES:
            errs.append(f"unknown role '{r}'")
    for t, cols in parse_tables(q.get("tables", "")).items():
        if t not in schema_tables:
            errs.append(f"unknown table '{t}'")
            continue
        for c in cols:
            if c not in schema_tables[t]:
                errs.append(f"unknown column {t}.{c}")
    if q.get("compare") not in ("ordered", "unordered", "none"):
        errs.append("compare must be ordered|unordered|none")
    try:
        int(q.get("time", "x"))
    except ValueError:
        errs.append("time must be an integer number of minutes")
    return errs


def roles_label(q):
    rs = [r.strip() for r in q.get("roles", "").split(",") if r.strip()]
    if len(rs) > 1:
        return "Multiple (" + ", ".join(ROLE_NAMES[r] for r in rs) + ")"
    return ROLE_NAMES.get(rs[0], rs[0]) if rs else ""

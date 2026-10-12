#!/usr/bin/env python3
"""
Build every learner-facing file from the validated sources.

  python3 scripts/build_workbook.py

Inputs : questions/*.txt, validation/results.json, scripts/schema.py, data/*.csv
Outputs: SQL_Practice_Workbook.ipynb, solutions.sql, solutions_postgresql.sql,
         solutions_mysql.sql, question_registry.csv, coverage_matrix.md,
         dataset_dictionary.md, validation/report.md, workbook_data/questions.json
"""
import csv
import json
import os
import re
import sys
import textwrap
from collections import Counter, defaultdict
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from questions import CONCEPTS, GROUP_NAMES, MODULES, ROLE_NAMES, load_all, module_of, parse_tables, roles_label  # noqa: E402
from schema import TABLES, engine_type  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = json.load(open(os.path.join(ROOT, "validation", "results.json"), encoding="utf-8"))
RES = RESULTS["questions"]
ENGINES = RESULTS.get("engines", {})
PG_VER = (ENGINES.get("pg", "PostgreSQL").split(" on ")[0])
MY_VER = "MySQL " + ENGINES.get("mysql", "8.x")
QS = load_all()
QBY = {q["id"]: q for q in QS}
MODULE_TITLE = dict(MODULES)
DIFF_ORDER = ["Easy", "Medium", "Hard", "Advanced"]
POINTS = {"Easy": 4, "Medium": 6, "Hard": 8, "Advanced": 10}

MODULE_INFO = {
    "M01": (["Filter rows with WHERE, IN, BETWEEN and LIKE, and know when each is safe",
             "Reason about NULL and three-valued logic (the NOT IN trap)",
             "Use CASE, COALESCE and NULLIF; cast and round correctly in both engines",
             "Handle strings and timestamps portably; know where MySQL and PostgreSQL differ (collations, date math)"],
            ["Why does `x NOT IN (SELECT ...)` return no rows when the subquery contains a NULL?",
             "Why is `ts >= start AND ts < next_start` safer than BETWEEN for timestamps?",
             "Which MySQL collation compares case-sensitively *and* respects trailing spaces?"]),
    "M02": (["Use aggregates, GROUP BY and HAVING precisely",
             "Pivot with conditional aggregation",
             "Choose the right COUNT variant and denominator; avoid integer division",
             "Build subtotals with ROLLUP and recognise weighted vs unweighted averages"],
            ["What does `AVG(col)` do with NULLs, and when is that the wrong denominator?",
             "Why can't you write `HAVING alias > 10` in PostgreSQL?",
             "When is the average of per-user averages the right metric?"]),
    "M03": (["State the grain of every table before joining",
             "Prevent fan-out and double counting",
             "Place filters correctly in LEFT JOINs (ON vs WHERE)",
             "Write semi-joins, anti-joins, self joins, range joins and composite-key joins",
             "Emulate FULL OUTER JOIN in MySQL"],
            ["What happens to `SUM(order_total)` after joining order lines?",
             "Why does a WHERE filter on the right table turn a LEFT JOIN into an INNER JOIN?",
             "How do you detect orders that match zero or two subscription periods?"]),
    "M04": (["Use scalar and correlated subqueries deliberately",
             "Structure analyses as CTE pipelines",
             "Write recursive CTEs for trees, transitive closures and date spines",
             "Decide between subqueries, EXISTS and joins"],
            ["Why is a correlated subquery acceptable with an index but dangerous without one?",
             "What must match between the anchor and recursive members of a recursive CTE?",
             "How do you produce a row for days without data?"]),
    "M05": (["Number, rank and deduplicate with ROW_NUMBER, RANK and DENSE_RANK",
             "Compare rows with LAG/LEAD and compute running, moving and cumulative metrics",
             "Control window frames (ROWS vs RANGE) and know the defaults",
             "Solve top-N per group, sessionization and gaps-and-islands problems"],
            ["What is the default frame when a window has ORDER BY, and why does it matter?",
             "Why does LAST_VALUE often return the current row?",
             "Explain the `date - ROW_NUMBER()` trick for consecutive days."]),
    "M06": (["Define and compute product metrics: MAU, stickiness, retention, churn, funnels",
             "Analyse experiments: exposure-relative conversion, lift, z statistic, SRM, segment effects",
             "Compute medians, outliers, correlation, Pareto shares and basket rules in SQL",
             "Know when approximation is acceptable"],
            ["How do you define a cohort and its denominator?",
             "Why must experiment conversion be measured from each user's assignment time?",
             "What does a sample-ratio mismatch tell you?"]),
    "M07": (["Build training sets with point-in-time-correct feature joins",
             "Detect and quantify target leakage, duplicates and delayed or missing data",
             "Create time-based splits and batch-inference inputs that match training",
             "Compute precision, recall, F1, AUC, lift and drift (PSI) from raw tables"],
            ["Which two timestamps decide whether a feature row was usable at prediction time?",
             "How would you prove that stored labels match their definition?",
             "Why compare models on paired examples?"]),
    "M08": (["Monitor LLM volume, failures, latency percentiles and cost with time-varying prices",
             "Manage versioned documents and chunks: latest versions, stale content, duplicates",
             "Evaluate retrieval (hit@k, MRR) and answer quality (acceptance, prompt comparisons)",
             "Prepare metadata for RAG ingestion and analyse AI experiments"],
            ["Why are p95/p99 latencies more useful than the mean for LLM features?",
             "How do you attribute the right token price to a historical request?",
             "What makes a retrieved chunk 'stale', and how do you measure it at request time?"]),
    "M09": (["Use UNION, UNION ALL, INTERSECT and EXCEPT (and their MySQL version limits)",
             "Diff datasets with symmetric differences",
             "Build data-quality scorecards and entity-resolution clusters",
             "Check referential integrity where no foreign key exists"],
            ["When is UNION ALL correct and UNION wrong?",
             "How would you prove that a refactored pipeline produces identical output?"]),
    "M10": (["Create tables with PK, FK, UNIQUE, CHECK and NOT NULL constraints",
             "Write INSERT ... SELECT, UPDATE/DELETE with joins, and idempotent upserts",
             "Use transactions and savepoints; know the DDL behaviour of each engine",
             "Apply views, temporary tables, normalization and index DDL"],
            ["Why is an upsert-based load idempotent?",
             "What does MySQL do with an inline `REFERENCES` clause?",
             "What happens to DDL inside a transaction in PostgreSQL vs MySQL?"]),
    "M11": (["Read EXPLAIN and EXPLAIN ANALYZE output in both engines",
             "Write sargable predicates and design composite and covering indexes",
             "Recognise when an index is useless, and when a sort or a repeated subplan is the bottleneck"],
            ["Why does `CAST(ts AS DATE) = '...'` prevent an index range scan?",
             "Which composite index serves `WHERE a = ? AND b BETWEEN ...`?",
             "What does `loops=1359` on a SubPlan tell you?"]),
    "M12": (["Query JSON in both dialects, unnest arrays, use generated columns",
             "Handle time zones and DST correctly",
             "Use regular expressions and full-text search in each engine",
             "Use MERGE, DISTINCT ON, FILTER, generate_series and LATERAL where available"],
            ["Why can `CONVERT_TZ` silently return NULL in MySQL?",
             "When would you choose LATERAL over a window function for top-N per group?"]),
}

REFERENCE = r"""
## SQL concept reference

A compact reference to keep open while practising. Every item is practised in the modules.

### Logical order of evaluation
`FROM/JOIN → WHERE → GROUP BY → HAVING → window functions → SELECT → DISTINCT → ORDER BY → LIMIT/OFFSET`
- WHERE cannot see aggregates or window results; HAVING filters groups; filter on window results in an outer query.
- ORDER BY may use SELECT aliases (both engines); HAVING may use aliases only in MySQL.

### NULL rules
- Any comparison with NULL is UNKNOWN; WHERE and `CASE WHEN` keep only TRUE.
- `x NOT IN (..., NULL)` is never TRUE; prefer `NOT EXISTS`.
- Aggregates ignore NULLs (except `COUNT(*)`); `SUM` of only NULLs is NULL, so wrap it in `COALESCE(SUM(x), 0)`.
- GROUP BY, DISTINCT, PARTITION BY and set operators treat NULLs as equal; `=` does not.
- Sort order: PostgreSQL puts NULLs **last** in ascending order, MySQL **first**. Portable: `ORDER BY col IS NULL, col`.

### Joins at a glance
| Join | Keeps | Typical use |
|---|---|---|
| `INNER JOIN` | matching pairs | lookups along foreign keys |
| `LEFT JOIN` | all left rows | keep entities without activity (filters on the right table go in **ON**) |
| `RIGHT JOIN` | all right rows | rarely needed; rewrite as LEFT JOIN |
| `FULL OUTER JOIN` | all rows of both | reconciliation (PostgreSQL only; MySQL: LEFT JOIN + anti-join UNION ALL) |
| `CROSS JOIN` | all combinations | grids, spines, one-row parameter CTEs |
| `EXISTS` / `NOT EXISTS` | semi / anti join | "has at least one" / "has none" without duplicates |

### Window functions
```sql
fn(...) OVER (PARTITION BY p ORDER BY o [ROWS|RANGE BETWEEN start AND end])
```
- Default frame with ORDER BY: `RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW` (includes peers).
- Ranking: `ROW_NUMBER` (unique), `RANK` (gaps after ties), `DENSE_RANK` (no gaps), `NTILE(n)`.
- Offsets: `LAG(x, k)`, `LEAD(x, k)`; `FIRST_VALUE` / `LAST_VALUE` (needs a full frame).
- Named windows: `... OVER w ... WINDOW w AS (PARTITION BY ... ORDER BY ...)` (both engines).

### PostgreSQL vs MySQL cheat sheet
| Task | PostgreSQL 16+ | MySQL 8.0+ |
|---|---|---|
| String concatenation | `CONCAT(a, b)` (NULLs ignored), `a \|\| b` | `CONCAT(a, b)` (NULL if any NULL); `\|\|` is OR |
| Case-insensitive match | `ILIKE`, `LOWER(x) LIKE` | default collation is case-insensitive |
| Month start | `DATE_TRUNC('month', ts)` | `DATE_FORMAT(ts, '%Y-%m-01')` |
| Week start (Monday) | `DATE_TRUNC('week', ts)` | `DATE_SUB(DATE(ts), INTERVAL WEEKDAY(ts) DAY)` |
| Add an interval | `ts + INTERVAL '7' DAY` (portable) | `ts + INTERVAL '7' DAY` (portable) |
| Seconds between timestamps | `EXTRACT(EPOCH FROM b - a)` | `TIMESTAMPDIFF(SECOND, a, b)` |
| Days between dates | `d2 - d1` | `DATEDIFF(d2, d1)` |
| Date minus n days | `d - n` | `DATE_SUB(d, INTERVAL n DAY)` |
| ISO weekday | `EXTRACT(ISODOW FROM d)` | `WEEKDAY(d) + 1` |
| Round a DOUBLE | `ROUND(CAST(x AS NUMERIC), 2)` | `ROUND(x, 2)` |
| Integer division | `7 / 2 = 3` | `7 / 2 = 3.5000` |
| Count a condition | `COUNT(*) FILTER (WHERE c)` | `SUM(c)` |
| Latest row per key | `DISTINCT ON (k) ... ORDER BY k, t DESC` | `ROW_NUMBER()` + filter |
| String aggregation | `STRING_AGG(x, ',' ORDER BY x)` | `GROUP_CONCAT(x ORDER BY x SEPARATOR ',')` |
| Percentile / median | `PERCENTILE_CONT/DISC(p) WITHIN GROUP (ORDER BY x)` | window functions (ROW_NUMBER + COUNT) |
| Date series | `generate_series(a, b, INTERVAL '1 day')` | recursive CTE |
| Upsert | `INSERT ... ON CONFLICT (k) DO UPDATE SET c = EXCLUDED.c` | `INSERT ... ON DUPLICATE KEY UPDATE c = alias.c` |
| MERGE | 15+ | not available |
| JSON value as text | `doc->>'key'` | `doc->>'$.key'` |
| JSON containment / key exists | `doc @> '{"k":1}'`, `doc ? 'k'` | `JSON_CONTAINS(doc, ...)`, `JSON_CONTAINS_PATH(doc, 'one', '$.k')` |
| Array to rows | `jsonb_array_elements_text(doc->'tags')` | `JSON_TABLE(doc, '$.tags[*]' COLUMNS (...))` |
| Regex match / extract | `s ~ 'p'`, `SUBSTRING(s FROM 'p(x)')` | `REGEXP_LIKE(s, 'p', 'c')`, `REGEXP_SUBSTR(s, 'p')` |
| Full-text search | `to_tsvector(...) @@ websearch_to_tsquery(...)` | `MATCH(col) AGAINST (...)` + FULLTEXT index |
| Time zones | `(ts AT TIME ZONE 'UTC') AT TIME ZONE 'Europe/Berlin'` | `CONVERT_TZ(ts, 'UTC', 'Europe/Berlin')` (needs tz tables) |
| FULL OUTER JOIN | yes | emulate |
| INTERSECT / EXCEPT | yes | 8.0.31+ |
| LATERAL | yes | 8.0.14+ |
| Multi-table UPDATE | `UPDATE t SET ... FROM s WHERE ...` | `UPDATE t JOIN s ON ... SET ...` |
| EXPLAIN | `EXPLAIN (ANALYZE, BUFFERS) ...` | `EXPLAIN FORMAT=TREE ...`, `EXPLAIN ANALYZE ...` |
| Reserved-word traps | — | `lines`, `stored`, `rank`, `groups` and others are reserved |

### Metric formulas used in the workbook
| Metric | Formula |
|---|---|
| Conversion / rate | events of interest / eligible population (state both) |
| Precision, recall | TP / (TP + FP), TP / (TP + FN) |
| F1 | 2TP / (2TP + FP + FN) |
| ROC AUC | (Σ ranks of positives − P(P+1)/2) / (P·N) with average ranks for ties |
| Lift@k | positive rate in the top k% / overall positive rate |
| Hit@k, MRR@k | share of queries with a relevant result in the top k; mean of 1/rank of the first relevant result |
| PSI | Σ (p_new − p_ref) · ln(p_new / p_ref) |
| Two-proportion z | (p₁ − p₂) / √(p(1 − p)(1/n₁ + 1/n₂)), with pooled p |
| χ² (SRM) | Σ (observed − expected)² / expected |
"""


# ----------------------------------------------------------------- helpers
def md_escape_cell(v):
    if v is None:
        return "NULL"
    s = str(v).replace("|", "\\|").replace("\n", " ")
    return s if len(s) <= 60 else s[:57] + "..."


def preview_table(run, n=5):
    cols, rows = run.get("columns") or [], run.get("preview") or []
    if not cols:
        return ""
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for r in rows[:n]:
        lines.append("| " + " | ".join(md_escape_cell(v) for v in r) + " |")
    return "\n".join(lines)


def ref_run(q):
    r = RES.get(q["id"], {}).get("runs", {})
    if q["dialect"] == "MYSQL":
        return r.get("main:mysql")
    return r.get("main:pg") or r.get("main:mysql")


def validation_line(q):
    rec = RES.get(q["id"])
    if not rec:
        return "Not validated."
    runs = rec.get("runs", {})
    bits = []
    if "main:pg" in runs:
        bits.append(f"{PG_VER} {'✓' if runs['main:pg']['ok'] else '✗'}")
    if "main:mysql" in runs:
        bits.append(f"{MY_VER} {'✓' if runs['main:mysql']['ok'] else '✗'}")
    if "equivalent:mysql" in runs:
        bits.append(f"MySQL equivalent on {MY_VER} {'✓' if runs['equivalent:mysql']['ok'] else '✗'}")
    if "equivalent:pg" in runs:
        bits.append(f"PostgreSQL equivalent on {PG_VER} {'✓' if runs['equivalent:pg']['ok'] else '✗'}")
    extra = []
    if rec.get("engines_match"):
        extra.append("identical results on both engines")
    if rec.get("equivalent_match"):
        extra.append("equivalent returns identical results")
    if rec.get("independent_match"):
        extra.append("independently re-computed in Python")
    alts = [k for k in runs if k.startswith("alternative")]
    if alts and rec.get("status") == "PASS" and q.get("compare") != "none":
        extra.append("alternative solution returns the same result")
    s = "Executed on: " + ", ".join(bits)
    if extra:
        s += " — " + "; ".join(extra)
    return s + "."


def badges(q):
    return (f"**Difficulty:** {q['difficulty']} · **Role:** {roles_label(q)} · **Dialect:** {q['dialect']} · "
            f"**Estimated time:** {q['time']} min  \n"
            f"**Primary concept:** {q['primary']} · **Also practises:** {q['secondary']}")


def tables_md(q):
    parts = []
    for t, cols in parse_tables(q["tables"]).items():
        parts.append(f"`{t}` ({', '.join(cols)})" if cols else f"`{t}`")
    return "; ".join(parts)


def bullets_md(text):
    return text.strip()


def solution_blocks(q, for_notebook=True):
    """List of (label, sql) for the solution section."""
    s, d, out = q["sections"], q["dialect"], []
    if s.get("setup") and not s.get("setup_mysql"):
        out.append(("Setup (run first)", s["setup"]))
    elif s.get("setup"):
        out.append(("Setup (PostgreSQL)", s["setup"]))
        out.append(("Setup (MySQL)", s["setup_mysql"]))
    if s.get("solution"):
        lab = {"BOTH": "Solution (portable: PostgreSQL and MySQL)", "POSTGRESQL": "Solution (PostgreSQL)",
               "MYSQL": "Solution (MySQL)"}[d]
        out.append((lab, s["solution"]))
    if s.get("solution_pg"):
        out.append(("Solution (PostgreSQL)", s["solution_pg"]))
    if s.get("solution_mysql"):
        out.append(("Solution (MySQL)", s["solution_mysql"]))
    if s.get("verify"):
        out.append(("Verify", s["verify"]))
    for k, lab in (("verify_pg", "Verify (PostgreSQL)"), ("verify_mysql", "Verify (MySQL)")):
        if s.get(k):
            out.append((lab, s[k]))
    if s.get("equivalent_mysql"):
        out.append(("MySQL equivalent (validated)", s["equivalent_mysql"]))
    if s.get("equivalent_pg"):
        out.append(("PostgreSQL equivalent (validated)", s["equivalent_pg"]))
    for k, lab in (("cleanup", "Clean up"), ("cleanup_pg", "Clean up (PostgreSQL)"), ("cleanup_mysql", "Clean up (MySQL)")):
        if s.get(k):
            out.append((lab, s[k]))
    return out


def alternative_blocks(q):
    s, out = q["sections"], []
    for k, lab in (("alternative", "Alternative (portable)"), ("alternative_pg", "Alternative (PostgreSQL)"),
                   ("alternative_mysql", "Alternative (MySQL)")):
        if s.get(k):
            out.append((lab, s[k]))
    return out


def ensure_semicolon(sql):
    sql = sql.rstrip()
    return sql if sql.endswith(";") else sql + ";"


# ------------------------------------------------------------- notebook
def md_cell(text):
    lines = text.strip("\n").split("\n")
    return {"cell_type": "markdown", "metadata": {}, "source": [l + "\n" for l in lines[:-1]] + [lines[-1]]}


def code_cell(text):
    lines = text.strip("\n").split("\n")
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [],
            "source": [l + "\n" for l in lines[:-1]] + [lines[-1]]}


def groups():
    g = defaultdict(list)
    for q in QS:
        g[module_of(q)].append(q)
    return g


def question_markdown(q, assessment=False):
    run = ref_run(q)
    parts = [f'<a id="q-{q["id"]}"></a>', f'### {q["id"]} · {q["title"]}', badges(q), "",
             f"**Context.** {q['sections']['context']}", "",
             f"**Problem.** {q['sections']['problem']}", "",
             f"**Tables and columns.** {tables_md(q)}", "",
             f"**Expected output.** {q['sections']['expected']}", "",
             "**Edge cases to consider**", bullets_md(q["sections"]["edge_cases"]), ""]
    if assessment:
        parts.append(f"**Points:** {POINTS[q['difficulty']]} (using a hint costs 1 point per hint)")
        parts.append("")
    for i in (1, 2, 3):
        parts += [f"<details><summary><b>Hint {i}</b></summary>", "", q["sections"][f"hint{i}"], "", "</details>", ""]
    if run and run.get("ok") and q.get("compare") != "none":
        parts += ["<details><summary><b>Check your result</b> (reference output preview)</summary>", "",
                  f"The reference solution returns **{run['row_count']} row(s)**. First rows:", "",
                  preview_table(run), "", "</details>", ""]
    elif q.get("compare") == "none":
        parts += ["*This exercise produces an execution plan; plans differ by engine version and are discussed in the solution.*", ""]
    parts.append(f"[Go to the solution →](#s-{q['id']})")
    return "\n".join(parts)


def answer_cell(q):
    return (f"# {q['id']}: write your SQL here and run it in psql / MySQL Workbench / pgAdmin.\n"
            f"# Optional (see Setup): uncomment to run it from the notebook or compare with the reference result.\n"
            f'my_sql = """\n\n"""\n'
            f"# run(my_sql)\n"
            f'# check("{q["id"]}", my_sql)')


def solution_markdown(q):
    s = q["sections"]
    parts = [f'<a id="s-{q["id"]}"></a>', f'### Solution {q["id"]} · {q["title"]}',
             f'[← Back to the question](#q-{q["id"]}) · {q["difficulty"]} · {q["dialect"]}', "",
             f"*{validation_line(q)}*", ""]
    for lab, sql in solution_blocks(q):
        parts += [f"**{lab}**", "```sql", sql.strip(), "```", ""]
    parts += ["**Explanation**", "", s["explanation"].strip(), ""]
    alts = alternative_blocks(q)
    if alts:
        for lab, sql in alts:
            parts += [f"**{lab}**", "```sql", sql.strip(), "```", ""]
        if s.get("alternative_note"):
            parts += [s["alternative_note"].strip(), ""]
    if s.get("dialect_note"):
        parts += ["**PostgreSQL vs MySQL**", "", s["dialect_note"].strip(), ""]
    parts += ["**Common mistakes**", "", s["mistakes"].strip(), ""]
    if s.get("performance"):
        parts += ["**Performance note**", "", s["performance"].strip(), ""]
    parts += ["**Interview insight**", "", s["interview"].strip(), ""]
    if s.get("rubric"):
        parts += ["**Scoring rubric**", "", s["rubric"].strip(), ""]
    run = ref_run(q)
    if q.get("compare") == "none" and run and run.get("preview"):
        txt = "\n".join(r[0] for r in run["preview"])[:3000]
        parts += [f"**Plan produced during validation ({PG_VER if q['dialect'] != 'MYSQL' else MY_VER})**", "```text", txt, "```", ""]
        myrun = RES.get(q["id"], {}).get("runs", {}).get("main:mysql")
        if q["dialect"] == "BOTH" and myrun and myrun.get("preview"):
            parts += [f"**Plan produced during validation ({MY_VER})**", "```text",
                      "\n".join(r[0] for r in myrun["preview"])[:3000], "```", ""]
    return "\n".join(parts)


def schema_markdown():
    lines = ["## Database schema and relationships", "",
             "The dataset describes **Lumen Analytics**, a fictional SaaS data platform with AI features "
             "(a RAG support bot, a SQL copilot and a document summarizer). 32 tables in five domains. "
             "All timestamps are UTC; \"today\" is **2025-07-01**. Full column-level documentation is in "
             "`dataset_dictionary.md`.", ""]
    dom = defaultdict(list)
    for t in TABLES:
        dom[t["domain"]].append(t)
    counts = table_counts()
    for d, ts in dom.items():
        lines += [f"**{d}**", "", "| table | grain | rows | key relationships |", "|---|---|---:|---|"]
        for t in ts:
            rels = ", ".join(f"{', '.join(c)} → {r}" for c, r, _ in t["fks"]) or "—"
            lines.append(f"| `{t['name']}` | {t['grain']} | {counts[t['name']]:,} | {rels} |")
        lines.append("")
    lines += ["**Entity-relationship diagram** (renders in JupyterLab ≥ 4.1, VS Code and GitHub)", "", "```mermaid",
              mermaid_er(), "```"]
    return "\n".join(lines)


def mermaid_er():
    out = ["erDiagram"]
    for t in TABLES:
        for cols, ref, _ in t["fks"]:
            if ref == t["name"]:
                out.append(f'    {ref} ||--o{{ {t["name"]} : "{cols[0]} (self)"')
            else:
                out.append(f'    {ref} ||--o{{ {t["name"]} : "{cols[0]}"')
    return "\n".join(out)


def table_counts():
    c = {}
    for t in TABLES:
        with open(os.path.join(ROOT, "data", f"{t['name']}.csv"), encoding="utf-8") as fh:
            c[t["name"]] = sum(1 for _ in csv.reader(fh)) - 1
    return c


def build_notebook():
    g = groups()
    main = [q for q in QS if q["id"].startswith("SQL-")]
    dc = Counter(q["difficulty"] for q in main)
    cells = []
    intro = f"""
# SQL Practice Workbook
## Data Science · Machine Learning Engineering · AI Engineering

A hands-on workbook of **{len(main)} practice questions**, **3 capstone projects** and a **{len(g['M14'])}-question final assessment**, all built on one realistic relational dataset (32 tables) and validated on real databases.

| | |
|---|---|
| **Engines** | PostgreSQL 16+ and MySQL 8.0+ (validated on {PG_VER} and {MY_VER}) |
| **Difficulty mix** | Easy {dc['Easy']} · Medium {dc['Medium']} · Hard {dc['Hard']} · Advanced {dc['Advanced']} |
| **Roles** | Data Scientist, ML Engineer, AI Engineer (each with dedicated problem sets) |
| **Dialect labels** | `BOTH` = solvable on both engines (portable SQL, or separate tested versions where syntax differs) · `POSTGRESQL` / `MYSQL` = engine-specific feature |

### How to use this notebook
1. Load the dataset into PostgreSQL or MySQL (see **Setup** below and `README.md`).
2. Work through **Part A: Practice**. Each question gives context, the problem, the tables, the expected output, edge cases and three progressive hints (click to expand). Write your SQL in the cell below the question and run it in `psql`, MySQL Workbench, pgAdmin, or optionally from this notebook.
3. Open **Check your result** to compare row counts and first rows with the reference solution.
4. Read **Part B: Solutions and explanations** only after attempting. Every question links to its solution and back.
5. Track progress with the checklist at the end of each module (or `mark_done("SQL-001")`).

The dataset is deliberately imperfect: duplicates, NULLs, late-arriving data, overlapping periods and stale documents are part of the exercises. Questions say which problems to watch for.
"""
    cells.append(md_cell(intro))
    toc = ["## Table of contents", "", "- [Setup](#setup)", "- [SQL concept reference](#reference)",
           "- [Database schema and relationships](#schema)", "- **Part A: Practice**"]
    for mid, title in MODULES:
        n = len(g[mid])
        toc.append(f"  - [{mid} · {title}](#{mid}) ({n} questions)")
    toc += ["- [Part B: Solutions and explanations](#part-b)", "- [Progress checklist](#progress)"]
    cells.append(md_cell("\n".join(toc)))
    cells.append(md_cell("""<a id="setup"></a>
## Setup

**Required:** PostgreSQL 16+ *or* MySQL 8.0+ with the `sql_workbook` database loaded:

| engine | load the data (from the project folder) |
|---|---|
| PostgreSQL | `createdb sql_workbook` then `psql -d sql_workbook -f setup.sql` |
| MySQL | `mysql -e "CREATE DATABASE sql_workbook CHARACTER SET utf8mb4"` then `mysql sql_workbook < setup_mysql.sql` |

The script ends with a row-count table; compare it with `README.md`.

**Optional:** run queries from this notebook. The helper `sql_practice.py` (in the project folder) works without any database driver for hints, answers and progress tracking. Running SQL from the notebook needs `sqlalchemy`, `pandas` and a driver (`psycopg` or `pymysql`); see `requirements.txt`. The workbook never *requires* this."""))
    cells.append(code_cell("""# Optional helper: works without database drivers (hints, answers, progress).
from sql_practice import question, hint, answer, list_questions, mark_done, progress, connect, run, check

# Optional: connect to your database to use run() and check().
# connect("postgresql+psycopg://postgres:password@localhost:5432/sql_workbook")
# connect("mysql+pymysql://root:password@localhost:3306/sql_workbook")"""))
    cells.append(md_cell('<a id="reference"></a>\n' + REFERENCE))
    cells.append(md_cell('<a id="schema"></a>\n' + schema_markdown()))
    cells.append(md_cell("# Part A: Practice\n\nSolutions are in Part B. Attempt each question first; use the hints in order."))
    for mid, title in MODULES:
        qs = g[mid]
        if not qs:
            continue
        head = [f'<a id="{mid}"></a>', f"## {mid} · {title}", ""]
        if mid in MODULE_INFO:
            head += ["**Learning objectives**"] + [f"- {o}" for o in MODULE_INFO[mid][0]] + [""]
        if mid == "M13":
            head += ["Each capstone combines several modules into one realistic deliverable. Allow about an hour each. "
                     "Pick the variant that matches your target role first, then try the others."]
        if mid == "M14":
            pts = sum(POINTS[q["difficulty"]] for q in qs)
            head += [f"**Rules.** Solve all {len(qs)} questions without looking at Part B. Suggested time: 3–4 hours. "
                     f"Each question is worth Easy {POINTS['Easy']} / Medium {POINTS['Medium']} / Hard {POINTS['Hard']} / "
                     f"Advanced {POINTS['Advanced']} points ({pts} in total). A hint costs 1 point. Score yourself with "
                     "the rubric shown under each solution in Part B.", "",
                     assessment_scoring_table(qs)]
        diffs = Counter(q["difficulty"] for q in qs)
        head += ["", "| ID | Title | Difficulty | Role | Dialect |", "|---|---|---|---|---|"]
        for q in qs:
            head.append(f"| [{q['id']}](#q-{q['id']}) | {q['title']} | {q['difficulty']} | {roles_label(q)} | {q['dialect']} |")
        head.append("")
        head.append(" · ".join(f"{d}: {diffs[d]}" for d in DIFF_ORDER if diffs[d]))
        cells.append(md_cell("\n".join(head)))
        for q in qs:
            cells.append(md_cell(question_markdown(q, assessment=(mid == "M14"))))
            cells.append(code_cell(answer_cell(q)))
        if mid in MODULE_INFO:
            cp = [f"### Checkpoint · {mid}", "", "Before moving on, make sure you can answer these without looking:"]
            cp += [f"- {c}" for c in MODULE_INFO[mid][1]]
            cp += ["", "Track your progress:", ""] + [f"- [ ] {q['id']} {q['title']}" for q in qs]
            cells.append(md_cell("\n".join(cp)))
    cells.append(md_cell('<a id="part-b"></a>\n# Part B: Solutions and explanations\n\n'
                         'Every solution was executed against the dataset during the build. The line under each title says '
                         'on which engines it ran and which cross-checks it passed.'))
    for mid, title in MODULES:
        qs = g[mid]
        if not qs:
            continue
        cells.append(md_cell(f"## Solutions · {mid} · {title}"))
        for q in qs:
            cells.append(md_cell(solution_markdown(q)))
    cells.append(md_cell(progress_markdown(g)))
    nb = {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                                       "language_info": {"name": "python"}},
          "nbformat": 4, "nbformat_minor": 5}
    for i, c in enumerate(nb["cells"]):
        c["id"] = f"cell-{i:04d}"
    path = os.path.join(ROOT, "SQL_Practice_Workbook.ipynb")
    json.dump(nb, open(path, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    return path, len(cells)


SKILL_HINTS = {
    "DS": "Data Science analytics (M06)", "MLE": "ML Engineering datasets (M07)", "AI": "AI Engineering (M08)",
}


def assessment_scoring_table(qs):
    lines = ["| Question | Difficulty | Points | Main skill | If you struggled, revisit |", "|---|---|---:|---|---|"]
    for q in qs:
        tags = [t.strip() for t in q["concepts"].split(",")]
        groups_ = sorted({CONCEPTS[t][0] for t in tags if t in CONCEPTS})
        mods = []
        gm = {"A": "M01", "B": "M02", "C": "M03", "D": "M04", "E": "M05", "F": "M06", "G": "M10", "H": "M09",
              "I": "M11", "J": "M12", "DS": "M06", "MLE": "M07", "AI": "M08"}
        for gname in groups_:
            if gm[gname] not in mods:
                mods.append(gm[gname])
        lines.append(f"| [{q['id']}](#q-{q['id']}) | {q['difficulty']} | {POINTS[q['difficulty']]} | {q['primary']} | "
                     f"{', '.join(mods)} |")
    lines += ["", "**Interpreting your score**", "",
              "| Score | Meaning | Next step |", "|---|---|---|",
              "| ≥ 85% | Interview-ready for most DS/MLE/AI SQL rounds | Do the capstones under time pressure |",
              "| 65–84% | Solid, with gaps | Revisit the modules listed for every question below full marks |",
              "| 45–64% | Foundations in place, advanced patterns shaky | Redo M03, M05 and your role module (M06/M07/M08) |",
              "| < 45% | Fundamentals need work | Restart at M01–M04; focus on grain, NULLs and joins |"]
    return "\n".join(lines)


def progress_markdown(g):
    lines = ['<a id="progress"></a>', "## Progress checklist", "",
             "Tick the boxes as you go (double-click to edit), or call `mark_done(\"SQL-001\")` and `progress()`.", ""]
    for mid, title in MODULES:
        qs = g[mid]
        if not qs:
            continue
        lines.append(f"**{mid} · {title}**")
        lines.append("")
        lines += [f"- [ ] [{q['id']}](#q-{q['id']}) {q['title']} ({q['difficulty']})" for q in qs]
        lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------- solutions.sql
def comment_block(text, width=96):
    plain = re.sub(r"\*\*|`|\[|\]\([^)]*\)", "", text)
    out = []
    for para in plain.split("\n"):
        if not para.strip():
            out.append("--")
            continue
        out += ["-- " + l for l in textwrap.wrap(para, width - 3)] or ["--"]
    return "\n".join(out)


def first_paragraph(text):
    return text.strip().split("\n\n")[0]


def build_solutions():
    g = groups()
    out = ["-- =====================================================================",
           "-- SQL Practice Workbook: solutions to every question",
           "-- Organized by module and question ID. Each entry shows the approach",
           "-- (short; the notebook has the full explanation) and the SQL.",
           "-- Labels: [BOTH] portable, [PostgreSQL] / [MySQL] engine-specific version.",
           "-- This file mixes dialects and is meant for reading. Runnable per-engine",
           "-- files: solutions_postgresql.sql and solutions_mysql.sql.",
           "-- Generated by scripts/build_workbook.py from questions/*.txt.",
           "-- =====================================================================", ""]
    for mid, title in MODULES:
        if not g[mid]:
            continue
        out += ["", "-- #####################################################################",
                f"-- {mid} · {title}", "-- #####################################################################", ""]
        for q in g[mid]:
            out += ["-- ---------------------------------------------------------------------",
                    f"-- {q['id']} · {q['title']}",
                    f"-- Difficulty: {q['difficulty']} | Dialect: {q['dialect']} | Role: {roles_label(q)}",
                    "-- Approach:", comment_block(first_paragraph(q["sections"]["explanation"])),
                    "-- ---------------------------------------------------------------------"]
            for lab, sql in solution_blocks(q) + alternative_blocks(q):
                out += [f"-- [{lab}]", ensure_semicolon(sql.strip()), ""]
    path = os.path.join(ROOT, "solutions.sql")
    open(path, "w", encoding="utf-8").write("\n".join(out) + "\n")
    for engine, name in (("pg", "solutions_postgresql.sql"), ("mysql", "solutions_mysql.sql")):
        open(os.path.join(ROOT, name), "w", encoding="utf-8").write(runnable_solutions(engine))
    return path


def runnable_solutions(engine):
    """One script per engine with every solution that runs there, in order (sandbox objects cleaned up)."""
    label = "PostgreSQL" if engine == "pg" else "MySQL"
    out = [f"-- SQL Practice Workbook: runnable {label} solutions.",
           f"-- Run against the loaded sql_workbook database, e.g.",
           "--   psql -d sql_workbook -f solutions_postgresql.sql" if engine == "pg" else
           "--   mysql sql_workbook < solutions_mysql.sql",
           "-- Exercises that create sandbox objects (sb_*) drop them again.", ""]
    for q in QS:
        s, d = q["sections"], q["dialect"]
        if d == "MYSQL" and engine == "pg":
            if s.get("equivalent_pg"):
                key = "equivalent_pg"
            else:
                continue
        elif d == "POSTGRESQL" and engine == "mysql":
            if s.get("equivalent_mysql"):
                key = "equivalent_mysql"
            else:
                continue
        else:
            key = ("solution_pg" if engine == "pg" else "solution_mysql")
            key = key if s.get(key) else "solution"
        sfx = "pg" if engine == "pg" else "mysql"
        parts = []
        for name in ("setup", "", "verify", "cleanup"):
            if name == "":
                parts.append(s[key])
                continue
            sec = s.get(f"{name}_{sfx}") or s.get(name)
            if sec:
                parts.append(sec)
        out.append(f"-- {q['id']} · {q['title']}")
        out += [ensure_semicolon(p.strip()) for p in parts]
        out.append("")
    return "\n".join(out) + "\n"


# ------------------------------------------------- registry & coverage
def build_registry():
    path = os.path.join(ROOT, "question_registry.csv")
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["question_id", "module", "module_title", "title", "difficulty", "primary_concept",
                    "secondary_concepts", "concept_tags", "roles", "dialect", "estimated_minutes", "tables",
                    "validated_postgresql", "validated_mysql", "engines_identical", "independent_python_check",
                    "validation_status"])
        for q in QS:
            rec = RES.get(q["id"], {})
            runs = rec.get("runs", {})
            pg = any(k.endswith(":pg") and v["ok"] for k, v in runs.items())
            my = any(k.endswith(":mysql") and v["ok"] for k, v in runs.items())
            w.writerow([q["id"], module_of(q), MODULE_TITLE[module_of(q)], q["title"], q["difficulty"], q["primary"],
                        q["secondary"], q["concepts"], roles_label(q), q["dialect"], q["time"],
                        ";".join(parse_tables(q["tables"]).keys()), "yes" if pg else "no", "yes" if my else "no",
                        "yes" if rec.get("engines_match") or rec.get("equivalent_match") else "",
                        "yes" if rec.get("independent_match") else "", rec.get("status", "NOT RUN")])
    return path


def build_coverage():
    main = [q for q in QS if q["id"].startswith("SQL-")]
    by_tag = defaultdict(list)
    for q in QS:
        for t in [x.strip() for x in q["concepts"].split(",") if x.strip()]:
            by_tag[t].append(q)
    lines = ["# Coverage matrix", "",
             "Generated from the question metadata (`concepts:` tags) by `scripts/build_workbook.py`. "
             "Every required concept and every role-specific topic maps to at least one question; the build fails otherwise.", "",
             "## Summary", "", "| Difficulty | Questions | Share | Target |", "|---|---:|---:|---:|"]
    dc = Counter(q["difficulty"] for q in main)
    targets = {"Easy": "20%", "Medium": "35%", "Hard": "30%", "Advanced": "15%"}
    for d in DIFF_ORDER:
        lines.append(f"| {d} | {dc[d]} | {100 * dc[d] / len(main):.1f}% | {targets[d]} |")
    lines += [f"| **Total (practice questions)** | **{len(main)}** | | 150–180 |", "",
              f"Plus {len([q for q in QS if q['id'].startswith('CAP')])} capstones and "
              f"{len([q for q in QS if q['id'].startswith('ASM')])} final-assessment questions.", "",
              "| Dialect label | Questions |", "|---|---:|"]
    for k, v in Counter(q["dialect"] for q in main).items():
        lines.append(f"| {k} | {v} |")
    per_dialect = sum(1 for q in main if q["dialect"] == "BOTH" and q["sections"].get("solution_pg"))
    lines += ["", f"Of the BOTH questions, {per_dialect} need separate PostgreSQL and MySQL versions (both tested); "
              "the rest use one portable query.", "", "### Role x difficulty (practice questions)", "",
              "| Role | " + " | ".join(DIFF_ORDER) + " | Total |", "|---|" + "---:|" * 5]
    for r, name in ROLE_NAMES.items():
        cnt = Counter(q["difficulty"] for q in main if r in [x.strip() for x in q["roles"].split(",")])
        lines.append(f"| {name} | " + " | ".join(str(cnt[d]) for d in DIFF_ORDER) + f" | {sum(cnt.values())} |")
    lines += ["", "Questions tagged with several roles count once per role.", "",
              "### Module x difficulty", "", "| Module | " + " | ".join(DIFF_ORDER) + " | Total |", "|---|" + "---:|" * 5]
    g = groups()
    for mid, title in MODULES:
        cnt = Counter(q["difficulty"] for q in g[mid])
        lines.append(f"| {mid} {title} | " + " | ".join(str(cnt[d]) for d in DIFF_ORDER) + f" | {len(g[mid])} |")
    current = None
    for tag, (grp, desc) in CONCEPTS.items():
        if grp != current:
            current = grp
            lines += ["", f"## {GROUP_NAMES[grp]}", "", "| Concept | # | Questions |", "|---|---:|---|"]
        qs = by_tag.get(tag, [])
        ids = ", ".join(f"{q['id']} ({q['difficulty'][0]})" for q in qs)
        lines.append(f"| {desc} | {len(qs)} | {ids or '**MISSING**'} |")
    missing = [t for t in CONCEPTS if not by_tag.get(t)]
    if missing:
        raise SystemExit(f"coverage incomplete: {missing}")
    path = os.path.join(ROOT, "coverage_matrix.md")
    open(path, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    return path


# ------------------------------------------------------ data dictionary
def column_stats(t):
    rows = list(csv.DictReader(open(os.path.join(ROOT, "data", f"{t['name']}.csv"), encoding="utf-8")))
    stats = {}
    for c in t["columns"]:
        vals = [r[c["name"]] for r in rows]
        non = [v for v in vals if v != ""]
        nulls = len(vals) - len(non)
        ty = c["type"].split("(")[0]
        obs = ""
        if non:
            if ty in ("INT", "BIGINT", "SMALLINT", "DECIMAL") or ty.startswith("DOUBLE"):
                nums = [float(v) for v in non]
                lo, hi = min(nums), max(nums)
                fmt = (lambda x: f"{x:,.0f}") if ty in ("INT", "BIGINT", "SMALLINT") else (lambda x: f"{x:,.4g}")
                obs = f"{fmt(lo)} … {fmt(hi)}"
            elif ty in ("TIMESTAMP", "DATE"):
                obs = f"{min(non)[:10]} … {max(non)[:10]}"
            elif ty == "BOOLEAN":
                obs = f"true {sum(1 for v in non if v == 'true'):,} / false {sum(1 for v in non if v == 'false'):,}"
            elif ty == "JSON":
                obs = "JSON object/array"
            else:
                d = Counter(non)
                obs = f"{len(d):,} distinct" + (": " + ", ".join(f"`{k}`" for k, _ in d.most_common(6)) if len(d) <= 8 else "")
        stats[c["name"]] = (f"{100 * nulls / len(vals):.1f}%" if vals else "", obs)
    return len(rows), stats


def build_dictionary():
    counts = table_counts()
    lines = ["# Dataset dictionary", "",
             "**Lumen Analytics**: a fictional SaaS data platform with AI features. 32 tables in five domains, "
             f"{sum(counts.values()):,} rows in total. Generated deterministically by `scripts/generate_data.py` "
             "(seed 20250701, standard library only). This document is generated from `scripts/schema.py` and the CSV "
             "files by `scripts/build_workbook.py`, so it always matches the setup scripts.", "",
             "## Conventions", "",
             "- **Time:** all timestamps are UTC without a time-zone offset (`TIMESTAMP` in PostgreSQL, `DATETIME` in MySQL). "
             "The data covers 2023-02 to 2025-06-30; **\"today\" is 2025-07-01**. Questions use fixed dates instead of "
             "`CURRENT_DATE` so that results are reproducible.",
             "- **NULL** means unknown or not applicable, as documented per column. The data never contains empty strings. "
             "In the CSV files an empty field is NULL.",
             "- **Booleans:** `BOOLEAN` in both engines (MySQL stores TINYINT(1): TRUE = 1).",
             "- **JSON:** `JSONB` in PostgreSQL, `JSON` in MySQL.",
             "- **Money:** USD, `DECIMAL`. **Tokens:** integer counts. **Latency:** milliseconds.",
             "- **Identifiers:** surrogate integer keys; IDs of time-ordered entities increase with their timestamp.",
             "- **Intentional imperfections** are documented below under each table and in the summary at the end. "
             "They never violate a declared PRIMARY KEY, UNIQUE, FOREIGN KEY or CHECK constraint.", "",
             "## Type mapping", "", "| Neutral type | PostgreSQL | MySQL |", "|---|---|---|",
             "| TIMESTAMP | TIMESTAMP | DATETIME |", "| JSON | JSONB | JSON |",
             "| BOOLEAN | BOOLEAN | BOOLEAN (TINYINT(1)) |", "| DOUBLE PRECISION | DOUBLE PRECISION | DOUBLE |",
             "| DECIMAL(p,s), INT, BIGINT, SMALLINT, VARCHAR(n), CHAR(n), TEXT, DATE | same | same |", "",
             "## Entity-relationship diagram", "", "```mermaid", mermaid_er(), "```", "",
             "## Tables", ""]
    dom = defaultdict(list)
    for t in TABLES:
        dom[t["domain"]].append(t)
    for d, ts in dom.items():
        lines.append(f"- **{d}:** " + ", ".join(f"[`{t['name']}`](#{t['name'].replace('_', '-')})" for t in ts))
    lines.append("")
    issues = []
    for t in TABLES:
        n, stats = column_stats(t)
        lines += [f"### {t['name']}", "", t["desc"], "",
                  f"- **Grain:** {t['grain']}", f"- **Rows:** {n:,}",
                  f"- **Primary key:** ({', '.join(t['pk'])})"]
        if t["fks"]:
            lines.append("- **Foreign keys:** " + "; ".join(f"({', '.join(c)}) → {r}({', '.join(rc)})" for c, r, rc in t["fks"]))
        if t["uniques"]:
            lines.append("- **Unique:** " + "; ".join(f"({', '.join(u)})" for u in t["uniques"]))
        if t["checks"]:
            lines.append("- **Checks:** " + "; ".join(f"`{c}`" for c in t["checks"]))
        idx = [f"ix_{t['name']}_{'_'.join(i)} ({', '.join(i)})" for i in t["indexes"]]
        lines.append("- **Secondary indexes:** " + ("; ".join(idx) if idx else "none (primary/unique keys only)"))
        lines += ["", "| Column | PostgreSQL type | MySQL type | Null? | Description | Units / allowed values | Observed (non-NULL) | NULL % |",
                  "|---|---|---|---|---|---|---|---:|"]
        for c in t["columns"]:
            nullp, obs = stats[c["name"]]
            lines.append(f"| `{c['name']}` | {engine_type(c['type'], 'pg')} | {engine_type(c['type'], 'mysql')} | "
                         f"{'NULL' if c['null'] else 'NOT NULL'} | {c['desc'].replace('|', '/')} | {c['range'] or ''} | {obs} | {nullp} |")
        if t["rules"]:
            lines += ["", "**Business rules and notes**", ""] + [f"- {r}" for r in t["rules"]]
            issues += [f"- `{t['name']}`: {r.replace('INTENTIONAL DATA-QUALITY ISSUE: ', '')}" for r in t["rules"] if "INTENTIONAL" in r]
        lines.append("")
    lines += ["## Intentional data-quality issues (summary)", "",
              "These exist on purpose so that questions can teach detection and handling. `scripts/test_setup.py` asserts "
              "that each one is present.", ""] + issues
    lines += ["", "## Data-generation assumptions", "", GENERATION_NOTES]
    path = os.path.join(ROOT, "dataset_dictionary.md")
    open(path, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    return path


GENERATION_NOTES = """
- **Determinism.** One `random.Random(20250701)` drives every draw, and only lists and dicts are iterated (never sets), so the output is byte-identical on every run. A built-in integrity check refuses to write data that would violate a PK, UNIQUE or FK constraint.
- **Organizations (200).** About 22 accounts predate 2024. Later sign-ups follow a growth curve (more recent accounts are more frequent). Segment mix SMB 60% / Mid-Market 30% / Enterprise 10%. About 9% are subsidiaries, and a few hierarchies are 3 levels deep. Two pairs of different companies share a name.
- **Subscriptions.** Each organization goes through a sequence of periods (mean length ≈ 260 days). Each period ends with an upgrade, downgrade, renewal-as-switch or churn. 30% of churned organizations come back after 1–4 months. Legacy-plan periods were migrated during 2024. MRR = seats × list price × (1 − annual discount if billed annually).
- **Users.** 2–34 users per organization depending on the segment. Users follow one of four activity archetypes (dormant, casual, regular, power), with an onboarding burst in the first 14 days and a lifetime after which they stop using the product (bounded by their organization's churn). 26 people registered a second account with a differently formatted e-mail.
- **Sessions and events.** Sessions are Poisson-distributed per week by archetype, with fewer on weekends and a daytime-weighted hour. Each session contains a login (70%) and 1–3 product events. Checkout sessions precede web orders, and abandoned checkout funnels are added. Server-side `purchase` events are emitted for completed and refunded orders. 1.5% of client events are duplicated.
- **Experiments.** Users are assigned at their first in-window session (sign-up time for `onboarding_checklist`). For purchase experiments, conversion inside the 14-day window is controlled explicitly (base 22%; `checkout_one_page` treatment +8 points, `treatment_b` +2.5, Enterprise users 9%), and organic orders are suppressed inside the window. `onboarding_checklist` is deliberately assigned 65/35 (SRM).
- **Orders and payments.** Buyers place orders during their sessions; sales-channel orders get negotiated prices. Status mix ≈ 85% completed, 8% refunded, 7% canceled, plus pending for recent orders. 12% of paid orders have 1–2 failed payment attempts first. A few large enterprise implementation deals create outliers.
- **Support tickets.** Ticket volume scales with organization size, with a spike before churn. First-response and resolution times are log-normal by priority. CSAT is answered for ≈ 45% of resolved tickets and is lower for slow resolutions.
- **ML.** An entity is registered at the user's 3rd session (not before the feature store launched on 2024-09-15). Features are recomputed from the generated sessions, events, tickets and seats every two weeks, so they can be validated from raw data (SQL-105). Labels follow the documented definition exactly (SQL-098). Scores come from a logistic function of the features plus the true label and version-specific noise, so newer versions have a higher AUC. Thresholds are 0.50/0.45/0.40/0.35 for v1–v4.
- **AI.** About 380 knowledge-base documents with 1–5 versions. ≈ 10% of published versions were edited after indexing, 4% were never indexed, and some drafts and old versions remain in the index. Chunk texts are synthetic sentences from per-area vocabularies. Unchanged paragraphs keep their hash across versions, and a standard footer is shared. LLM traffic grows from Oct 2024 to Jun 2025. Model choice changes over time (nimbus-pro from 2025-03-10, orbit-8b for half the copilot traffic from Feb 2025), and so do prompt versions (2-week 50/50 rollouts) and retrieval configs (top-10 reranker from 2025-04-15). Latency is log-normal per model with outliers; there are timeouts, rate limiting for two heavy organizations in May, and an incident on 2025-03-18. Feedback probability depends on prompt version, retrieval config, model, stale retrievals, latency and the citations experiment.
- **Pipelines.** Daily runs for 2025 H1 with random failures and retries, two multi-day outages that match the feature backfill and the stale index, three missing days and one silent partial load.
"""


def build_report():
    rows, fails = [], []
    for q in QS:
        rec = RES.get(q["id"])
        if not rec:
            fails.append(f"- {q['id']}: not validated")
            continue
        if rec["status"] != "PASS":
            fails.append(f"- {q['id']}: " + "; ".join(rec["problems"]))
    main = [q for q in QS if q["id"].startswith("SQL-")]
    both = [q for q in QS if q["dialect"] == "BOTH"]
    eq = sum(1 for q in both if RES.get(q["id"], {}).get("engines_match"))
    none_cmp = sum(1 for q in both if q.get("compare") == "none")
    single = [q for q in QS if q["dialect"] != "BOTH"]
    eq_single = sum(1 for q in single if RES.get(q["id"], {}).get("equivalent_match"))
    indep = sum(1 for q in QS if RES.get(q["id"], {}).get("independent_match"))
    alts = sum(1 for q in QS for k in RES.get(q["id"], {}).get("runs", {}) if k.startswith("alternative"))
    asserts = sum(RES.get(q["id"], {}).get("asserts", 0) for q in QS)
    lines = ["# Validation report", "",
             f"Generated {datetime.now().strftime('%Y-%m-%d %H:%M')} from `validation/results.json`.", "",
             f"- Engines: **{PG_VER}** and **{MY_VER}**.",
             f"- Questions validated: **{sum(1 for q in QS if RES.get(q['id'], {}).get('status') == 'PASS')} / {len(QS)}** "
             f"({len(main)} practice, 3 capstones, {len([q for q in QS if q['id'].startswith('ASM')])} assessment).",
             f"- BOTH questions: {len(both)}; {eq} returned **identical results** on PostgreSQL and MySQL "
             f"(the remaining {len(both) - eq} produce execution plans or engine-specific catalogue output and are only required to run: {none_cmp} EXPLAIN exercises).",
             f"- Engine-specific questions: {len(single)}; {eq_single} have a validated equivalent on the other engine that returns identical results.",
             f"- Alternative solutions executed: {alts} (each must equal the main result).",
             f"- Assertions evaluated: {asserts}. Independent Python re-computations matching SQL: {indep}.",
             "- Additional checks: every result's column names match the documented expected columns; result-returning "
             "questions must return rows; ordered questions must end with ORDER BY.", ""]
    lines += ["## Failures", ""] + (fails or ["None."])
    lines += ["", "## Per-question results", "", "| ID | Status | PostgreSQL rows | MySQL rows | Cross-check |", "|---|---|---:|---:|---|"]
    for q in QS:
        rec = RES.get(q["id"], {})
        runs = rec.get("runs", {})
        pg = runs.get("main:pg", runs.get("equivalent:pg", {})).get("row_count", "")
        my = runs.get("main:mysql", runs.get("equivalent:mysql", {})).get("row_count", "")
        cc = []
        if rec.get("engines_match"):
            cc.append("engines identical")
        if rec.get("equivalent_match"):
            cc.append("equivalent identical")
        if rec.get("independent_match"):
            cc.append("Python re-computation")
        if rec.get("asserts"):
            cc.append(f"{rec['asserts']} assert(s)")
        lines.append(f"| {q['id']} | {rec.get('status', 'NOT RUN')} | {pg} | {my} | {', '.join(cc)} |")
    path = os.path.join(ROOT, "validation", "report.md")
    open(path, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    return path, fails


def build_helper_data():
    os.makedirs(os.path.join(ROOT, "workbook_data"), exist_ok=True)
    data = {"generated_at": datetime.now().isoformat(timespec="seconds"), "engines": ENGINES, "questions": []}
    for q in QS:
        run = ref_run(q)
        data["questions"].append({
            "id": q["id"], "module": module_of(q), "title": q["title"], "difficulty": q["difficulty"],
            "roles": roles_label(q), "dialect": q["dialect"], "time": q["time"], "primary": q["primary"],
            "secondary": q["secondary"], "tables": q["tables"], "columns": q["columns"], "compare": q["compare"],
            "sections": q["sections"],
            "reference": {"columns": run.get("columns") if run else None,
                          "row_count": run.get("row_count") if run else None,
                          "preview": (run.get("preview") or [])[:5] if run else None},
        })
    path = os.path.join(ROOT, "workbook_data", "questions.json")
    json.dump(data, open(path, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    return path


def main():
    missing = [q["id"] for q in QS if q["id"] not in RES]
    if missing:
        raise SystemExit(f"run scripts/validate.py first; not validated: {missing[:10]}")
    print("notebook:", *build_notebook())
    print("solutions:", build_solutions())
    print("registry:", build_registry())
    print("coverage:", build_coverage())
    print("dictionary:", build_dictionary())
    path, fails = build_report()
    print("report:", path, "failures:", len(fails))
    print("helper data:", build_helper_data())


if __name__ == "__main__":
    main()

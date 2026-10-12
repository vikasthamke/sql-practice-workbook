# SQL Practice Workbook: Data Science, ML Engineering and AI Engineering

A hands-on SQL practice system for aspiring **Data Scientists, Machine Learning Engineers and AI Engineers**. It is built around one realistic, deliberately imperfect relational dataset: a fictional SaaS company (*Lumen Analytics*) with product analytics, billing, an ML churn model, and LLM/RAG features.

- **171 practice questions** in 12 modules: 33 Easy, 65 Medium, 50 Hard and 23 Advanced.
- **3 capstone projects** (Data Science, ML Engineering, AI Engineering variants).
- **A 16-question final assessment** with a scoring rubric and a map of skills to revisit.
- Every question has context, a precise problem statement, the tables and columns needed, the expected output, edge cases, **three progressive hints**, a solution, an explanation, common mistakes, a performance note and an interview insight.
- **PostgreSQL 16+ and MySQL 8.0+.** Every solution was executed on real servers (PostgreSQL 18.6 and MySQL 8.4.11). Portable questions return identical results on both. See [Validation](#validation).

Nothing requires a paid service, cloud database, API key or internet connection.

---

## Contents

| File | What it is |
|---|---|
| `SQL_Practice_Workbook.ipynb` | The workbook: setup, SQL reference, schema, **Part A: Practice** (questions, hints, result previews, answer cells), **Part B: Solutions and explanations**, capstones, final assessment, progress checklist |
| `setup.sql` | **PostgreSQL** setup: creates the 32 tables with all keys, constraints and indexes, and loads all data |
| `setup_mysql.sql` | **MySQL** setup: the same tables and rows, with MySQL types |
| `load_csv_postgresql.sql`, `load_csv_mysql.sql` | Alternative setup that bulk-loads `data/*.csv` (`\copy` / `LOAD DATA LOCAL INFILE`) |
| `data/*.csv` | The dataset as CSV (one file per table; an empty field is NULL) |
| `solutions.sql` | Every solution, organized by module and question ID, with the approach in comments (mixed dialects, for reading) |
| `solutions_postgresql.sql`, `solutions_mysql.sql` | Runnable per-engine scripts with every solution that applies to that engine |
| `dataset_dictionary.md` | Every table and column: types per engine, keys, relationships, nullability, units, observed ranges, business rules, intentional data-quality issues and data-generation assumptions |
| `question_registry.csv` | One row per question: ID, module, difficulty, concepts, roles, dialect, tables, validation status |
| `coverage_matrix.md` | Every required SQL concept and role topic mapped to questions; difficulty, role and module breakdowns |
| `sql_practice.py` | Optional notebook helper: `question()`, `hint()`, `answer()`, `list_questions()`, `mark_done()`, `progress()`, and (with drivers) `connect()`, `run()`, `check()` |
| `requirements.txt` | Optional Python packages for running queries from the notebook |
| `validation/report.md`, `validation/results.json` | What was executed, on which engine, with which result |
| `questions/*.txt` | Question sources (the notebook and solution files are generated from them) |
| `scripts/` | Data generator, setup builder, validators and workbook builder (standard library only) |

---

## Who this is for

| Role | Dedicated material |
|---|---|
| **Data Scientist** | MAU and stickiness, cohorts and retention, churn, funnels, A/B tests (lift, z statistic, SRM, segment effects), Pareto, market basket, medians, outliers, correlation, time series (module M06 plus the DS capstone) |
| **ML Engineer** | Class balance, label deduplication and reconstruction, **point-in-time-correct feature joins**, leakage audits, time-based splits, feature missingness, feature validation, latest predictions, precision/recall/F1/AUC/lift, PSI drift, batch-inference inputs, stale features and delayed labels (module M07 plus the MLE capstone) |
| **AI Engineer** | LLM volume, failures, p95 latency, token cost with time-varying prices, prompt economics, anomaly detection, trace/metadata completeness, versioned documents and chunks, stale and duplicate content, hit@k and MRR, acceptance rates, prompt comparisons, RAG ingestion manifests, AI experiments (module M08 plus the AI capstone) |

Modules M01–M05 and M09–M12 build the shared foundations: filtering and NULL logic, aggregation, joins and grain, subqueries and CTEs, window functions, set operations, data-quality checks, DML/DDL and transactions, query performance, and dialect-specific features.

**Prerequisites:** basic SELECT/WHERE/GROUP BY and a working SQL client. The workbook is not beginner-only: about two thirds of the questions are Medium or harder.

---

## Required software

| Need | Options |
|---|---|
| A database (one is enough) | **PostgreSQL 16 or later**, or **MySQL 8.0 or later** (8.0.31+ recommended: INTERSECT/EXCEPT questions need it) |
| A SQL client | `psql`, pgAdmin, DBeaver, MySQL Workbench, the `mysql` CLI, or the notebook (optional) |
| To open the notebook | JupyterLab ≥ 4.1 (renders the ER diagram), Jupyter Notebook, or VS Code |
| Python (optional) | 3.9+, only to use `sql_practice.py`, regenerate the data or re-run validation. No third-party packages are needed for that. |

---

## Database setup

All commands run from the project folder. Each script **drops and recreates** the workbook tables; it touches nothing else.

### PostgreSQL

```bash
createdb sql_workbook
```

```bash
psql -d sql_workbook -f setup.sql
```

Add `-h localhost -U postgres` (or your user) if needed. On Windows, run the same commands from the "SQL Shell (psql)" or a terminal where `psql` is on the PATH. In **pgAdmin**, create the database, open the Query Tool, open `setup.sql` and run it (about 10 MB; it takes a few seconds).

### MySQL

```bash
mysql -u root -p -e "CREATE DATABASE sql_workbook CHARACTER SET utf8mb4"
```

```bash
mysql -u root -p sql_workbook < setup_mysql.sql
```

In **MySQL Workbench**, create the schema, then *File → Run SQL Script…* → `setup_mysql.sql` with default schema `sql_workbook`. Do not paste the 10 MB file into an editor tab.

### Alternative: load the CSV files

```bash
psql -d sql_workbook -f load_csv_postgresql.sql
```

```bash
mysql --local-infile=1 -u root -p sql_workbook < load_csv_mysql.sql
```

The MySQL variant needs `local_infile=ON` on the server (`SET GLOBAL local_infile = 1;` as an admin). Both loaders were tested and produce data identical to the setup scripts.

### Check the load

Both setup scripts end with a row-count query. Expected counts (113,515 rows in total):

| table | rows | table | rows | table | rows |
|---|---:|---|---:|---|---:|
| `ai_feedback` | 1,447 | `llm_request_chunks` | 19,520 | `orders` | 1,560 |
| `document_chunks` | 3,207 | `llm_requests` | 6,808 | `organizations` | 200 |
| `documents` | 556 | `ml_entities` | 754 | `payments` | 1,685 |
| `entity_features` | 10,416 | `model_evaluations` | 90 | `pipeline_runs` | 572 |
| `eval_queries` | 200 | `model_predictions` | 3,771 | `plans` | 6 |
| `events` | 34,278 | `model_versions` | 6 | `product_categories` | 11 |
| `experiment_assignments` | 2,094 | `order_items` | 2,518 | `products` | 36 |
| `experiments` | 6 | `llm_models` | 5 | `prompts` | 9 |
| `llm_pricing` | 7 | `sessions` | 14,449 | `retrieval_configs` | 3 |
| `retrieval_evaluations` | 4,000 | `subscriptions` | 367 | `support_tickets` | 1,359 |
| `training_labels` | 1,793 | `users` | 1,782 | | |

The `events` table (34k rows) is larger than the other activity tables on purpose: retention, funnel and sessionization questions need enough events per user to be meaningful. The whole dataset still loads in a few seconds.

**MySQL time zone tables (one question):** SQL-164 converts to named time zones. If `SELECT CONVERT_TZ('2025-01-01 12:00', 'UTC', 'Europe/Berlin')` returns NULL, load the zone tables (Linux/macOS: `mysql_tzinfo_to_sql /usr/share/zoneinfo | mysql -u root -p mysql`; Windows: the time zone package from dev.mysql.com). PostgreSQL needs nothing.

---

## How to practise

1. Open `SQL_Practice_Workbook.ipynb` and read **Setup**, the **SQL concept reference** and the **schema** section.
2. Work module by module in **Part A**. For each question:
   - read the context, problem, tables and **expected output** (columns, grain, sort order);
   - write your query in the answer cell, or directly in your SQL client;
   - stuck? Open **Hint 1**, then **Hint 2**, then **Hint 3**. They go from direction, to technique, to query structure;
   - open **Check your result** to compare the row count and first rows with the reference result;
   - only then follow **Go to the solution** to Part B and read the explanation, alternatives, common mistakes and interview insight.
3. At the end of each module, answer the **checkpoint** questions and tick the checklist.
4. Do the **capstone** for your target role, then the **final assessment** under time pressure, and score it with the rubric.

**Dates:** "today" in the dataset is **2025-07-01**. Questions use fixed dates instead of `CURRENT_DATE` so results are reproducible.

**Sandbox exercises:** DML/DDL questions (M10, some M11/M12) create tables named `sb_*` and drop them at the end. The main tables are never modified. If you stop halfway, re-run the solution's clean-up statement or simply re-run the setup script.

### Hints and solutions without scrolling

```python
from sql_practice import question, hint, answer, list_questions, mark_done, progress
question("SQL-099"); hint("SQL-099", 1); hint("SQL-099", 2); answer("SQL-099")
list_questions(role="MLE", difficulty="Hard")      # filter by module / role / difficulty / dialect
mark_done("SQL-099"); progress()                   # progress is stored in workbook_data/progress.json
```

These functions use only the Python standard library. Optionally, run queries and check your answers from the notebook (`pip install -r requirements.txt`):

```python
from sql_practice import connect, run, check
connect("postgresql+psycopg://postgres:password@localhost:5432/sql_workbook")   # or mysql+pymysql://...
run(my_sql)               # pandas DataFrame
check("SQL-031", my_sql)  # compares with the reference solution on your database
```

### Suggested paths

| Goal | Path |
|---|---|
| Interview refresher (1–2 weeks) | All Easy/Medium questions of M01–M05, then the Hard ones, then your role module, then the assessment |
| Data Scientist | M01 → M02 → M03 → M05 → M06 → M04 → M09 → CAP-DS → assessment |
| ML Engineer | M01–M05 → M07 → M09 → M10 → M11 → CAP-ML → assessment |
| AI Engineer | M01–M05 → M08 → M12 → M11 → CAP-AI → assessment |

---

## MySQL and PostgreSQL compatibility

Every question is labelled:

- **`BOTH`** (164 practice questions): solvable on both engines. 130 use one portable query. 34 need different syntax for date truncation, durations, JSON paths, string aggregation, upserts and similar; for those the workbook shows **separate PostgreSQL and MySQL versions**, both tested.
- **`POSTGRESQL`** (5 questions) or **`MYSQL`** (2 questions): practise an engine-specific feature (JSONB operators, time zones, full-text search, MERGE, DISTINCT ON/FILTER/generate_series, MySQL FULLTEXT, JSON_TABLE). Each explains why the engines differ; 5 of the 7 include an equivalent for the other engine that returns identical results.

Portable conventions used throughout: half-open timestamp ranges, `TIMESTAMP '...'` literals, `INTERVAL 'n' DAY` arithmetic (standard syntax both engines accept), `CAST(... AS DATE)`, `CAST(x AS DECIMAL(p,s))` before rounding doubles, `100.0 *` to avoid integer division, `CONCAT` only on non-NULL arguments, explicit tie-breakers in every ORDER BY, and lower-case non-reserved aliases.

Differences you will meet (each one is taught in at least one question):

| Topic | PostgreSQL | MySQL |
|---|---|---|
| String comparison | case-sensitive | default `utf8mb4_0900_ai_ci` is case- and accent-insensitive (SQL-009, SQL-136) |
| Integer division | `7/2 = 3` | `7/2 = 3.5000` (SQL-018) |
| `ROUND(double, n)` | not defined, so cast to NUMERIC | works (SQL-014) |
| NULL sort order (ASC) | last | first |
| `CONCAT` with NULL | ignores NULL | returns NULL (SQL-007) |
| Date truncation / durations | `DATE_TRUNC`, `EXTRACT(EPOCH ...)`, `d1 - d2` | `DATE_FORMAT`, `TIMESTAMPDIFF`, `DATEDIFF` |
| FULL OUTER JOIN | yes | emulate (SQL-041) |
| INTERSECT / EXCEPT | yes | 8.0.31+ (SQL-137, SQL-138) |
| LATERAL | yes | 8.0.14+ (SQL-171) |
| Percentiles | `PERCENTILE_CONT/DISC` | window-function workaround (SQL-089, SQL-117) |
| Upsert | `ON CONFLICT`, `MERGE` (15+) | `ON DUPLICATE KEY UPDATE` (SQL-149, SQL-169) |
| JSON | `JSONB`, `->>'key'`, `@>`, `?` | `JSON`, `->>'$.key'`, `JSON_CONTAINS`, `JSON_TABLE` |
| Multi-table UPDATE/DELETE | `UPDATE ... FROM`, `DELETE ... USING` | `UPDATE ... JOIN`, error 1093 on self-references (SQL-146, SQL-147) |
| Transactions and DDL | DDL is transactional | DDL commits implicitly (SQL-148) |
| Reserved words that bite | — | `lines`, `stored` (SQL-043, SQL-098) |
| Time zones | built in | needs time zone tables (SQL-164) |

Minimum versions for the less common MySQL features: CHECK constraints 8.0.16, functional indexes 8.0.13, EXPLAIN ANALYZE 8.0.18, row aliases in `ON DUPLICATE KEY UPDATE` 8.0.19, INTERSECT/EXCEPT 8.0.31. PostgreSQL 16 supports everything used except two items that are explained as optional extras: the B-tree skip scan visible in some PostgreSQL 18 plans (SQL-157), and `WHEN NOT MATCHED BY SOURCE` in MERGE (17+, mentioned in SQL-169, not used).

Execution plans (module M11) differ between engine versions and with statistics; the solutions show the plans observed during validation and explain how to read yours.

---

## Validation

Everything in this workbook was executed, not just written:

- **Database setup** (`scripts/test_setup.py`), on both engines: all 32 tables, every column (name, order, nullability), primary keys, unique keys, foreign keys, CHECK constraints and indexes match `scripts/schema.py`; row counts match the CSV files; per-column fingerprints (sums, lengths, min/max, NULL counts) are **identical on PostgreSQL and MySQL**; 31 checks confirm that the documented intentional data-quality issues are present. The CSV loaders produce the same fingerprints.
- **Questions** (`scripts/validate.py`): all 190 items (171 practice, 3 capstones, 16 assessment) ran successfully on **PostgreSQL 18.6** and **MySQL 8.4.11**:
  - 175 of the 183 `BOTH` items returned **identical results on both engines** (with numeric tolerance for rounding). The other 8 are EXPLAIN exercises whose output is engine-specific by nature; they were executed on both, and assertions on the plan shape were checked against PostgreSQL.
  - 5 of the 7 engine-specific questions have an equivalent for the other engine that returned identical results. The two full-text-search questions have none, because relevance scoring differs by design.
  - 25 alternative solutions (in 14 questions) were executed and matched their main solution; 85 assertions on results passed.
  - Result columns match the documented expected output; result queries return rows; ordered results end with ORDER BY.
  - 15 key results (for example monthly revenue, fan-out, MAU, Pareto, label reconstruction, precision/recall, AUC, latency percentiles, token cost, hit@k/MRR) were **re-computed independently in Python** from the CSV files and matched.
- **Deliverables:** both runnable solution files ran end-to-end on their engine; no sandbox objects were left behind and the dataset fingerprints were unchanged afterwards; the notebook passed `nbformat` validation and executed top to bottom without database drivers; the `sql_practice.py` helper functions were exercised.

**Not verified:**
- PostgreSQL 16/17 and MySQL 8.0.x were not run. Compatibility with those versions is based on documented feature availability; the exact plans in M11 will differ on them.
- MySQL on Windows, and GUI clients (pgAdmin, MySQL Workbench), were not exercised.
- `connect()` / `run()` / `check()` in `sql_practice.py` were not tested against live drivers, because `psycopg` and `pymysql` were not installed in the build environment. Hints, answers and progress tracking were tested.

Re-run the validation yourself (standard library only; uses the `psql` and `mysql` command-line clients):

```bash
export PGHOST=localhost PGPORT=5432 PGUSER=postgres PGDATABASE=sql_workbook
```

```bash
export MYSQL_HOST=127.0.0.1 MYSQL_TCP_PORT=3306 MYSQL_USER=root MYSQL_PWD=secret MYSQL_DATABASE=sql_workbook
```

```bash
python3 scripts/test_setup.py && python3 scripts/validate.py
```

`validate.py --module M07` or `--only SQL-099,SQL-100` validates a subset; `--engines pg` limits the engines.

---

## Regenerating the dataset and the workbook

```bash
python3 scripts/generate_data.py && python3 scripts/build_setup.py
```

```bash
python3 scripts/validate.py && python3 scripts/build_workbook.py
```

The generator is deterministic (fixed seed; byte-identical output on every run) and refuses to write data that violates a declared key or constraint. `build_workbook.py` regenerates the notebook, solution files, registry, coverage matrix, data dictionary and validation report from `questions/*.txt` and the validation results, so all files stay consistent.

---

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `ERROR: function round(double precision, integer) does not exist` | PostgreSQL rounds only NUMERIC; use `ROUND(CAST(x AS NUMERIC), 2)` (SQL-014) |
| `Expression #1 of SELECT list is not in GROUP BY clause` (MySQL 1055) | `ONLY_FULL_GROUP_BY` (default): group by every non-aggregated expression |
| `You can't specify target table ... for update in FROM clause` (MySQL 1093) | wrap the subquery in a derived table (SQL-147) |
| `Can't reopen table` (MySQL 1137) | a TEMPORARY table used twice in one statement; use a CTE (SQL-151) |
| Syntax error near `lines`, `stored`, `rank` (MySQL) | reserved word; rename the alias |
| `INTERSECT`/`EXCEPT` syntax error (MySQL) | needs 8.0.31+; use the EXISTS alternatives shown |
| `CONVERT_TZ` returns NULL | load MySQL time zone tables (see Database setup) |
| `Recursive query aborted after 1001 iterations` | raise `cte_max_recursion_depth` or shorten the date range |
| `GROUP_CONCAT` output cut off | `SET SESSION group_concat_max_len = 100000;` |
| `LOAD DATA LOCAL INFILE` refused | enable `local_infile` on server and client (`--local-infile=1`) |
| `invalid byte sequence for encoding "UTF8"` | run `psql` with UTF-8 client encoding (`SET client_encoding = 'UTF8';` is in the script) |
| Different numbers than the "Check your result" preview | compare definitions first: date boundaries, duplicates, NULL handling, and which rows are excluded |
| Notebook shows `erDiagram` text instead of a diagram | your Jupyter does not render Mermaid; use JupyterLab ≥ 4.1 or read `dataset_dictionary.md` on GitHub/VS Code |

---

## Project structure

```
SQL_Practice_Workbook/
├── SQL_Practice_Workbook.ipynb    workbook (generated)
├── README.md
├── setup.sql / setup_mysql.sql    full setup per engine (generated)
├── load_csv_postgresql.sql / load_csv_mysql.sql
├── solutions.sql / solutions_postgresql.sql / solutions_mysql.sql
├── dataset_dictionary.md / coverage_matrix.md / question_registry.csv
├── requirements.txt / sql_practice.py
├── data/                          32 CSV files
├── questions/                     question sources m01–m14
├── workbook_data/questions.json   data for sql_practice.py
├── validation/                    results.json, report.md
└── scripts/
    ├── schema.py                  single source of truth for tables, constraints, docs
    ├── generate_data.py           deterministic dataset generator
    ├── build_setup.py             setup and CSV loader scripts
    ├── dbrun.py                   runs SQL through psql / mysql CLIs
    ├── test_setup.py              database tests
    ├── questions.py               question parser, concept vocabulary
    ├── validate.py                executes and cross-checks every solution
    ├── independent_checks.py      Python re-computations of key results
    └── build_workbook.py          notebook, solutions, registry, coverage, dictionary, report
```

All companies, people, products, models and documents are fictional. Model names such as `atlas-large` or `nimbus-pro` do not refer to real products.

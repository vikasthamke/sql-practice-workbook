#!/usr/bin/env python3
"""
Test the loaded database(s) against scripts/schema.py and data/*.csv.

  python3 scripts/test_setup.py            # tests every engine that is reachable
  python3 scripts/test_setup.py pg         # PostgreSQL only

Checks
  1. every table/column exists with the documented nullability and order
  2. primary keys, unique constraints, foreign keys, checks and indexes exist
  3. row counts equal the CSV files
  4. per-column fingerprints (sum / char length / min / max / null count) are
     identical on PostgreSQL and MySQL (proves both engines hold the same data)
  5. every documented intentional data-quality issue is actually present
"""
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dbrun import available, run  # noqa: E402
from schema import TABLES  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAIL = []


def check(cond, msg):
    if not cond:
        FAIL.append(msg)
        print("  FAIL", msg)


def catalog(engine):
    if engine == "pg":
        cols = run(engine, """SELECT table_name, column_name, ordinal_position, is_nullable
                               FROM information_schema.columns WHERE table_schema = 'public'
                               ORDER BY table_name, ordinal_position""")[1]
        cons = run(engine, """SELECT table_name, constraint_type, COUNT(*) FROM information_schema.table_constraints
                               WHERE table_schema = 'public' AND constraint_name NOT LIKE '%_not_null'
                               GROUP BY table_name, constraint_type""")[1]
        idx = run(engine, "SELECT tablename, indexname FROM pg_indexes WHERE schemaname = 'public'")[1]
    else:
        cols = run(engine, """SELECT table_name, column_name, ordinal_position, is_nullable
                               FROM information_schema.columns WHERE table_schema = DATABASE()
                               ORDER BY table_name, ordinal_position""")[1]
        cons = run(engine, """SELECT table_name, constraint_type, COUNT(*) FROM information_schema.table_constraints
                               WHERE table_schema = DATABASE() GROUP BY table_name, constraint_type""")[1]
        idx = run(engine, """SELECT DISTINCT table_name, index_name FROM information_schema.statistics
                              WHERE table_schema = DATABASE()""")[1]
    return cols, cons, idx


def test_catalog(engine):
    print(f"[{engine}] catalog")
    cols, cons, idx = catalog(engine)
    by_table = {}
    for t, c, pos, nullable in cols:
        by_table.setdefault(t, []).append((c, nullable))
    cons_map = {(t, ty): int(n) for t, ty, n in cons}
    idx_set = {(t, i.lower()) for t, i in idx}
    check(len(by_table) == len(TABLES), f"{engine}: expected {len(TABLES)} tables, found {len(by_table)}")
    for t in TABLES:
        got = by_table.get(t["name"])
        if not got:
            check(False, f"{engine}: table {t['name']} missing")
            continue
        exp = [(c["name"], "YES" if c["null"] else "NO") for c in t["columns"]]
        check(got == exp, f"{engine}: column mismatch in {t['name']}: {got} != {exp}")
        check(cons_map.get((t["name"], "PRIMARY KEY")) == 1, f"{engine}: PK missing on {t['name']}")
        check(cons_map.get((t["name"], "FOREIGN KEY"), 0) == len(t["fks"]), f"{engine}: FK count on {t['name']}")
        check(cons_map.get((t["name"], "UNIQUE"), 0) == len(t["uniques"]), f"{engine}: UNIQUE count on {t['name']}")
        check(cons_map.get((t["name"], "CHECK"), 0) == len(t["checks"]), f"{engine}: CHECK count on {t['name']}")
        for icols in t["indexes"]:
            name = f"ix_{t['name']}_{'_'.join(icols)}"
            check((t["name"], name) in idx_set, f"{engine}: index {name} missing")


def test_counts(engine):
    print(f"[{engine}] row counts vs CSV")
    sql = "\nUNION ALL ".join(f"SELECT '{t['name']}', COUNT(*) FROM {t['name']}" for t in TABLES)
    got = {r[0]: int(r[1]) for r in run(engine, sql)[1]}
    for t in TABLES:
        with open(os.path.join(ROOT, "data", f"{t['name']}.csv"), encoding="utf-8") as fh:
            n = sum(1 for _ in csv.reader(fh)) - 1
        check(got[t["name"]] == n, f"{engine}: {t['name']} has {got[t['name']]} rows, CSV has {n}")


def fingerprint_sql(t, engine):
    parts = []
    for c in t["columns"]:
        n, ty = c["name"], c["type"].split("(")[0]
        nulls = f"SUM(CASE WHEN {n} IS NULL THEN 1 ELSE 0 END)"
        if ty in ("INT", "BIGINT", "SMALLINT", "DECIMAL"):
            parts.append(f"CAST(SUM({n}) AS DECIMAL(20,4))")
        elif ty.startswith("DOUBLE"):
            parts.append(f"CAST(ROUND(CAST(SUM({n}) AS DECIMAL(30,6)), 3) AS DECIMAL(30,3))")
        elif ty == "BOOLEAN":
            parts.append(f"SUM(CASE WHEN {n} THEN 1 ELSE 0 END)")
        elif ty in ("TIMESTAMP", "DATE"):
            parts.append(f"CAST(MIN({n}) AS CHAR(19))" if engine == "mysql" else f"CAST(MIN({n}) AS VARCHAR(19))")
            parts.append(f"CAST(MAX({n}) AS CHAR(19))" if engine == "mysql" else f"CAST(MAX({n}) AS VARCHAR(19))")
        elif ty == "JSON":
            parts.append(f"COUNT({n})")
        else:
            parts.append(f"SUM(CHAR_LENGTH({n}))")
        parts.append(nulls)
    return f"SELECT {', '.join(parts)} FROM {t['name']}"


def test_fingerprints():
    print("[pg vs mysql] per-column fingerprints")
    for t in TABLES:
        a = run("pg", fingerprint_sql(t, "pg"))[1][0]
        b = run("mysql", fingerprint_sql(t, "mysql"))[1][0]
        check(a == b, f"fingerprint differs for {t['name']}:\n    pg={a}\n    my={b}")


DQ_CHECKS = [  # description, portable SQL returning one count, minimum expected
    ("duplicate user accounts (normalized e-mail)",
     "SELECT COUNT(*) FROM (SELECT LOWER(TRIM(email)) e FROM users GROUP BY LOWER(TRIM(email)) HAVING COUNT(*) > 1) d", 10),
    ("overlapping subscriptions",
     "SELECT COUNT(*) FROM subscriptions a JOIN subscriptions b ON a.org_id = b.org_id AND a.subscription_id < b.subscription_id "
     "AND b.started_at < COALESCE(a.ended_at, TIMESTAMP '2999-01-01 00:00:00') AND a.started_at < COALESCE(b.ended_at, TIMESTAMP '2999-01-01 00:00:00')", 3),
    ("order header totals not matching lines",
     "SELECT COUNT(*) FROM orders o JOIN (SELECT order_id, SUM(quantity*unit_price - discount_amount) s FROM order_items GROUP BY order_id) i "
     "ON i.order_id = o.order_id WHERE ABS(o.order_total - i.s) > 0.005", 10),
    ("completed orders without payments",
     "SELECT COUNT(*) FROM orders o WHERE o.status = 'completed' AND NOT EXISTS (SELECT 1 FROM payments p WHERE p.order_id = o.order_id)", 5),
    ("orders billed to a different org than the user's",
     "SELECT COUNT(*) FROM orders o JOIN users u ON u.user_id = o.user_id WHERE o.org_id <> u.org_id", 3),
    ("duplicate client events",
     "SELECT COUNT(*) FROM (SELECT user_id, session_id, event_name, event_ts FROM events WHERE session_id IS NOT NULL "
     "GROUP BY user_id, session_id, event_name, event_ts HAVING COUNT(*) > 1) d", 100),
    ("duplicate label rows", "SELECT COUNT(*) FROM (SELECT entity_id, observation_date FROM training_labels GROUP BY entity_id, observation_date HAVING COUNT(*) > 1) d", 5),
    ("conflicting duplicate labels", "SELECT COUNT(*) FROM (SELECT entity_id, observation_date FROM training_labels GROUP BY entity_id, observation_date HAVING COUNT(DISTINCT label_value) > 1) d", 2),
    ("backfilled feature rows", "SELECT COUNT(*) FROM entity_features WHERE feature_source = 'backfill'", 100),
    ("late-arriving feature rows (> 1 day)", "SELECT COUNT(*) FROM entity_features WHERE feature_source = 'batch' AND ingested_at > as_of_ts + INTERVAL '1' DAY", 50),
    ("NULL feature values", "SELECT COUNT(*) FROM entity_features WHERE sessions_7d IS NULL OR events_28d IS NULL", 20),
    ("missing feature snapshot rows",
     "SELECT COUNT(*) FROM ml_entities e JOIN (SELECT DISTINCT as_of_ts FROM entity_features) s ON s.as_of_ts >= e.registered_at "
     "WHERE NOT EXISTS (SELECT 1 FROM entity_features f WHERE f.entity_id = e.entity_id AND f.as_of_ts = s.as_of_ts)", 50),
    ("predictions logged with a not-yet-ingested snapshot",
     "SELECT COUNT(*) FROM model_predictions p JOIN entity_features f ON f.entity_id = p.entity_id AND f.as_of_ts = p.feature_as_of_ts WHERE f.ingested_at > p.predicted_at", 10),
    ("re-run predictions (same entity, model, day)",
     "SELECT COUNT(*) FROM (SELECT entity_id, model_version_id, CAST(predicted_at AS DATE) d FROM model_predictions GROUP BY entity_id, model_version_id, CAST(predicted_at AS DATE) HAVING COUNT(*) > 1) x", 50),
    ("NULL scores", "SELECT COUNT(*) FROM model_predictions WHERE score IS NULL", 5),
    ("NULL (pending) labels", "SELECT COUNT(*) FROM training_labels WHERE label_value IS NULL", 50),
    ("test accounts", "SELECT COUNT(*) FROM ml_entities WHERE is_test_account = TRUE", 10),
    ("stale published documents", "SELECT COUNT(*) FROM documents WHERE status = 'published' AND (last_indexed_at IS NULL OR last_indexed_at < updated_at)", 10),
    ("draft versions present in the index", "SELECT COUNT(DISTINCT d.document_id) FROM documents d JOIN document_chunks c ON c.document_id = d.document_id WHERE d.status = 'draft'", 1),
    ("chunks of archived versions still indexed", "SELECT COUNT(*) FROM document_chunks c JOIN documents d ON d.document_id = c.document_id WHERE d.status = 'archived'", 10),
    ("boilerplate duplicate chunks", "SELECT MAX(n) FROM (SELECT content_hash, COUNT(*) n FROM document_chunks GROUP BY content_hash) x", 10),
    ("failed embeddings", "SELECT COUNT(*) FROM document_chunks WHERE embedding_model IS NULL", 5),
    ("requests without trace_id", "SELECT COUNT(*) FROM llm_requests WHERE trace_id IS NULL", 50),
    ("nimbus-pro incident 2025-03-18",
     "SELECT COUNT(*) FROM llm_requests WHERE model_name = 'nimbus-pro' AND requested_at >= '2025-03-18' AND requested_at < '2025-03-19' AND status <> 'success'", 5),
    ("extreme token requests", "SELECT COUNT(*) FROM llm_requests WHERE input_tokens > 50000", 3),
    ("feedback changed (multiple rows per request)", "SELECT COUNT(*) FROM (SELECT request_id FROM ai_feedback GROUP BY request_id HAVING COUNT(*) > 1) x", 20),
    ("unjudged retrieval rows", "SELECT COUNT(*) FROM retrieval_evaluations WHERE is_relevant IS NULL", 30),
    ("events_ingest dates without any run",
     "SELECT 181 - COUNT(DISTINCT run_date) FROM pipeline_runs WHERE pipeline_name = 'events_ingest'", 2),
    ("users with NULL marketing_opt_in", "SELECT COUNT(*) FROM users WHERE marketing_opt_in IS NULL", 100),
    ("soft-deleted organizations", "SELECT COUNT(*) FROM organizations WHERE is_deleted = TRUE", 3),
    ("3-level org hierarchy", "SELECT COUNT(*) FROM organizations c JOIN organizations p ON p.org_id = c.parent_org_id WHERE p.parent_org_id IS NOT NULL", 1),
]


def test_data_quality(engine):
    print(f"[{engine}] intentional data-quality issues are present")
    for desc, sql, minimum in DQ_CHECKS:
        try:
            n = int(run(engine, sql)[1][0][0])
        except Exception as e:  # noqa: BLE001
            check(False, f"{engine}: DQ query failed ({desc}): {e}")
            continue
        check(n >= minimum, f"{engine}: expected >= {minimum} for '{desc}', got {n}")
        print(f"    {desc:<55} {n}")


def main():
    engines = sys.argv[1:] or [e for e in ("pg", "mysql") if available(e)]
    if not engines:
        print("No database reachable. See README 'Validation'.")
        sys.exit(2)
    for e in engines:
        test_catalog(e)
        test_counts(e)
        test_data_quality(e)
    if "pg" in engines and "mysql" in engines:
        test_fingerprints()
    print("\nRESULT:", "PASS" if not FAIL else f"FAIL ({len(FAIL)} problems)")
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()

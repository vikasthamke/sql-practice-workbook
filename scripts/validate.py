#!/usr/bin/env python3
"""
Validate every question against the real databases.

  python3 scripts/validate.py                    # all questions, all reachable engines
  python3 scripts/validate.py --module M05       # one module (file prefix m05_)
  python3 scripts/validate.py --only SQL-012,SQL-013
  python3 scripts/validate.py --engines pg       # PostgreSQL only

For every question it
  * lints the metadata (tables/columns exist in schema.py, concept tags known, ...)
  * executes the solution on each engine its dialect declares
      BOTH        -> PostgreSQL and MySQL (portable SQL or per-dialect versions)
      POSTGRESQL  -> PostgreSQL only (plus an optional MySQL equivalent)
      MYSQL       -> MySQL only      (plus an optional PostgreSQL equivalent)
  * checks the result columns match the 'columns:' header
  * compares PostgreSQL and MySQL results for BOTH questions
  * runs @alternative solutions and requires the same result
  * evaluates @assert expressions and independent Python re-computations
Results go to validation/results.json and validation/report.md.
"""
import argparse
import json
import math
import os
import re
import sys
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dbrun import SQLError, available, run  # noqa: E402
from questions import lint, load_all  # noqa: E402
from schema import TABLES  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VDIR = os.path.join(ROOT, "validation")
RESULTS = os.path.join(VDIR, "results.json")
SCHEMA_TABLES = {t["name"]: [c["name"] for c in t["columns"]] for t in TABLES}

try:
    import independent_checks  # noqa: E402
    INDEPENDENT = independent_checks.CHECKS
except Exception as e:  # noqa: BLE001
    print("warning: independent checks not loaded:", e)
    INDEPENDENT = {}


# ---------------------------------------------------------------- compare
DATE0 = re.compile(r"^\d{4}-\d{2}-\d{2} 00:00:00$")


def norm(v):
    if v is None:
        return None
    if v in ("t", "true"):
        return "1"
    if v in ("f", "false"):
        return "0"
    if DATE0.match(v):
        return v[:10]
    return v


def as_num(v):
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    if math.isnan(f):
        return None
    if "e" in v.lower():
        dec = 15
    else:
        dec = len(v.split(".")[1]) if "." in v else 0
    return f, dec


def val_eq(a, b):
    a, b = norm(a), norm(b)
    if a is None or b is None:
        return a is None and b is None
    if a == b:
        return True
    na, nb = as_num(a), as_num(b)
    if na and nb:
        (fa, da), (fb, db) = na, nb
        d = min(da, db)
        tol = 1e-9 * max(1.0, abs(fa))
        if d > 0:
            tol = max(tol, 1.0001 * 10 ** (-d))
        return abs(fa - fb) <= tol
    return False


def sort_key(row):
    out = []
    for v in row:
        v = norm(v)
        n = as_num(v) if v is not None else None
        if v is None:
            out.append((0, ""))
        elif n:
            out.append((1, f"{round(n[0], 2):+020.2f}"))
        else:
            out.append((2, v))
    return out


def compare(rows_a, rows_b, ordered):
    if len(rows_a) != len(rows_b):
        return f"row count {len(rows_a)} vs {len(rows_b)}"
    if not ordered:
        rows_a = sorted(rows_a, key=sort_key)
        rows_b = sorted(rows_b, key=sort_key)
    for i, (ra, rb) in enumerate(zip(rows_a, rows_b)):
        if len(ra) != len(rb):
            return f"column count differs at row {i}"
        for j, (x, y) in enumerate(zip(ra, rb)):
            if not val_eq(x, y):
                return f"row {i} col {j}: {x!r} vs {y!r}"
    return None


# -------------------------------------------------------------- execution
def section_for(q, name, engine):
    """Engine-specific section (e.g. verify_pg) if present, else the shared one."""
    s = q["sections"]
    return s.get(f"{name}_{'pg' if engine == 'pg' else 'mysql'}") or s.get(name)


def script_for(q, key, engine):
    s = q["sections"]
    parts = []
    if section_for(q, "setup", engine):
        parts.append(section_for(q, "setup", engine))
    parts.append(s[key])
    if section_for(q, "verify", engine):
        parts.append(section_for(q, "verify", engine))
    return ";\n".join(p.rstrip().rstrip(";") for p in parts)


def has_verify(q):
    s = q["sections"]
    return bool(s.get("verify") or s.get("verify_pg") or s.get("verify_mysql"))


def cleanup(q, engine):
    c = section_for(q, "cleanup", engine)
    if c:
        try:
            run(engine, c + ";\nSELECT 1")
        except SQLError:
            pass


def plan(q, engines):
    """List of (label, engine, section_key, kind) to execute."""
    s, d, out = q["sections"], q["dialect"], []

    def main_key(engine):
        k = "solution_pg" if engine == "pg" else "solution_mysql"
        return k if s.get(k) else ("solution" if s.get("solution") else None)

    if d == "BOTH":
        for e in ("pg", "mysql"):
            out.append(("main", e, main_key(e), "main"))
    elif d == "POSTGRESQL":
        out.append(("main", "pg", main_key("pg"), "main"))
        if s.get("equivalent_mysql"):
            out.append(("equivalent", "mysql", "equivalent_mysql", "equivalent"))
    else:
        out.append(("main", "mysql", main_key("mysql"), "main"))
        if s.get("equivalent_pg"):
            out.append(("equivalent", "pg", "equivalent_pg", "equivalent"))
    for k in ("alternative", "alternative_pg", "alternative_mysql"):
        if s.get(k):
            engs = {"alternative": ["pg", "mysql"] if d == "BOTH" else (["pg"] if d == "POSTGRESQL" else ["mysql"]),
                    "alternative_pg": ["pg"], "alternative_mysql": ["mysql"]}[k]
            for e in engs:
                out.append((k, e, k, "alternative"))
    return [p for p in out if p[1] in engines and p[2]]


def validate_question(q, engines):
    rec = {"id": q["id"], "title": q.get("title"), "dialect": q.get("dialect"), "runs": {},
           "problems": [], "checked_at": datetime.now().isoformat(timespec="seconds")}
    rec["problems"].extend("lint: " + e for e in lint(q, SCHEMA_TABLES))
    expected_cols = [c.strip().lower() for c in q.get("columns", "").split(",") if c.strip()]
    ordered = q.get("compare") == "ordered"
    results = {}
    for label, engine, key, kind in plan(q, engines):
        cleanup(q, engine)
        t0 = time.time()
        try:
            cols, rows = run(engine, script_for(q, key, engine))
            ok, err = True, None
        except SQLError as ex:
            cols, rows, ok, err = [], [], False, str(ex)
        ms = int((time.time() - t0) * 1000)
        cleanup(q, engine)
        rid = f"{label}:{engine}"
        rec["runs"][rid] = {"ok": ok, "error": err, "ms": ms, "columns": cols,
                            "row_count": len(rows), "preview": rows[:12]}
        if not ok:
            rec["problems"].append(f"{rid} failed: {err[:400]}")
            continue
        results[(label, engine)] = (cols, rows)
        if kind == "main" and not rows and not has_verify(q) and q.get("compare") != "none":
            rec["problems"].append(f"{rid} returned no rows (a practice query should return data)")
        if q.get("compare") != "none" and kind in ("main", "equivalent") and not (engine == "mysql" and not rows):
            if [c.lower() for c in cols] != expected_cols:
                rec["problems"].append(f"{rid} columns {cols} != expected {expected_cols}")
        if kind == "main" and q.get("compare") == "ordered" and not has_verify(q):
            sql = re.sub(r"--[^\n]*", "", q["sections"][key].split(";")[-1] or q["sections"][key])
            prev = None
            while prev != sql:
                prev, sql = sql, re.sub(r"\([^()]*\)", "", sql)
            if not re.search(r"order\s+by", sql, re.I) and len(rows) > 1:
                rec["problems"].append(f"{rid}: compare=ordered but the final SELECT has no ORDER BY")
    # cross-engine comparison
    if q.get("compare") != "none":
        if ("main", "pg") in results and ("main", "mysql") in results:
            diff = compare(results[("main", "pg")][1], results[("main", "mysql")][1], ordered)
            rec["engines_match"] = diff is None
            if diff:
                rec["problems"].append(f"pg vs mysql differ: {diff}")
        for (label, engine), (cols, rows) in results.items():
            if label.startswith("alternative") and ("main", engine) in results:
                diff = compare(results[("main", engine)][1], rows, ordered)
                if diff:
                    rec["problems"].append(f"{label}:{engine} differs from main: {diff}")
            if label == "equivalent":
                other = "pg" if engine == "mysql" else "mysql"
                if ("main", other) in results:
                    diff = compare(results[("main", other)][1], rows, ordered)
                    rec["equivalent_match"] = diff is None
                    if diff:
                        rec["problems"].append(f"equivalent ({engine}) differs from main: {diff}")
    # assertions on the reference result
    ref_engine = "mysql" if q["dialect"] == "MYSQL" else "pg"
    ref = results.get(("main", ref_engine))
    if ref is None and results:
        ref = next(v for k, v in results.items() if k[0] == "main") if any(k[0] == "main" for k in results) else None
    if q["sections"].get("assert") and ref:
        cols, rows = ref
        for line in [ln.strip() for ln in q["sections"]["assert"].split("\n") if ln.strip()]:
            try:
                env = {"rows": rows, "cols": cols, "num": lambda v: None if v is None else float(v),
                       "col": lambda name: [r[[c.lower() for c in cols].index(name)] for r in rows],
                       "__builtins__": {"len": len, "all": all, "any": any, "sum": sum, "abs": abs,
                                        "min": min, "max": max, "set": set, "sorted": sorted,
                                        "float": float, "int": int, "round": round, "list": list,
                                        "zip": zip, "range": range}}
                if not eval(line, env):
                    rec["problems"].append(f"assert failed: {line}")
            except Exception as ex:  # noqa: BLE001
                rec["problems"].append(f"assert error: {line}: {ex}")
        rec["asserts"] = len([ln for ln in q["sections"]["assert"].split("\n") if ln.strip()])
    if q["id"] in INDEPENDENT and ref:
        try:
            exp_rows = INDEPENDENT[q["id"]]()
            diff = compare([[None if v is None else str(v) for v in r] for r in exp_rows], ref[1], ordered)
            rec["independent_match"] = diff is None
            if diff:
                rec["problems"].append(f"independent Python check differs: {diff}")
        except Exception as ex:  # noqa: BLE001
            rec["problems"].append(f"independent check error: {ex}")
    rec["status"] = "PASS" if not rec["problems"] else "FAIL"
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--module")
    ap.add_argument("--only")
    ap.add_argument("--engines")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()
    engines = a.engines.split(",") if a.engines else [e for e in ("pg", "mysql") if available(e)]
    if not engines:
        print("No database reachable; see README 'Validation'.")
        sys.exit(2)
    qs = load_all(prefix=a.module.lower() + "_" if a.module else None)
    ids = [q["id"] for q in load_all()]
    dup = sorted({i for i in ids if ids.count(i) > 1})
    if dup:
        print("DUPLICATE IDS:", dup)
        sys.exit(1)
    if a.only:
        want = set(a.only.split(","))
        qs = [q for q in qs if q["id"] in want]
    os.makedirs(VDIR, exist_ok=True)
    store = json.load(open(RESULTS)) if os.path.exists(RESULTS) else {}
    store.setdefault("questions", {})
    store.setdefault("engines", {})
    for e in engines:
        try:
            store["engines"][e] = run(e, "SELECT version()")[1][0][0]
        except SQLError:
            pass
    fails = 0
    t0 = time.time()
    for q in qs:
        rec = validate_question(q, engines)
        rec["engines_tested"] = engines
        store["questions"][q["id"]] = rec
        if rec["status"] != "PASS":
            fails += 1
            print(f"FAIL {q['id']} {q.get('title')}")
            for p in rec["problems"]:
                print("     -", p[:600])
        elif not a.quiet:
            rc = {k: v["row_count"] for k, v in rec["runs"].items()}
            print(f"ok   {q['id']} {q.get('title')[:60]:<60} {rc}")
    # drop results of questions that no longer exist
    for k in list(store["questions"]):
        if k not in ids:
            del store["questions"][k]
    store["generated_at"] = datetime.now().isoformat(timespec="seconds")
    json.dump(store, open(RESULTS, "w"), indent=1, ensure_ascii=False)
    print(f"\n{len(qs) - fails}/{len(qs)} passed in {time.time() - t0:.1f}s on {engines}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()

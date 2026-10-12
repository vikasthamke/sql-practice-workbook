"""
sql_practice: optional helper for the SQL Practice Workbook notebook.

Works with the Python standard library only:
    question("SQL-001")        show a question
    hint("SQL-001", 1)         progressive hints (levels 1-3)
    answer("SQL-001")          solution(s) + explanation
    list_questions(module="M05", role="MLE", difficulty="Hard")
    mark_done("SQL-001"); progress()

Optional database execution (pip install sqlalchemy pandas + psycopg or pymysql):
    connect("postgresql+psycopg://user:pass@localhost:5432/sql_workbook")
    connect("mysql+pymysql://user:pass@localhost:3306/sql_workbook")
    run("SELECT ...")          returns a pandas DataFrame (or a list of rows without pandas)
    check("SQL-001", my_sql)   compares your result with the reference solution on your database
"""
import json
import math
import os
import re

_HERE = os.path.dirname(os.path.abspath(__file__))
_DATA = os.path.join(_HERE, "workbook_data", "questions.json")
_PROGRESS = os.path.join(_HERE, "workbook_data", "progress.json")
_CACHE = {}
_ENGINE = {"engine": None, "dialect": None}


def _questions():
    if "q" not in _CACHE:
        with open(_DATA, encoding="utf-8") as fh:
            data = json.load(fh)
        _CACHE["q"] = {q["id"]: q for q in data["questions"]}
    return _CACHE["q"]


def _get(qid):
    qid = qid.strip().upper()
    if re.fullmatch(r"\d{1,3}", qid):
        qid = f"SQL-{int(qid):03d}"
    q = _questions().get(qid)
    if q is None:
        raise KeyError(f"Unknown question id {qid!r}. Use list_questions() to browse.")
    return q


def _show(markdown):
    """Render Markdown inside Jupyter; print plain text elsewhere."""
    try:
        from IPython import get_ipython  # noqa: WPS433
        if get_ipython() is not None:
            from IPython.display import Markdown, display  # noqa: WPS433
            display(Markdown(markdown))
            return
    except Exception:  # noqa: BLE001
        pass
    print(re.sub(r"</?(?:details|summary|b|a)(?:\s[^>]*)?>", "", markdown))


def list_questions(module=None, role=None, difficulty=None, dialect=None):
    """Print (and return) questions filtered by module (M01..M14), role (DS/MLE/AI), difficulty or dialect."""
    role_names = {"DS": "Data Scientist", "MLE": "ML Engineer", "AI": "AI Engineer"}
    out = []
    for q in _questions().values():
        if module and q["module"] != module.upper():
            continue
        if role and role_names.get(role.upper(), role) not in q["roles"]:
            continue
        if difficulty and q["difficulty"].lower() != difficulty.lower():
            continue
        if dialect and q["dialect"] != dialect.upper():
            continue
        out.append(q)
    done = _load_progress()
    for q in out:
        mark = "x" if q["id"] in done else " "
        print(f"[{mark}] {q['id']:<8} {q['difficulty']:<9} {q['dialect']:<10} {q['title']}")
    return [q["id"] for q in out]


def question(qid):
    q = _get(qid)
    s = q["sections"]
    md = (f"### {q['id']} · {q['title']}\n**{q['difficulty']}** · {q['roles']} · {q['dialect']} · ~{q['time']} min\n\n"
          f"**Context.** {s['context']}\n\n**Problem.** {s['problem']}\n\n**Tables.** {q['tables']}\n\n"
          f"**Expected output.** {s['expected']}\n\n**Edge cases**\n{s['edge_cases']}")
    _show(md)


def hint(qid, level=1):
    """Show hint 1, 2 or 3 (only the requested level)."""
    if level not in (1, 2, 3):
        raise ValueError("level must be 1, 2 or 3")
    q = _get(qid)
    _show(f"**{q['id']} · hint {level}/3:** {q['sections'][f'hint{level}']}")


def answer(qid, dialect=None):
    """Show the solution(s), explanation, mistakes and notes. dialect='pg' or 'mysql' filters versions."""
    q = _get(qid)
    s = q["sections"]
    blocks = []
    order = [("setup", "Setup"), ("setup_pg", "Setup (PostgreSQL)"), ("setup_mysql", "Setup (MySQL)"),
             ("solution", "Solution"), ("solution_pg", "Solution (PostgreSQL)"), ("solution_mysql", "Solution (MySQL)"),
             ("verify", "Verify"), ("equivalent_mysql", "MySQL equivalent"), ("equivalent_pg", "PostgreSQL equivalent"),
             ("alternative", "Alternative"), ("alternative_pg", "Alternative (PostgreSQL)"),
             ("alternative_mysql", "Alternative (MySQL)"), ("cleanup", "Clean up")]
    for key, label in order:
        if not s.get(key):
            continue
        if dialect == "pg" and key.endswith("_mysql"):
            continue
        if dialect == "mysql" and key.endswith("_pg"):
            continue
        blocks.append(f"**{label}**\n```sql\n{s[key].strip()}\n```")
    md = f"### Solution {q['id']} · {q['title']}\n\n" + "\n\n".join(blocks)
    for key, label in (("explanation", "Explanation"), ("alternative_note", "About the alternative"),
                       ("dialect_note", "PostgreSQL vs MySQL"), ("mistakes", "Common mistakes"),
                       ("performance", "Performance"), ("interview", "Interview insight"), ("rubric", "Rubric")):
        if s.get(key):
            md += f"\n\n**{label}**\n\n{s[key].strip()}"
    _show(md)


# ------------------------------------------------------------- progress
def _load_progress():
    try:
        with open(_PROGRESS, encoding="utf-8") as fh:
            return set(json.load(fh))
    except (OSError, ValueError):
        return set()


def mark_done(qid, done=True):
    q = _get(qid)
    p = _load_progress()
    (p.add if done else p.discard)(q["id"])
    with open(_PROGRESS, "w", encoding="utf-8") as fh:
        json.dump(sorted(p), fh)
    print(f"{q['id']} marked as {'done' if done else 'not done'} ({len(p)} completed)")


def progress():
    p = _load_progress()
    by_mod = {}
    for q in _questions().values():
        tot, d = by_mod.get(q["module"], (0, 0))
        by_mod[q["module"]] = (tot + 1, d + (q["id"] in p))
    for m in sorted(by_mod):
        tot, d = by_mod[m]
        print(f"{m}: {d:>3}/{tot:<3} {'#' * int(20 * d / tot):<20}")
    print(f"total: {len(p)}/{len(_questions())}")


# ------------------------------------------------------ optional execution
def connect(url, **kwargs):
    """Create a SQLAlchemy engine (optional). Requires sqlalchemy and a driver."""
    try:
        from sqlalchemy import create_engine  # noqa: WPS433
    except ImportError as e:  # pragma: no cover
        raise ImportError("connect() needs `pip install sqlalchemy` plus psycopg or pymysql. "
                          "Everything else in the workbook works without it.") from e
    engine = create_engine(url, **kwargs)
    with engine.connect():
        pass
    _ENGINE["engine"] = engine
    _ENGINE["dialect"] = "pg" if engine.dialect.name.startswith("postgres") else "mysql"
    print(f"connected ({engine.dialect.name})")
    return engine


def _split(sql):
    out, buf, q = [], [], False
    for ch in sql:
        if ch == "'":
            q = not q
        if ch == ";" and not q:
            if "".join(buf).strip():
                out.append("".join(buf).strip())
            buf = []
        else:
            buf.append(ch)
    tail = "".join(buf).strip()
    if tail and re.sub(r"--[^\n]*", "", tail).strip():
        out.append(tail)
    return out


def _execute(sql):
    """Execute statements through the raw DBAPI cursor.

    SQLAlchemy's text() would treat ':00' inside timestamp literals as bind
    parameters, and drivers apply %-formatting when parameters are passed, so
    statements are sent verbatim without parameters.
    """
    if _ENGINE["engine"] is None:
        raise RuntimeError("Not connected. Call connect(url) first (optional feature).")
    raw = _ENGINE["engine"].raw_connection()
    cols, rows = [], []
    try:
        cur = raw.cursor()
        for stmt in _split(sql):
            cur.execute(stmt)
            if cur.description:
                cols = [d[0] for d in cur.description]
                rows = [tuple(r) for r in cur.fetchall()]
        raw.commit()
    except Exception:
        raw.rollback()
        raise
    finally:
        raw.close()
    return cols, rows


def run(sql, limit=50):
    """Run SQL (several statements allowed; the last result is returned)."""
    cols, rows = _execute(sql)
    try:
        import pandas as pd  # noqa: WPS433
        df = pd.DataFrame(rows, columns=cols)
        return df.head(limit) if limit else df
    except ImportError:
        for r in rows[:limit]:
            print(r)
        return rows


def _norm(v):
    if v is None:
        return None
    if isinstance(v, bool):
        return float(v)
    try:
        f = float(v)
        return None if math.isnan(f) else round(f, 2)
    except (TypeError, ValueError):
        s = str(v)
        return s[:10] if re.fullmatch(r"\d{4}-\d{2}-\d{2} 00:00:00", s) else s


def check(qid, sql):
    """Compare your query's result with the reference solution on the connected database."""
    q = _get(qid)
    s = q["sections"]
    d = _ENGINE["dialect"]
    if q["compare"] == "none":
        print("This exercise produces an execution plan; compare it with the solution discussion instead.")
        return None
    ref = s.get(f"solution_{d}") or s.get("solution") or s.get(f"equivalent_{d}")
    if not ref or (q["dialect"] == "POSTGRESQL" and d == "mysql" and not s.get("equivalent_mysql")) or \
            (q["dialect"] == "MYSQL" and d == "pg" and not s.get("equivalent_pg")):
        print(f"No reference solution for this engine ({q['dialect']} question).")
        return None
    if s.get("verify") or s.get(f"verify_{d}"):
        print("DML/DDL exercise: run your statements, then compare the output of the verify query in answer().")
        return None
    yc, yr = _execute(sql)
    rc, rr = _execute(ref)
    ok = True
    if [c.lower() for c in yc] != [c.lower() for c in rc]:
        print(f"Column names differ.\n  yours:     {yc}\n  reference: {rc}")
        ok = False
    a = [tuple(_norm(v) for v in r) for r in yr]
    b = [tuple(_norm(v) for v in r) for r in rr]
    if q["compare"] != "ordered":
        a, b = sorted(a, key=repr), sorted(b, key=repr)
    if len(a) != len(b):
        print(f"Row count differs: yours {len(a)}, reference {len(b)}.")
        ok = False
    else:
        for i, (x, y) in enumerate(zip(a, b)):
            if x != y:
                print(f"First difference at row {i + 1}:\n  yours:     {yr[i]}\n  reference: {rr[i]}")
                ok = False
                break
    print("Matches the reference result." if ok else "Not yet; use hint() or compare the rows above.")
    return ok

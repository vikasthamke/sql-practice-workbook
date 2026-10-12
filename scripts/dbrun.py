"""
Run SQL against PostgreSQL and MySQL through their command-line clients
(psql / mysql), so validation needs no Python database drivers.

Connection settings come from the standard environment variables:
  PostgreSQL: PGHOST, PGPORT, PGUSER, PGPASSWORD, PGDATABASE  (default db sql_workbook)
  MySQL:      MYSQL_HOST, MYSQL_TCP_PORT, MYSQL_USER, MYSQL_PWD, MYSQL_DATABASE
Optional: PSQL_BIN / MYSQL_BIN to point at specific client binaries.
"""
import csv
import io
import os
import re
import subprocess

MARK = "@@RESULT@@"
NULL = None


class SQLError(Exception):
    pass


def split_statements(sql):
    """Split a script on top-level semicolons (respects quotes and comments)."""
    out, buf, i, n = [], [], 0, len(sql)
    in_s = in_d = False
    while i < n:
        c = sql[i]
        if not in_s and not in_d and sql.startswith("--", i):
            j = sql.find("\n", i)
            j = n if j == -1 else j
            buf.append(sql[i:j])
            i = j
            continue
        if not in_s and not in_d and sql.startswith("/*", i):
            j = sql.find("*/", i)
            j = n if j == -1 else j + 2
            buf.append(sql[i:j])
            i = j
            continue
        if c == "'" and not in_d:
            in_s = not in_s
        elif c == '"' and not in_s:
            in_d = not in_d
        if c == ";" and not in_s and not in_d:
            stmt = "".join(buf).strip()
            if _has_code(stmt):
                out.append(stmt)
            buf = []
        else:
            buf.append(c)
        i += 1
    stmt = "".join(buf).strip()
    if _has_code(stmt):
        out.append(stmt)
    return out


def _has_code(stmt):
    s = re.sub(r"--[^\n]*", "", stmt)
    s = re.sub(r"/\*.*?\*/", "", s, flags=re.S)
    return bool(s.strip())


def _pg_cmd():
    db = os.environ.get("PGDATABASE", "sql_workbook")
    return [os.environ.get("PSQL_BIN", "psql"), "-X", "-q", "--csv", "-v", "ON_ERROR_STOP=1",
            "-P", "null=\\N", "-d", db]


def _my_cmd(db=True):
    cmd = [os.environ.get("MYSQL_BIN", "mysql"), "--batch", "--default-character-set=utf8mb4"]
    if os.environ.get("MYSQL_HOST"):
        cmd += ["-h", os.environ["MYSQL_HOST"]]
    if os.environ.get("MYSQL_TCP_PORT"):
        cmd += ["-P", os.environ["MYSQL_TCP_PORT"]]
    cmd += ["-u", os.environ.get("MYSQL_USER", "root")]
    if db:
        cmd += [os.environ.get("MYSQL_DATABASE", "sql_workbook")]
    return cmd


def _unescape_mysql(v):
    if v == "NULL":
        return NULL
    if "\\" not in v:
        return v
    return (v.replace("\\t", "\t").replace("\\n", "\n").replace("\\r", "\r")
             .replace("\\0", "\0").replace("\\\\", "\\"))


def run(engine, sql, timeout=120):
    """
    Execute a script and return (columns, rows) of its LAST statement.
    Rows are lists of strings (None for NULL). Raises SQLError on failure.
    """
    stmts = split_statements(sql)
    if not stmts:
        raise SQLError("empty script")
    body = ";\n".join(stmts[:-1])
    script = (body + ";\n" if body else "") + f"SELECT '{MARK}' AS marker;\n" + stmts[-1] + ";\n"
    if engine == "pg":
        p = subprocess.run(_pg_cmd(), input=script, capture_output=True, text=True, timeout=timeout)
    else:
        p = subprocess.run(_my_cmd(), input=script, capture_output=True, text=True, timeout=timeout)
    if p.returncode != 0:
        raise SQLError((p.stderr or p.stdout).strip()[-2000:])
    out = p.stdout
    k = out.find(MARK)
    if k == -1:
        raise SQLError("marker not found in output:\n" + out[-500:])
    rest = out[k + len(MARK):].lstrip("\n")
    if not rest.strip():
        return [], []
    if engine == "pg":
        rdr = list(csv.reader(io.StringIO(rest)))
        cols, data = rdr[0], rdr[1:]
        data = [[NULL if v == "\\N" else v for v in r] for r in data]
    else:
        lines = rest.rstrip("\n").split("\n")
        cols = lines[0].split("\t")
        data = [[_unescape_mysql(v) for v in ln.split("\t")] for ln in lines[1:]]
    return cols, data


def run_raw(engine, sql, timeout=300):
    """Run a script and return raw stdout (used for EXPLAIN output and setup)."""
    if engine == "pg":
        cmd = [c for c in _pg_cmd() if c != "--csv"]
    else:
        cmd = _my_cmd()
    p = subprocess.run(cmd, input=sql, capture_output=True, text=True, timeout=timeout)
    if p.returncode != 0:
        raise SQLError((p.stderr or p.stdout).strip()[-2000:])
    return p.stdout


def available(engine):
    try:
        run(engine, "SELECT 1")
        return True
    except Exception:
        return False

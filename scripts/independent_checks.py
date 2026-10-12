"""
Independent re-computation of selected question results in plain Python,
directly from data/*.csv (no SQL involved). validate.py compares these rows
with the PostgreSQL (or MySQL) result of the same question.

Each check returns rows in the same column order and row order as the SQL.
Values are returned unrounded; the comparator tolerates the rounding that the
SQL solutions apply.
"""
import bisect
import csv
import json
import math
import os
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta
from functools import lru_cache

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from schema import TABLE_BY_NAME  # noqa: E402

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def _conv(v, typ):
    if v == "":
        return None
    t = typ.split("(")[0]
    if t in ("INT", "BIGINT", "SMALLINT"):
        return int(v)
    if t in ("DECIMAL",) or t.startswith("DOUBLE"):
        return float(v)
    if t == "BOOLEAN":
        return v == "true"
    if t == "TIMESTAMP":
        return datetime.fromisoformat(v)
    if t == "DATE":
        return date.fromisoformat(v)
    if t == "JSON":
        return json.loads(v)
    return v


@lru_cache(maxsize=None)
def load(table):
    cols = TABLE_BY_NAME[table]["columns"]
    with open(os.path.join(DATA, f"{table}.csv"), encoding="utf-8", newline="") as fh:
        r = csv.DictReader(fh)
        return [{c["name"]: _conv(row[c["name"]], c["type"]) for c in cols} for row in r]


def ts(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def between(x, a, b):
    return a <= x < b


# ------------------------------------------------------------------ checks
def sql_003():
    u = load("users")
    t = sum(1 for r in u if r["marketing_opt_in"] is True)
    f = sum(1 for r in u if r["marketing_opt_in"] is False)
    n = sum(1 for r in u if r["marketing_opt_in"] is None)
    return [[t, f, n, f, f + n]]


def sql_016():
    g = defaultdict(list)
    for o in load("orders"):
        g[o["status"]].append(o)
    rows = []
    for st, os_ in g.items():
        tot = sum(o["order_total"] for o in os_)
        rows.append([st, len(os_), tot, tot / len(os_), ts(min(o["order_ts"] for o in os_)),
                     ts(max(o["order_ts"] for o in os_))])
    return sorted(rows, key=lambda r: (-r[1], r[0]))


def sql_020():
    g = defaultdict(list)
    for o in load("orders"):
        if o["status"] == "completed" and between(o["order_ts"], datetime(2024, 1, 1), datetime(2025, 7, 1)):
            g[date(o["order_ts"].year, o["order_ts"].month, 1)].append(o["order_total"])
    return [[m.isoformat(), len(v), sum(v), sum(v) / len(v)] for m, v in sorted(g.items())]


def sql_025():
    users, cnt = defaultdict(set), defaultdict(int)
    for e in load("events"):
        if between(e["event_ts"], datetime(2025, 6, 1), datetime(2025, 7, 1)):
            d = e["event_ts"].date()
            users[d].add(e["user_id"])
            cnt[d] += 1
    return [[d.isoformat(), len(users[d]), cnt[d], cnt[d] / len(users[d])] for d in sorted(cnt)]


def sql_031():
    seg = {o["org_id"]: o["segment"] for o in load("organizations")}
    lines = defaultdict(int)
    for li in load("order_items"):
        lines[li["order_id"]] += 1
    correct, naive = defaultdict(float), defaultdict(float)
    for o in load("orders"):
        if o["status"] == "completed" and between(o["order_ts"], datetime(2025, 1, 1), datetime(2025, 7, 1)):
            s = seg[o["org_id"]]
            correct[s] += o["order_total"]
            naive[s] += o["order_total"] * lines[o["order_id"]]
    return [[s, naive[s], correct[s], 100 * (naive[s] / correct[s] - 1)] for s in sorted(correct)]


def sql_078():
    days, months = defaultdict(set), defaultdict(set)
    for e in load("events"):
        if between(e["event_ts"], datetime(2025, 1, 1), datetime(2025, 7, 1)):
            days[e["event_ts"].date()].add(e["user_id"])
            months[date(e["event_ts"].year, e["event_ts"].month, 1)].add(e["user_id"])
    out = []
    for m in sorted(months):
        dau = [len(v) for d, v in days.items() if d.year == m.year and d.month == m.month]
        avg = sum(dau) / len(dau)
        out.append([m.isoformat(), len(months[m]), avg, 100 * avg / len(months[m])])
    return out


def sql_087():
    rev = defaultdict(float)
    for o in load("orders"):
        if o["status"] == "completed":
            rev[o["org_id"]] += o["order_total"]
    items = sorted(rev.items(), key=lambda kv: (-kv[1], kv[0]))
    total = sum(rev.values())
    before, need = 0.0, 0
    for _, v in items:
        if before < 0.8 * total:
            need += 1
        before += v
    return [[len(items), need, 100 * need / len(items)]]


def authoritative_labels():
    best = {}
    for l in load("training_labels"):
        if l["label_name"] != "churned_30d":
            continue
        k = (l["entity_id"], l["observation_date"])
        key = (l["label_available_at"] or datetime.min, l["label_id"])
        if k not in best or key > best[k][0]:
            best[k] = (key, l)
    test = {e["entity_id"] for e in load("ml_entities") if e["is_test_account"]}
    return {k: v[1]["label_value"] for k, v in best.items()
            if v[1]["label_value"] is not None and k[0] not in test}


def sql_096():
    test = {e["entity_id"] for e in load("ml_entities") if e["is_test_account"]}
    g = defaultdict(list)
    for l in load("training_labels"):
        if l["label_name"] == "churned_30d" and l["label_value"] is not None and l["entity_id"] not in test:
            g[l["observation_date"]].append(l["label_value"])
    out = []
    for d, v in sorted(g.items()):
        p = sum(v)
        out.append([d.isoformat(), len(v), p, 100 * p / len(v), (len(v) - p) / p if p else None])
    return out


def sql_098():
    obs = datetime(2025, 3, 1)
    sess = defaultdict(list)
    for s in load("sessions"):
        sess[s["user_id"]].append(s["started_at"])
    for v in sess.values():
        v.sort()

    def cnt(lst, a, b):
        return bisect.bisect_left(lst, b) - bisect.bisect_left(lst, a)

    rebuilt = {}
    for e in load("ml_entities"):
        if e["registered_at"] > obs:
            continue
        ss = sess.get(e["user_id"], [])
        if cnt(ss, obs - timedelta(days=30), obs) >= 2:
            rebuilt[e["entity_id"]] = 1 if cnt(ss, obs, obs + timedelta(days=30)) == 0 else 0
    best = {}
    for l in load("training_labels"):
        if l["label_name"] == "churned_30d" and l["observation_date"] == obs.date():
            key = (l["label_available_at"] or datetime.min, l["label_id"])
            if l["entity_id"] not in best or key > best[l["entity_id"]][0]:
                best[l["entity_id"]] = (key, l["label_value"])
    stored = {k: v[1] for k, v in best.items()}
    match = sum(1 for k in rebuilt if k in stored and stored[k] == rebuilt[k])
    mism = sum(1 for k in rebuilt if k in stored and stored[k] != rebuilt[k])
    return [[len(rebuilt), len(stored), match, mism, sum(1 for k in rebuilt if k not in stored),
             sum(1 for k in stored if k not in rebuilt)]]


def _latest_valid_preds():
    best = {}
    for p in load("model_predictions"):
        if p["score"] is None:
            continue
        k = (p["model_version_id"], p["entity_id"], p["predicted_at"].date())
        key = (p["predicted_at"], p["prediction_id"])
        if k not in best or key > best[k][0]:
            best[k] = (key, p)
    return {k: v[1] for k, v in best.items()}


def sql_107():
    labels = authoritative_labels()
    vlabel = {m["model_version_id"]: m["version_label"] for m in load("model_versions")
              if m["model_name"] == "churn_classifier"}
    cm = defaultdict(lambda: [0, 0, 0, 0])
    for (mid, ent, d), p in _latest_valid_preds().items():
        if mid not in vlabel or (ent, d) not in labels:
            continue
        y, yh = labels[(ent, d)], p["predicted_label"]
        idx = {(1, 1): 0, (1, 0): 1, (0, 1): 2, (0, 0): 3}[(yh, y)]
        cm[vlabel[mid]][idx] += 1
    out = []
    for v in sorted(cm):
        tp, fp, fn, tn = cm[v]
        n = tp + fp + fn + tn
        out.append([v, n, tp, fp, fn, tn, 100 * tp / (tp + fp) if tp + fp else None,
                    100 * tp / (tp + fn) if tp + fn else None, 100 * (tp + tn) / n,
                    2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else None])
    return out


def sql_114():
    labels = authoritative_labels()
    vlabel = {m["model_version_id"]: m["version_label"] for m in load("model_versions")
              if m["model_name"] == "churn_classifier"}
    groups = defaultdict(list)
    for (mid, ent, d), p in _latest_valid_preds().items():
        if mid in vlabel and (ent, d) in labels:
            groups[vlabel[mid]].append((p["score"], labels[(ent, d)]))
    out = []
    for v in sorted(groups):
        pairs = groups[v]
        pos = [s for s, y in pairs if y == 1]
        neg = [s for s, y in pairs if y == 0]
        # exact pairwise AUC (ties count 1/2): independent of the rank formula used in SQL
        neg_sorted = sorted(neg)
        wins = 0.0
        for s in pos:
            lo = bisect.bisect_left(neg_sorted, s)
            hi = bisect.bisect_right(neg_sorted, s)
            wins += lo + 0.5 * (hi - lo)
        out.append([v, len(pos), len(neg), wins / (len(pos) * len(neg))])
    return out


def sql_117():
    g = defaultdict(list)
    for r in load("llm_requests"):
        if r["status"] == "success" and not r["cache_hit"] and \
                between(r["requested_at"], datetime(2025, 4, 1), datetime(2025, 7, 1)):
            g[r["model_name"]].append(r["latency_ms"])
    out = []
    for m, v in g.items():
        v.sort()
        n = len(v)
        pct = [v[math.ceil(p * n) - 1] for p in (0.50, 0.95, 0.99)]
        out.append([m, n] + pct)
    return sorted(out, key=lambda r: (r[3], r[0]))


def _price(model, d):
    for p in load("llm_pricing"):
        if p["model_name"] == model and p["effective_from"] <= d and (p["effective_to"] is None or d <= p["effective_to"]):
            return p
    raise KeyError((model, d))


def sql_118():
    g = defaultdict(lambda: [0, 0.0])
    for r in load("llm_requests"):
        if between(r["requested_at"], datetime(2025, 1, 1), datetime(2025, 7, 1)):
            p = _price(r["model_name"], r["requested_at"].date())
            c = 0.0 if r["cache_hit"] else (r["input_tokens"] / 1000 * p["input_usd_per_1k"]
                                            + (r["output_tokens"] or 0) / 1000 * p["output_usd_per_1k"])
            k = (date(r["requested_at"].year, r["requested_at"].month, 1), r["model_name"])
            g[k][0] += 1
            g[k][1] += c
    return [[m.isoformat(), model, v[0], v[1]] for (m, model), v in sorted(g.items())]


def sql_129():
    names = {c["config_id"]: c["config_name"] for c in load("retrieval_configs")}
    first = {}
    for r in load("retrieval_evaluations"):
        k = (r["config_id"], r["query_id"])
        first.setdefault(k, None)
        if r["is_relevant"] is True:
            if first[k] is None or r["rank_position"] < first[k]:
                first[k] = r["rank_position"]
    per = defaultdict(list)
    for (cfg, q), fr in first.items():
        per[names[cfg]].append(fr)
    out = []
    for name in sorted(per):
        v = per[name]
        n = len(v)
        hit = lambda k: 100 * sum(1 for x in v if x is not None and x <= k) / n  # noqa: E731
        mrr = sum((1 / x) if (x is not None and x <= 5) else 0 for x in v) / n
        out.append([name, n, hit(1), hit(3), hit(5), mrr])
    return out


def sql_089():
    seg = {o["org_id"]: o["segment"] for o in load("organizations")}
    g = defaultdict(list)
    for o in load("orders"):
        if o["status"] == "completed":
            g[seg[o["org_id"]]].append(o["order_total"])
    out = []
    for s in sorted(g):
        v = sorted(g[s])
        n = len(v)
        med = v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2
        out.append([s, n, sum(v) / n, med])
    return out


CHECKS = {
    "SQL-003": sql_003, "SQL-016": sql_016, "SQL-020": sql_020, "SQL-025": sql_025,
    "SQL-031": sql_031, "SQL-078": sql_078, "SQL-087": sql_087, "SQL-089": sql_089,
    "SQL-096": sql_096, "SQL-098": sql_098, "SQL-107": sql_107, "SQL-114": sql_114,
    "SQL-117": sql_117, "SQL-118": sql_118, "SQL-129": sql_129,
}

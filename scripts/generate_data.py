#!/usr/bin/env python3
"""
Deterministic dataset generator for the SQL Practice Workbook.

  python3 scripts/generate_data.py            # writes data/*.csv

Standard library only, fixed seed, no network access. Running it twice
produces byte-identical CSV files.

Fictional company: "Lumen Analytics" -- a SaaS data platform with AI features
(a RAG support bot, a SQL copilot and a document summarizer).

CSV conventions: header row, comma separated, RFC-4180 quoting, an EMPTY
unquoted field means NULL (the data never contains empty strings),
booleans are 'true'/'false', timestamps are 'YYYY-MM-DD HH:MM:SS' in UTC.
"""
import bisect
import csv
import hashlib
import json
import math
import os
import random
import sys
from datetime import date, datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from schema import TABLES  # noqa: E402

SEED = 20250701
rng = random.Random(SEED)

DATA_START = datetime(2024, 1, 1)
DATA_END = datetime(2025, 7, 1)          # exclusive; "today" for the workbook
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data")


# --------------------------------------------------------------- helpers
def wchoice(pairs):
    """Weighted choice from [(value, weight), ...]."""
    total = sum(w for _, w in pairs)
    x = rng.random() * total
    acc = 0.0
    for v, w in pairs:
        acc += w
        if x < acc:
            return v
    return pairs[-1][0]


def poisson(lam):
    if lam <= 0:
        return 0
    L, k, p = math.exp(-lam), 0, 1.0
    while True:
        p *= rng.random()
        if p <= L:
            return k
        k += 1


def secs(dt):
    return dt.replace(microsecond=0)


def rand_between(a, b):
    """Uniform datetime in [a, b)."""
    span = (b - a).total_seconds()
    if span <= 0:
        return secs(a)
    return secs(a + timedelta(seconds=rng.random() * span))


HOUR_W = [1, 1, 1, 1, 1, 2, 3, 5, 8, 10, 10, 9, 8, 9, 10, 10, 9, 7, 5, 4, 3, 2, 2, 1]


def business_time(day):
    """A datetime on `day` (date) with a day-time weighted hour."""
    h = wchoice(list(enumerate(HOUR_W)))
    return datetime(day.year, day.month, day.day, h, rng.randrange(60), rng.randrange(60))


def rand_day(a, b):
    """Random date in [a, b) given datetimes/dates."""
    a = a.date() if isinstance(a, datetime) else a
    b = b.date() if isinstance(b, datetime) else b
    n = (b - a).days
    return a + timedelta(days=rng.randrange(max(n, 1)))


def hexid(nbytes=16):
    return "".join(f"{rng.randrange(256):02x}" for _ in range(nbytes))


def uuid_like():
    h = hexid(16)
    return f"{h[:8]}-{h[8:12]}-4{h[13:16]}-a{h[17:20]}-{h[20:32]}"


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def money(x):
    return round(x + 1e-9, 2)


def month_start(d):
    return datetime(d.year, d.month, 1)


def add_months(d, n):
    y, m = d.year, d.month - 1 + n
    return datetime(y + m // 12, m % 12 + 1, 1)


# ------------------------------------------------------------ static data
FIRST = ["Aarav", "Maya", "Liam", "Sofia", "Noah", "Emma", "Lucas", "Mia", "Ethan", "Ava",
         "Arjun", "Priya", "Jonas", "Lena", "Mateo", "Chloé", "Zoë", "José", "Hannah", "Omar",
         "Yuki", "Kenji", "Fatima", "Ali", "Elena", "Marco", "Sara", "David", "Olivia", "Isaac",
         "Grace", "Leo", "Nora", "Felix", "Ines", "Rohan", "Ananya", "Tom", "Julia", "Ben",
         "Clara", "Max", "Aisha", "Daniel", "Laura", "Ravi", "Meera", "Paul", "Anna", "Victor"]
LAST = ["Sharma", "Smith", "Müller", "García", "Patel", "Johnson", "Schmidt", "Rossi", "Kim",
        "Nguyen", "Brown", "Dubois", "Silva", "Kumar", "Wilson", "Fischer", "Martin", "Lopez",
        "Singh", "Taylor", "Weber", "Moreau", "Costa", "Ito", "Khan", "Novak", "Jensen", "O'Brien",
        "Reddy", "Clark", "Wagner", "Bernard", "Santos", "Tanaka", "Ahmed", "Evans", "Becker",
        "Lefèvre", "Ferreira", "Iyer"]
ORG_A = ["Blue", "North", "Bright", "Quantum", "Silver", "Green", "Swift", "Prime", "Urban",
         "Nova", "Iron", "Clear", "Summit", "Atlas", "Coral", "Vertex", "Pine", "Delta",
         "Golden", "Polar", "Crimson", "Lunar", "Solar", "Rapid", "Cedar"]
ORG_B = ["Harbor", "Peak", "Labs", "Logistics", "Health", "Finance", "Retail", "Systems",
         "Foods", "Media", "Works", "Dynamics", "Analytics", "Ventures", "Bank", "Energy",
         "Learning", "Motors", "Partners", "Networks"]
ORG_SUFFIX = ["Inc", "Ltd", "GmbH", "LLC", "Group", "Co", "SA", "Pvt Ltd", "BV", "Pte Ltd"]
INDUSTRIES = ["Software", "Financial Services", "Healthcare", "Retail", "Manufacturing",
              "Education", "Media", "Logistics", "Energy", "Public Sector"]
COUNTRIES = [  # code, weight, timezones, typical suffix
    ("US", 35, ["America/New_York", "America/Chicago", "America/Los_Angeles"], ["Inc", "LLC", "Co"]),
    ("GB", 10, ["Europe/London"], ["Ltd", "Group"]),
    ("DE", 10, ["Europe/Berlin"], ["GmbH", "Group"]),
    ("IN", 12, ["Asia/Kolkata"], ["Pvt Ltd"]),
    ("FR", 6, ["Europe/Paris"], ["SA", "Group"]),
    ("CA", 6, ["America/Toronto"], ["Inc", "Ltd"]),
    ("AU", 5, ["Australia/Sydney"], ["Ltd", "Group"]),
    ("BR", 5, ["America/Sao_Paulo"], ["SA", "Ltd"]),
    ("NL", 5, ["Europe/Amsterdam"], ["BV"]),
    ("SG", 6, ["Asia/Singapore"], ["Pte Ltd"]),
]

PLANS = [  # id, name, tier, price, annual_disc, seat_limit, active, launched
    (1, "Free", 0, 0.00, None, 3, True, date(2022, 1, 10)),
    (2, "Starter", 1, 12.00, 15.00, 10, True, date(2022, 1, 10)),
    (3, "Pro", 2, 29.00, 20.00, 50, True, date(2023, 4, 1)),
    (4, "Business", 3, 49.00, 20.00, 200, True, date(2022, 6, 1)),
    (5, "Enterprise", 4, 89.00, 20.00, None, True, date(2022, 6, 1)),
    (6, "Pro (Legacy)", 2, 25.00, 15.00, 50, False, date(2021, 3, 1)),
]
PLAN = {p[0]: p for p in PLANS}

CATEGORIES = [  # id, name, parent
    (1, "Software", None), (2, "Add-ons", 1), (3, "Usage Credits", 1),
    (4, "Services", None), (5, "Training", 4), (6, "Professional Services", 4),
    (7, "Implementation", 6), (8, "Custom Integration", 6),
    (9, "Marketplace", None), (10, "Templates", 9), (11, "Connectors", 9),
]
PRODUCTS = [  # name, category, price, active, launched
    ("Extra Storage 100GB", 2, 19.00, True, date(2022, 3, 1)),
    ("Extra Storage 1TB", 2, 149.00, True, date(2023, 1, 15)),
    ("Advanced Audit Log", 2, 99.00, True, date(2023, 6, 1)),
    ("SSO Add-on", 2, 199.00, True, date(2022, 9, 1)),
    ("Sandbox Workspace", 2, 59.00, True, date(2023, 9, 1)),
    ("Priority Support", 2, 299.00, True, date(2022, 1, 15)),
    ("Legacy Reports Pack", 2, 39.00, False, date(2021, 5, 1)),
    ("AI Credits 10k", 3, 25.00, True, date(2024, 10, 1)),
    ("AI Credits 100k", 3, 200.00, True, date(2024, 10, 1)),
    ("Query Credits 1M", 3, 49.00, True, date(2022, 2, 1)),
    ("Query Credits 10M", 3, 399.00, True, date(2022, 2, 1)),
    ("Export Credits 500", 3, 15.00, True, date(2023, 3, 1)),
    ("SQL Fundamentals Course", 5, 149.00, True, date(2022, 4, 1)),
    ("Admin Certification", 5, 349.00, True, date(2023, 2, 1)),
    ("AI Features Workshop", 5, 499.00, True, date(2024, 11, 1)),
    ("Team Onboarding Session", 5, 250.00, True, date(2022, 4, 1)),
    ("Data Modeling Bootcamp", 5, 899.00, True, date(2023, 8, 1)),
    ("Legacy Webinar Seat", 5, 49.00, False, date(2021, 1, 1)),
    ("Implementation - Starter", 7, 1500.00, True, date(2022, 6, 1)),
    ("Implementation - Enterprise", 7, 12000.00, True, date(2022, 6, 1)),
    ("Data Migration Day", 7, 1800.00, True, date(2022, 6, 1)),
    ("Salesforce Integration Build", 8, 4500.00, True, date(2023, 1, 1)),
    ("Custom Connector Build", 8, 6500.00, True, date(2023, 5, 1)),
    ("Architecture Review", 8, 3000.00, True, date(2024, 2, 1)),
    ("Finance KPI Template", 10, 79.00, True, date(2023, 1, 1)),
    ("Marketing Funnel Template", 10, 59.00, True, date(2023, 1, 1)),
    ("Churn Analysis Template", 10, 99.00, True, date(2023, 7, 1)),
    ("RAG Evaluation Template", 10, 129.00, True, date(2025, 1, 15)),
    ("SaaS Metrics Template", 10, 69.00, True, date(2023, 4, 1)),
    ("Snowflake Connector", 11, 99.00, True, date(2022, 5, 1)),
    ("BigQuery Connector", 11, 99.00, True, date(2022, 5, 1)),
    ("Kafka Connector", 11, 149.00, True, date(2023, 10, 1)),
    ("HubSpot Connector", 11, 49.00, True, date(2023, 3, 1)),
    ("Legacy FTP Connector", 11, 29.00, False, date(2020, 6, 1)),
    ("Vector DB Connector", 11, 179.00, True, date(2024, 12, 1)),
    ("Postgres CDC Connector", 11, 129.00, True, date(2024, 4, 1)),
]
PRODUCT_WEIGHTS = {2: 14, 3: 22, 5: 6, 7: 1.5, 8: 1, 10: 8, 11: 10}
DISCONTINUED_ON = date(2024, 9, 1)   # inactive products only sold before this date

EVENT_POOL = [("view_dashboard", 30), ("run_query", 28), ("create_project", 6),
              ("ai_assist_used", 12), ("invite_user", 3), ("export_report", 7),
              ("view_pricing", 4)]
AI_LAUNCH = datetime(2024, 10, 1)

# --------------------------------------------------------------- tables
rows = {t["name"]: [] for t in TABLES}


def gen_static():
    for p in PLANS:
        rows["plans"].append(dict(plan_id=p[0], plan_name=p[1], tier_rank=p[2],
                                  price_per_seat_month=p[3], annual_discount_pct=p[4],
                                  seat_limit=p[5], is_active=p[6], launched_on=p[7]))
    for c in CATEGORIES:
        rows["product_categories"].append(dict(category_id=c[0], category_name=c[1],
                                               parent_category_id=c[2]))
    for i, p in enumerate(PRODUCTS, 1):
        rows["products"].append(dict(product_id=i, product_name=p[0], category_id=p[1],
                                     list_price=p[2], is_active=p[3], launched_on=p[4]))


# ---------------------------------------------------------- organizations
orgs = []


def gen_orgs(n=200):
    names_used = []
    for i in range(n):
        seg = wchoice([("SMB", 60), ("Mid-Market", 30), ("Enterprise", 10)])
        cc, _, tzs, sfx = wchoice([((c[0], c[1], c[2], c[3]), c[1]) for c in COUNTRIES])
        if i < 22:
            created = rand_between(datetime(2023, 2, 1), datetime(2024, 1, 1))
        else:
            # growth: more sign-ups later (triangular distribution over the window)
            frac = rng.triangular(0, 1, 0.8)
            created = DATA_START + timedelta(seconds=frac * (datetime(2025, 6, 1) - DATA_START).total_seconds())
            created = business_time(created.date())
        name = f"{rng.choice(ORG_A)} {rng.choice(ORG_B)} {rng.choice(sfx)}"
        while name in names_used:
            name = f"{rng.choice(ORG_A)} {rng.choice(ORG_B)} {rng.choice(sfx)}"
        names_used.append(name)
        band = {"SMB": [("1-10", 50), ("11-50", 50)],
                "Mid-Market": [("51-200", 70), ("201-1000", 30)],
                "Enterprise": [("201-1000", 30), ("1000+", 70)]}[seg]
        orgs.append(dict(segment=seg, country_code=cc, timezone=rng.choice(tzs),
                         created_at=created, org_name=name,
                         industry=None if rng.random() < 0.06 else rng.choice(INDUSTRIES),
                         employee_band=None if rng.random() < 0.08 else wchoice(band)))
    orgs.sort(key=lambda o: o["created_at"])
    for i, o in enumerate(orgs, 1):
        o["org_id"] = i
        o["parent_org_id"] = None
        o["is_deleted"] = False
        o["deleted_at"] = None
    # two pairs of different companies sharing a name
    orgs[150]["org_name"] = orgs[40]["org_name"]
    orgs[171]["org_name"] = orgs[95]["org_name"]
    # subsidiaries: parent must be older (smaller id) and Mid-Market/Enterprise
    big = [o for o in orgs if o["segment"] != "SMB"]
    subs = 0
    for o in orgs[30:]:
        if subs >= 18:
            break
        if rng.random() < 0.12:
            cands = [b for b in big if b["org_id"] < o["org_id"] and b is not o]
            if cands:
                p = rng.choice(cands[:max(3, len(cands) // 2)])
                o["parent_org_id"] = p["org_id"]
                subs += 1
    # guarantee some depth-3 chains
    level2 = [o for o in orgs if o["parent_org_id"] is not None]
    for o in orgs[120:]:
        if o["parent_org_id"] is None and sum(1 for x in orgs if x.get("_deep")) < 4:
            cands = [p for p in level2 if p["org_id"] < o["org_id"]]
            if cands and rng.random() < 0.15:
                o["parent_org_id"] = rng.choice(cands)["org_id"]
                o["_deep"] = True


# ---------------------------------------------------------- subscriptions
def gen_subscriptions():
    sid = 0
    for o in orgs:
        seg = o["segment"]
        start = o["created_at"]
        if start < datetime(2023, 9, 1) and rng.random() < 0.5:
            plan = 6
        else:
            plan = wchoice({"SMB": [(1, 40), (2, 40), (3, 20)],
                            "Mid-Market": [(2, 20), (3, 50), (4, 30)],
                            "Enterprise": [(4, 40), (5, 60)]}[seg])
        periods = []
        churned_final = None
        t = start
        while t < DATA_END:
            length = timedelta(days=rng.expovariate(1 / 260))
            end = t + length
            seats = {"SMB": rng.randint(1, 8), "Mid-Market": rng.randint(8, 60),
                     "Enterprise": rng.randint(40, 400)}[seg]
            lim = PLAN[plan][5]
            if lim:
                seats = min(seats, lim)
            cycle = "annual" if (PLAN[plan][4] is not None and rng.random() < 0.35) else "monthly"
            if plan == 6:   # legacy plan migrated during 2024
                end = min(end, rand_between(datetime(2024, 2, 1), datetime(2024, 12, 1)))
                end = max(end, t + timedelta(days=30))
            period = dict(org=o, plan=plan, seats=seats, cycle=cycle, start=t, end=end)
            periods.append(period)
            if end >= DATA_END:
                period["end"] = None
                break
            if plan == 6:
                nxt = wchoice([(3, 70), (4, 20), (2, 10)])
                period["status"] = "switched"
                plan = nxt
                t = end
                continue
            outcome = wchoice([("upgrade", 42), ("downgrade", 10), ("churn", 22), ("renew", 26)])
            if outcome == "churn":
                period["status"] = "canceled"
                period["reason"] = wchoice([("too_expensive", 30), ("missing_feature", 20),
                                            ("switched_competitor", 20), ("no_longer_needed", 15),
                                            (None, 15)])
                if rng.random() < 0.3:  # comes back later
                    t = end + timedelta(days=rng.randint(30, 120))
                    plan = max(2, plan - 1) if plan in (1, 2, 3, 4, 5) else 3
                    if t >= DATA_END:
                        churned_final = end
                        break
                    continue
                churned_final = end
                break
            period["status"] = "switched"
            tier = {1: 0, 2: 1, 3: 2, 4: 3, 5: 4}[plan]
            if outcome == "upgrade":
                tier = min(4, tier + 1)
            elif outcome == "downgrade":
                tier = max(0, tier - 1)
            plan = [1, 2, 3, 4, 5][tier]
            t = end
        # open period status
        last = periods[-1]
        if last["end"] is None:
            if last["start"] > DATA_END - timedelta(days=14) and last["plan"] != 1:
                last["status"] = "trialing"
            else:
                last["status"] = wchoice([("active", 92), ("past_due", 8)])
        o["churned_at"] = churned_final
        # soft-deleted organizations: churned ones, deleted 5-60 days later
        if churned_final and churned_final < datetime(2025, 5, 1) and rng.random() < 0.35:
            o["is_deleted"] = True
            o["deleted_at"] = churned_final + timedelta(days=rng.randint(5, 60), hours=rng.randint(0, 23))
        for p in periods:
            sid += 1
            price = PLAN[p["plan"]][3]
            disc = PLAN[p["plan"]][4] or 0
            mrr = p["seats"] * price * (1 - disc / 100 if p["cycle"] == "annual" else 1)
            rows["subscriptions"].append(dict(
                subscription_id=sid, org_id=o["org_id"], plan_id=p["plan"], status=p["status"],
                billing_cycle=p["cycle"], seats=p["seats"], mrr=money(mrr),
                started_at=p["start"], ended_at=p["end"],
                cancel_reason=p.get("reason") if p["status"] == "canceled" else None))
        o["periods"] = periods
    # overlap bug: for a few orgs, the next period starts before the previous ended
    by_org = {}
    for s in rows["subscriptions"]:
        by_org.setdefault(s["org_id"], []).append(s)
    multi = [v for v in by_org.values() if len(v) >= 2 and v[0]["ended_at"] is not None]
    for v in rng.sample(multi, 6):
        a, b = v[0], v[1]
        if b["started_at"] == a["ended_at"]:
            b["started_at"] = a["ended_at"] - timedelta(days=rng.randint(3, 20))
    # sort and renumber by start time
    rows["subscriptions"].sort(key=lambda s: (s["started_at"], s["org_id"]))
    for i, s in enumerate(rows["subscriptions"], 1):
        s["subscription_id"] = i


# ------------------------------------------------------------------ users
users = []


def make_email(first, last, org, n):
    dom = org["org_name"].split()[0].lower() + org["org_name"].split()[1].lower() + ".com"
    base = f"{first}.{last}".lower()
    for a, b in (("é", "e"), ("è", "e"), ("ë", "e"), ("ü", "u"), ("'", "")):
        base = base.replace(a, b)
    return f"{base}{n if n else ''}@{dom}"


def gen_users():
    seen_emails = []
    for o in orgs:
        n = {"SMB": rng.randint(2, 7), "Mid-Market": rng.randint(6, 16),
             "Enterprise": rng.randint(14, 34)}[o["segment"]]
        org_end = o["churned_at"] or DATA_END
        for k in range(n):
            if k == 0:
                signup = o["created_at"] + timedelta(minutes=rng.randint(1, 50))
            else:
                horizon = min(org_end, DATA_END) - o["created_at"]
                frac = min(rng.expovariate(1 / 0.18), 0.98)
                signup = o["created_at"] + timedelta(seconds=frac * horizon.total_seconds())
                signup = business_time(signup.date())
                if signup <= o["created_at"]:
                    signup = o["created_at"] + timedelta(hours=rng.randint(1, 48))
                if signup >= DATA_END:
                    signup = DATA_END - timedelta(days=rng.randint(1, 20), hours=3)
            first, last = rng.choice(FIRST), rng.choice(LAST)
            email = make_email(first, last, o, 0)
            j = 1
            while email in seen_emails:
                j += 1
                email = make_email(first, last, o, j)
            seen_emails.append(email)
            arche = wchoice([("dormant", 30), ("casual", 46), ("regular", 18), ("power", 6)])
            mean_life = {"dormant": 40, "casual": 300, "regular": 1100, "power": 1500}[arche]
            until = signup + timedelta(days=rng.expovariate(1 / mean_life))
            if o["churned_at"] and until > o["churned_at"]:
                until = o["churned_at"] - timedelta(days=rng.randint(0, 10))
            if until <= signup:
                until = signup + timedelta(hours=2)
            if until >= DATA_END:
                until = None
            channel = wchoice([("organic", 35), ("paid_search", 20), ("referral", 15),
                               ("social", 10), ("partner", 12), (None, 8)])
            users.append(dict(org=o, first=first, last=last, email=email, signup_at=signup,
                              arche=arche, active_until=until, channel=channel,
                              role="admin" if k == 0 else wchoice([("admin", 8), ("member", 70), ("viewer", 22)])))
    # duplicate accounts (same person, re-registered with a differently formatted e-mail)
    dups = []
    for u in rng.sample(users, 26):
        e = u["email"]
        variant = rng.choice([
            e[0].upper() + e[1:],
            e.upper(),
            " " + e,
            e + " ",
            e.split("@")[0].title().replace(".", ".") + "@" + e.split("@")[1].upper(),
        ])
        signup = u["signup_at"] + timedelta(days=rng.randint(3, 200), hours=rng.randint(0, 10))
        if signup >= DATA_END:
            signup = u["signup_at"] + timedelta(days=1)
        dups.append(dict(org=u["org"], first=u["first"], last=u["last"], email=variant,
                         signup_at=signup, arche="dormant",
                         active_until=signup + timedelta(days=rng.randint(1, 20)),
                         channel=u["channel"], role="member", dup_of=u))
    users.extend(dups)
    users.sort(key=lambda u: u["signup_at"])
    for i, u in enumerate(users, 1):
        u["user_id"] = i
    # referrals point to an earlier user
    for u in users:
        u["referred_by"] = None
        if u["channel"] == "referral" and u["user_id"] > 20 and rng.random() < 0.9:
            u["referred_by"] = rng.randint(1, u["user_id"] - 1)


# -------------------------------------------------------- sessions/events
sessions = []      # dicts with user, start, end, device, version, events(list)
events = []        # dicts with user, session(or None), ts, name, props


def app_version(ts):
    months = (ts.year - 2023) * 12 + ts.month
    major = 3 + months // 12
    return f"{major}.{months % 12}"


def new_session(u, start, n_events=None, login=True):
    dur = max(1.0, rng.lognormvariate(math.log(11), 0.8))
    end = start + timedelta(minutes=dur, seconds=rng.randrange(60))
    s = dict(user=u, start=secs(start), end=secs(end),
             device=wchoice([("desktop", 70), ("mobile", 22), ("tablet", 8)]),
             version=None if rng.random() < 0.03 else app_version(start), events=[])
    if rng.random() < 0.04:
        s["end_null"] = True
    sessions.append(s)
    u["sessions"].append(s)
    t = s["start"] + timedelta(seconds=rng.randint(1, 20))
    if login and rng.random() < 0.7:
        add_event(u, s, t, "login", None)
    k = n_events if n_events is not None else 1 + poisson(0.45)
    for _ in range(k):
        t = t + timedelta(seconds=rng.randint(15, 240))
        if t > s["end"]:
            t = s["end"]
        pool = [p for p in EVENT_POOL if p[0] != "ai_assist_used" or t >= AI_LAUNCH]
        name = wchoice(pool)
        add_event(u, s, t, name, event_props(name))
    return s


def event_props(name):
    if name == "view_pricing":
        return {"page": "/pricing", "referrer": rng.choice(["dashboard", "email", "banner", "docs"])}
    if name == "export_report":
        return {"format": wchoice([("csv", 60), ("pdf", 30), ("xlsx", 10)])}
    if name == "ai_assist_used":
        return {"feature": wchoice([("sql_copilot", 60), ("support_bot", 25), ("doc_summary", 15)])}
    if name == "run_query":
        return {"rows_returned": int(rng.lognormvariate(5, 2)) if rng.random() > 0.1 else 0,
                "engine": rng.choice(["warehouse", "lakehouse"])}
    if name == "create_project":
        return {"template": rng.choice(["blank", "finance", "marketing", "churn"])}
    return None


def add_event(u, s, ts, name, props):
    e = dict(user=u, session=s, ts=secs(ts), name=name, props=props)
    events.append(e)
    if s is not None:
        s["events"].append(e)
    return e


def session_times(u, start, end, rate_per_week):
    """Poisson session starts between start and end with weekday weighting."""
    out = []
    if end <= start or rate_per_week <= 0:
        return out
    weeks = (end - start).total_seconds() / (7 * 86400)
    n = poisson(rate_per_week * weeks * 1.25)
    for _ in range(n):
        d = rand_day(start, end + timedelta(days=1))
        if d.weekday() >= 5 and rng.random() < 0.6:
            continue
        t = business_time(d)
        if start <= t < end:
            out.append(t)
    return sorted(out)


def gen_sessions():
    rate = {"dormant": 0.0, "casual": 0.05, "regular": 0.75, "power": 1.6}
    onboard = {"dormant": 0.3, "casual": 0.55, "regular": 1.8, "power": 2.6}
    for u in users:
        u["sessions"] = []
        end = u["active_until"] or DATA_END
        # first session shortly after signup (most users)
        if rng.random() < (0.55 if u["arche"] == "dormant" else 0.93):
            new_session(u, u["signup_at"] + timedelta(minutes=rng.randint(1, 90)))
        for _ in range(poisson(onboard[u["arche"]])):
            t = u["signup_at"] + timedelta(days=rng.uniform(0.5, 14), hours=rng.uniform(0, 6))
            if t < end and t < DATA_END:
                new_session(u, t)
        for t in session_times(u, u["signup_at"] + timedelta(days=14), end, rate[u["arche"]]):
            new_session(u, t)


# ------------------------------------------------------------ experiments
EXPERIMENTS = [
    (1, "pricing_page_v2", "A redesigned pricing page increases checkout conversion.",
     "purchase_conversion_14d", date(2024, 3, 4), date(2024, 4, 14), "completed"),
    (2, "annual_discount_banner", "Showing the annual discount increases purchases.",
     "purchase_conversion_14d", date(2024, 9, 2), date(2024, 10, 13), "completed"),
    (3, "ai_assist_default_on", "Enabling AI assist by default increases adoption.",
     "ai_assist_adoption_14d", date(2024, 11, 4), date(2024, 12, 15), "completed"),
    (4, "onboarding_checklist", "An in-app checklist increases week-1 retention of new users.",
     "week1_retention", date(2024, 12, 2), date(2025, 2, 9), "completed"),
    (5, "checkout_one_page", "A one-page checkout increases purchases (two treatment designs).",
     "purchase_conversion_14d", date(2025, 2, 3), date(2025, 3, 16), "completed"),
    (6, "rag_answer_citations", "Showing citations in support-bot answers increases thumbs-up rate.",
     "answer_thumbs_up_rate", date(2025, 5, 5), None, "running"),
]
assignments = []
extra_orders = []   # (user, ts) purchase intents created by experiments


def gen_experiments():
    for e in EXPERIMENTS:
        rows["experiments"].append(dict(experiment_id=e[0], experiment_name=e[1], hypothesis=e[2],
                                        primary_metric=e[3], start_date=e[4], end_date=e[5],
                                        status=e[6]))
    for e in EXPERIMENTS:
        eid, name, s, en = e[0], e[1], e[4], e[5]
        start = datetime(s.year, s.month, s.day)
        end = datetime(en.year, en.month, en.day) + timedelta(days=1) if en else DATA_END
        for u in users:
            if name == "onboarding_checklist":
                if not (start <= u["signup_at"] < end) or "dup_of" in u:
                    continue
                at = u["signup_at"] + timedelta(seconds=rng.randint(5, 50))
                variant = "control" if rng.random() < 0.65 else "treatment"   # SRM on purpose
            else:
                first = next((x for x in u["sessions"] if start <= x["start"] < end), None)
                if first is None:
                    continue
                at = first["start"] + timedelta(seconds=rng.randint(2, 30))
                if name == "checkout_one_page":
                    variant = rng.choice(["control", "treatment", "treatment_b"])
                else:
                    variant = rng.choice(["control", "treatment"])
            assignments.append(dict(experiment_id=eid, user=u, variant=variant, assigned_at=secs(at)))
            u.setdefault("exp", {})[eid] = (variant, secs(at))
            seg = u["org"]["segment"]
            # treatment effects
            if name in ("pricing_page_v2", "annual_discount_banner", "checkout_one_page"):
                # conversion inside the 14-day window is fully controlled here; organic
                # orders are suppressed inside the window (see in_purchase_experiment_window)
                base = 0.22
                lift = {"pricing_page_v2": {"treatment": 0.08},
                        "annual_discount_banner": {"treatment": 0.01},
                        "checkout_one_page": {"treatment": 0.08, "treatment_b": 0.025}}[name]
                p = base + lift.get(variant, 0.0)
                if name == "checkout_one_page" and variant != "control" and seg == "Enterprise":
                    p = 0.09                  # heterogeneous effect: hurts Enterprise
                if rng.random() < p:
                    t = at + timedelta(hours=rng.uniform(0.2, 13 * 24))
                    if t < DATA_END:
                        extra_orders.append((u, secs(t)))
            elif name == "onboarding_checklist":
                p = 0.28 if variant == "treatment" else 0.18
                if rng.random() < p:
                    t = at + timedelta(days=rng.uniform(1.2, 6.5))
                    if t < DATA_END and (u["active_until"] is None or t < u["active_until"]):
                        new_session(u, t)
            elif name == "ai_assist_default_on":
                p = 0.45 if variant == "treatment" else 0.22
                if rng.random() < p:
                    t = at + timedelta(days=rng.uniform(0.1, 13))
                    if t < DATA_END:
                        s = new_session(u, t, n_events=0)
                        add_event(u, s, s["start"] + timedelta(seconds=40), "ai_assist_used",
                                  {"feature": "sql_copilot"})


# ----------------------------------------------------------------- orders
orders = []


def pick_product(ts):
    d = ts.date()
    cands = []
    for pid, p in enumerate(PRODUCTS, 1):
        if p[4] > d:
            continue
        if not p[3] and d >= DISCONTINUED_ON:
            continue
        cands.append((pid, PRODUCT_WEIGHTS[p[1]]))
    return wchoice(cands)


PURCHASE_EXPERIMENTS = (1, 2, 5)


def in_purchase_experiment_window(u, ts):
    for eid in PURCHASE_EXPERIMENTS:
        if eid in u.get("exp", {}):
            at = u["exp"][eid][1]
            if at <= ts < at + timedelta(days=14):
                return True
    return False


def make_order(u, ts, channel=None):
    o = dict(user=u, ts=secs(ts), channel=channel or wchoice([("web", 70), ("sales", 20), ("marketplace", 10)]))
    age = (DATA_END - ts).days
    if age < 20 and rng.random() < 0.25:
        o["status"] = "pending"
    else:
        o["status"] = wchoice([("completed", 85), ("refunded", 8), ("canceled", 7)])
    codes = [("WELCOME10", date(2024, 1, 1), date(2025, 7, 1), 0.10),
             ("SPRING24", date(2024, 3, 1), date(2024, 5, 31), 0.15),
             ("BF2024", date(2024, 11, 25), date(2024, 12, 2), 0.25),
             ("PARTNER15", date(2024, 1, 1), date(2025, 7, 1), 0.15),
             ("SUMMER25", date(2025, 6, 1), date(2025, 7, 1), 0.20)]
    valid = [c for c in codes if c[1] <= ts.date() < c[2]]
    bf = [c for c in valid if c[0] == "BF2024"]
    o["code"] = None
    if bf and rng.random() < 0.6:
        o["code"] = bf[0]
    elif valid and rng.random() < 0.13:
        o["code"] = rng.choice(valid)
    nlines = wchoice([(1, 55), (2, 28), (3, 15), (4, 2)])
    lines, used = [], []
    for ln in range(1, nlines + 1):
        pid = pick_product(ts)
        tries = 0
        while pid in used and tries < 10:
            pid = pick_product(ts)
            tries += 1
        used.append(pid)
        cat = PRODUCTS[pid - 1][1]
        qty = {2: rng.randint(1, 3), 3: wchoice([(1, 50), (2, 25), (3, 10), (5, 10), (10, 5)]),
               5: rng.randint(1, 12), 7: 1, 8: 1, 10: 1, 11: 1}[cat]
        price = PRODUCTS[pid - 1][2]
        if o["channel"] == "sales" and rng.random() < 0.5:
            price = money(price * (1 - rng.choice([0.05, 0.1, 0.15, 0.2, 0.25])))
        disc = money(qty * price * o["code"][3]) if o["code"] else 0.0
        lines.append(dict(line_number=ln, product_id=pid, quantity=qty, unit_price=price,
                          discount_amount=disc))
    o["lines"] = lines
    o["total"] = money(sum(l["quantity"] * l["unit_price"] - l["discount_amount"] for l in lines))
    orders.append(o)
    return o


def gen_orders():
    buy_p = {"dormant": 0.10, "casual": 0.5, "regular": 0.8, "power": 0.9}
    for u in users:
        if "dup_of" in u or not u["sessions"]:
            continue
        p = buy_p[u["arche"]] * (1.3 if u["role"] == "admin" else 1.0)
        if rng.random() >= p:
            continue
        n = 1 + poisson(1.6 if u["arche"] in ("regular", "power") else 0.6)
        for _ in range(n):
            s = rng.choice(u["sessions"])
            ts = s["start"] + timedelta(minutes=rng.uniform(1, 8))
            if s["start"] < DATA_START or ts >= DATA_END:
                continue
            if in_purchase_experiment_window(u, ts):
                continue
            # holiday-season boost: re-draw some orders into Nov/Dec
            make_order(u, ts)
    for u, ts in extra_orders:
        make_order(u, ts, channel="web")
    # a few very large enterprise service orders (outliers)
    ent_users = [u for u in users if u["org"]["segment"] == "Enterprise" and u["sessions"]
                 and "dup_of" not in u]
    for u in rng.sample(ent_users, 8):
        ts = business_time(rand_day(max(u["signup_at"], DATA_START), DATA_END))
        o = make_order(u, ts, channel="sales")
        o["status"] = "completed"
        o["lines"] = [dict(line_number=1, product_id=20, quantity=rng.randint(2, 4),
                           unit_price=12000.0, discount_amount=0.0),
                      dict(line_number=2, product_id=23, quantity=rng.randint(1, 3),
                           unit_price=6500.0, discount_amount=0.0)]
        o["code"] = None
        o["total"] = money(sum(l["quantity"] * l["unit_price"] for l in o["lines"]))
    orders.sort(key=lambda o: (o["ts"], o["user"]["user_id"]))
    for i, o in enumerate(orders, 1):
        o["order_id"] = i
    # 2% header totals that do not match the lines
    for o in rng.sample(orders, int(len(orders) * 0.02)):
        o["total"] = money(max(0.0, o["total"] + rng.choice([-0.01, 0.01, -1.0, 2.5, -5.0, 10.0])))
    # a few orders billed to the parent company (legitimate) and a few to an unrelated org (bug)
    sub_orders = [o for o in orders if o["user"]["org"]["parent_org_id"] is not None]
    for o in rng.sample(sub_orders, min(5, len(sub_orders))):
        o["org_override"] = o["user"]["org"]["parent_org_id"]
    for o in rng.sample([o for o in orders if "org_override" not in o], 5):
        uo = o["user"]["org"]
        o["org_override"] = rng.randint(1, len(orgs))
        if o["org_override"] == uo["org_id"] or o["org_override"] == uo["parent_org_id"]:
            o["org_override"] = (uo["org_id"] % len(orgs)) + 1

    # funnel + purchase events
    for o in orders:
        u = o["user"]
        if o["channel"] == "web":
            s = new_session(u, o["ts"] - timedelta(minutes=rng.uniform(4, 25)), n_events=0)
            if rng.random() < 0.8:
                add_event(u, s, o["ts"] - timedelta(minutes=rng.uniform(2.5, 4)), "view_pricing",
                          {"page": "/pricing", "referrer": rng.choice(["dashboard", "email", "banner"])})
            add_event(u, s, o["ts"] - timedelta(minutes=rng.uniform(0.5, 2)), "start_checkout",
                      {"plan": PLAN[rng.choice([2, 3, 4])][1], "cart_lines": len(o["lines"])})
            s["end"] = max(s["end"], o["ts"] + timedelta(minutes=1))
        if o["status"] in ("completed", "refunded"):
            add_event(u, None, o["ts"], "purchase", {"order_id": o["order_id"], "amount": o["total"]})
    # abandoned funnels
    pool = [s for s in sessions if s["start"] >= DATA_START and s["events"]]
    for s in rng.sample(pool, 700):
        u = s["user"]
        t = s["events"][-1]["ts"] + timedelta(seconds=rng.randint(20, 120))
        add_event(u, s, t, "view_pricing", {"page": "/pricing", "referrer": rng.choice(["dashboard", "banner", "docs"])})
        if rng.random() < 0.35:
            add_event(u, s, t + timedelta(seconds=rng.randint(30, 200)), "start_checkout",
                      {"plan": PLAN[rng.choice([2, 3, 4, 5])][1], "cart_lines": rng.randint(1, 3)})
        s["end"] = max(s["end"], s["events"][-1]["ts"] + timedelta(seconds=30))


def finalize_orders():
    pid_ = 0
    for o in orders:
        org_id = o.get("org_override") or o["user"]["org"]["org_id"]
        rows["orders"].append(dict(order_id=o["order_id"], user_id=o["user"]["user_id"], org_id=org_id,
                                   order_ts=o["ts"], status=o["status"], sales_channel=o["channel"],
                                   discount_code=o["code"][0] if o["code"] else None,
                                   order_total=o["total"]))
        for l in o["lines"]:
            rows["order_items"].append(dict(order_id=o["order_id"], **l))
        pays = []
        t = o["ts"] + timedelta(seconds=rng.randint(5, 90))
        if o["status"] in ("completed", "refunded"):
            for _ in range(wchoice([(0, 88), (1, 9), (2, 3)])):
                pays.append(dict(at=t, status="failed", reason=wchoice([("card_declined", 50), ("insufficient_funds", 20),
                                                                       ("expired_card", 15), ("network_error", 15)])))
                t = t + timedelta(minutes=rng.randint(2, 600))
            p = dict(at=t, status="succeeded", reason=None)
            if o["status"] == "refunded":
                p["status"] = "refunded"
                p["ref_amt"] = o["total"] if rng.random() < 0.7 else money(o["total"] * rng.choice([0.25, 0.5]))
                p["ref_at"] = t + timedelta(days=rng.randint(1, 25), hours=rng.randint(0, 12))
                if p["ref_at"] >= DATA_END:
                    p["ref_at"] = DATA_END - timedelta(hours=2)
            pays.append(p)
        elif o["status"] == "canceled":
            if rng.random() < 0.5:
                pays.append(dict(at=t, status="failed", reason="card_declined"))
        elif o["status"] == "pending":
            if rng.random() < 0.7:
                pays.append(dict(at=t, status="pending", reason=None))
        o["pays"] = pays
    # completed orders with no payment row recorded
    completed = [o for o in orders if o["status"] == "completed"]
    for o in rng.sample(completed, 14):
        o["pays"] = []
    allp = []
    for o in orders:
        for p in o["pays"]:
            allp.append((p["at"], o, p))
    allp.sort(key=lambda x: (x[0], x[1]["order_id"]))
    for p_id, (at, o, p) in enumerate(allp, 1):
        rows["payments"].append(dict(payment_id=p_id, order_id=o["order_id"], attempted_at=secs(at),
                                     amount=o["total"], method=method_for(o), status=p["status"],
                                     failure_reason=p["reason"], refunded_amount=p.get("ref_amt"),
                                     refunded_at=secs(p["ref_at"]) if p.get("ref_at") else None))


def method_for(o):
    if "method" not in o:
        o["method"] = (wchoice([("invoice", 60), ("bank_transfer", 40)]) if o["channel"] == "sales"
                       else wchoice([("card", 66), ("bank_transfer", 12), ("paypal", 16), ("invoice", 6)]))
    return o["method"]


def finalize_sessions_events():
    # duplicate client events (client retries)
    client = [e for e in events if e["session"] is not None]
    for e in rng.sample(client, int(len(client) * 0.015)):
        d = dict(e)
        events.append(d)
        e["session"]["events"].append(d)
    sessions.sort(key=lambda s: (s["start"], s["user"]["user_id"]))
    for i, s in enumerate(sessions, 1):
        s["session_id"] = i
        rows["sessions"].append(dict(session_id=i, user_id=s["user"]["user_id"], started_at=s["start"],
                                     ended_at=None if s.get("end_null") else s["end"],
                                     device_type=s["device"], app_version=s["version"]))
    events.sort(key=lambda e: (e["ts"], e["user"]["user_id"], e["name"]))
    for i, e in enumerate(events, 1):
        rows["events"].append(dict(event_id=i, user_id=e["user"]["user_id"],
                                   session_id=e["session"]["session_id"] if e["session"] else None,
                                   event_ts=e["ts"], event_name=e["name"],
                                   properties=e["props"]))
    for u in users:
        starts = sorted(s["start"] for s in u["sessions"])
        u["session_starts"] = starts
        u["session_durations"] = sorted(((s["start"], None if s.get("end_null") else (s["end"] - s["start"]).total_seconds() / 60)
                                         for s in u["sessions"]), key=lambda x: x[0])
        last = starts[-1] if starts else None
        if u["active_until"] is not None and u["active_until"] < datetime(2025, 3, 1):
            status = "deleted" if rng.random() < 0.25 else "inactive"
        else:
            status = "active"
        if u["org"]["is_deleted"]:
            status = rng.choice(["inactive", "deleted"])
        rows["users"].append(dict(
            user_id=u["user_id"], org_id=u["org"]["org_id"], email=u["email"],
            full_name=f"{u['first']} {u['last']}", role=u["role"], signup_at=u["signup_at"],
            last_login_at=last, status=status, acquisition_channel=u["channel"],
            country_code=(None if rng.random() < 0.03 else
                          (u["org"]["country_code"] if rng.random() < 0.86 else rng.choice(COUNTRIES)[0])),
            referred_by_user_id=u["referred_by"],
            marketing_opt_in=wchoice([(True, 40), (False, 45), (None, 15)])))
    # event timestamps per user (for features)
    per_user = {}
    for e in events:
        per_user.setdefault(e["user"]["user_id"], []).append(e["ts"])
    for u in users:
        u["event_ts"] = sorted(per_user.get(u["user_id"], []))


def finalize_orgs():
    for o in orgs:
        rows["organizations"].append(dict(org_id=o["org_id"], org_name=o["org_name"],
                                          parent_org_id=o["parent_org_id"], industry=o["industry"],
                                          segment=o["segment"], employee_band=o["employee_band"],
                                          country_code=o["country_code"], timezone=o["timezone"],
                                          created_at=o["created_at"], is_deleted=o["is_deleted"],
                                          deleted_at=secs(o["deleted_at"]) if o["deleted_at"] else None))
    for a in sorted(assignments, key=lambda a: (a["experiment_id"], a["user"]["user_id"])):
        rows["experiment_assignments"].append(dict(experiment_id=a["experiment_id"],
                                                   user_id=a["user"]["user_id"], variant=a["variant"],
                                                   assigned_at=a["assigned_at"]))


# ---------------------------------------------------------------- tickets
def gen_tickets():
    tickets = []
    for o in orgs:
        ousers = [u for u in users if u["org"] is o]
        end = min(o["churned_at"] or DATA_END, DATA_END)
        start = max(o["created_at"], DATA_START)
        months = max(0.0, (end - start).days / 30.4)
        n = poisson(months * (0.16 * len(ousers) ** 0.8))
        if o["churned_at"] and o["churned_at"] > DATA_START:
            n += poisson(2.5)   # pre-churn spike
        for _ in range(n):
            if o["churned_at"] and rng.random() < 0.3:
                created = rand_between(max(start, o["churned_at"] - timedelta(days=60)), end)
            else:
                created = business_time(rand_day(start, end))
            if created >= DATA_END or created < start:
                continue
            cat = wchoice([("billing", 20), ("bug", 28), ("how_to", 30), ("feature_request", 10),
                           ("account", 7), ("ai_quality", 5 if created >= AI_LAUNCH else 0)])
            pri = wchoice([("low", 30), ("medium", 45), ("high", 18), ("urgent", 7)])
            cand = [u for u in ousers if u["signup_at"] <= created]
            user = None if (rng.random() < 0.1 or not cand) else rng.choice(cand)
            tickets.append(dict(org=o, user=user, created=created, cat=cat, pri=pri))
    tickets.sort(key=lambda t: (t["created"], t["org"]["org_id"]))
    for i, t in enumerate(tickets, 1):
        age_days = (DATA_END - t["created"]).days
        resp_h = rng.lognormvariate(math.log({"urgent": 0.6, "high": 2, "medium": 6, "low": 14}[t["pri"]]), 0.9)
        first = t["created"] + timedelta(hours=resp_h)
        res_h = resp_h + rng.lognormvariate(math.log({"urgent": 6, "high": 20, "medium": 48, "low": 90}[t["pri"]]), 1.0)
        if rng.random() < 0.01:
            res_h *= 15                       # very slow outliers
        resolved = t["created"] + timedelta(hours=res_h)
        if age_days > 30 or resolved < DATA_END - timedelta(days=1):
            status = wchoice([("closed", 60), ("resolved", 40)]) if resolved < DATA_END else "pending"
        else:
            status = wchoice([("open", 50), ("pending", 50)])
        if status in ("open", "pending"):
            resolved = None
            if status == "open" and rng.random() < 0.5:
                first = None
        if first is not None and first >= DATA_END:
            first = None
        csat = None
        if resolved is not None and rng.random() < 0.45:
            slow = res_h > 72
            csat = wchoice([(5, 30), (4, 30), (3, 15), (2, 10), (1, 5)] if not slow else
                           [(5, 10), (4, 20), (3, 25), (2, 25), (1, 20)])
        rows["support_tickets"].append(dict(
            ticket_id=i, org_id=t["org"]["org_id"], user_id=t["user"]["user_id"] if t["user"] else None,
            created_at=secs(t["created"]), first_response_at=secs(first) if first else None,
            resolved_at=secs(resolved) if resolved else None, priority=t["pri"], category=t["cat"],
            status=status, channel=wchoice([("email", 40), ("chat", 30), ("phone", 10), ("web_form", 20)]),
            csat_score=csat))
    return rows["support_tickets"]


# --------------------------------------------------------------------- ML
FEATURE_STORE_LAUNCH = datetime(2024, 9, 15, 3, 0, 0)
SNAPSHOTS = [datetime(2024, 10, 7) + timedelta(days=14 * i) for i in range(20)]   # .. 2025-06-30
OUTAGE = [datetime(2025, 2, 24), datetime(2025, 3, 10)]
BACKFILL_AT = datetime(2025, 3, 20, 11, 15, 0)
OBS_DATES = [add_months(datetime(2024, 11, 1), i) for i in range(8)]                # .. 2025-06-01


def count_between(sorted_list, a, b):
    return bisect.bisect_left(sorted_list, b) - bisect.bisect_left(sorted_list, a)


def gen_ml():
    # entities: users who reached activation (3rd session), registered no earlier than launch
    ents = []
    for u in users:
        if len(u["session_starts"]) >= 3 and "dup_of" not in u:
            third = u["session_starts"][2]
            if third < datetime(2025, 5, 1):
                reg = max(third, FEATURE_STORE_LAUNCH) + timedelta(hours=rng.randint(1, 30))
                ents.append((reg, u))
    ents.sort(key=lambda x: (x[0], x[1]["user_id"]))
    entities = []
    test_ids = rng.sample(range(len(ents)), 18)
    for i, (reg, u) in enumerate(ents, 1):
        e = dict(entity_id=i, user=u, registered_at=secs(reg), is_test=(i - 1) in test_ids)
        entities.append(e)
        rows["ml_entities"].append(dict(entity_id=i, user_id=u["user_id"], org_id=u["org"]["org_id"],
                                        registered_at=e["registered_at"], is_test_account=e["is_test"]))
    # org seat usage helper
    org_seats = {}
    for s in rows["subscriptions"]:
        org_seats.setdefault(s["org_id"], []).append(s)
    tickets_by_org = {}
    for t in rows["support_tickets"]:
        tickets_by_org.setdefault(t["org_id"], []).append(t)
    org_users = {}
    for u in users:
        org_users.setdefault(u["org"]["org_id"], []).append(u)

    def seats_at(org_id, ts):
        best = None
        for s in org_seats.get(org_id, []):
            if s["started_at"] <= ts and (s["ended_at"] is None or ts < s["ended_at"]):
                best = s
        return best["seats"] if best else None

    feats = {}
    for e in entities:
        u = e["user"]
        for snap in SNAPSHOTS:
            if snap < e["registered_at"]:
                continue
            if snap not in OUTAGE and rng.random() < 0.012:
                continue                         # row silently missing (partial pipeline run)
            ss = u["session_starts"]
            s7 = count_between(ss, snap - timedelta(days=7), snap)
            s28 = count_between(ss, snap - timedelta(days=28), snap)
            ev28 = count_between(u["event_ts"], snap - timedelta(days=28), snap)
            prev = [x for x in ss if x < snap]
            dsl = (snap - prev[-1]).days if prev else None
            durs = [d for (st, d) in u["session_durations"]
                    if snap - timedelta(days=28) <= st < snap and d is not None]
            avg_m = round(sum(durs) / len(durs), 2) if durs else None
            oid = u["org"]["org_id"]
            opent = sum(1 for t in tickets_by_org.get(oid, [])
                        if t["created_at"] < snap and (t["resolved_at"] is None or t["resolved_at"] >= snap))
            seats = seats_at(oid, snap)
            active = sum(1 for x in org_users[oid] if count_between(x["session_starts"], snap - timedelta(days=28), snap) > 0)
            sup = round(active / seats, 3) if seats else None
            if e["is_test"]:
                s7, s28, ev28 = s7 + 40, s28 + 160, ev28 + 900
            row = dict(entity_id=e["entity_id"], as_of_ts=snap, sessions_7d=s7, sessions_28d=s28,
                       events_28d=ev28, days_since_last_session=dsl, open_tickets=opent,
                       avg_session_minutes=avg_m, seats_used_pct=sup, feature_source="batch")
            for k in ("sessions_7d", "events_28d", "avg_session_minutes", "seats_used_pct", "open_tickets"):
                if rng.random() < 0.007:
                    row[k] = None
            if snap in OUTAGE:
                row["feature_source"] = "backfill"
                row["ingested_at"] = BACKFILL_AT + timedelta(minutes=rng.randint(0, 90))
            elif rng.random() < 0.05:
                row["ingested_at"] = snap + timedelta(days=rng.uniform(1, 3))
            else:
                row["ingested_at"] = snap + timedelta(hours=rng.uniform(2, 6))
            row["ingested_at"] = secs(row["ingested_at"])
            rows["entity_features"].append(row)
            feats[(e["entity_id"], snap)] = row

    # labels: eligible = registered and >=1 session in the 30 days before obs
    label_rows = []
    for obs in OBS_DATES:
        for e in entities:
            if e["registered_at"] > obs:
                continue
            ss = e["user"]["session_starts"]
            if count_between(ss, obs - timedelta(days=30), obs) < 2:
                continue
            if obs + timedelta(days=30) > DATA_END:
                val, avail = None, None
            else:
                val = 1 if count_between(ss, obs, obs + timedelta(days=30)) == 0 else 0
                avail = obs + timedelta(days=30, hours=rng.uniform(4, 30))
                if rng.random() < 0.04:
                    avail = avail + timedelta(days=rng.randint(5, 20))      # delayed labels
                if avail >= DATA_END:
                    val, avail = None, None
            label_rows.append(dict(e=e, obs=obs, val=val, avail=secs(avail) if avail else None))
    # duplicated / conflicting re-runs
    done = [l for l in label_rows if l["val"] is not None]
    for l in rng.sample(done, int(len(label_rows) * 0.01)):
        d = dict(l)
        d["avail"] = secs(l["avail"] + timedelta(days=rng.randint(1, 6), hours=rng.randint(1, 9)))
        if rng.random() < 0.5:
            l["val"] = 1 - d["val"]      # first run was wrong; the later re-run holds the true value
        label_rows.append(d)
    label_rows.sort(key=lambda l: (l["obs"], l["e"]["entity_id"], l["avail"] or DATA_END))
    for i, l in enumerate(label_rows, 1):
        rows["training_labels"].append(dict(label_id=i, entity_id=l["e"]["entity_id"], label_name="churned_30d",
                                            observation_date=l["obs"].date(), label_value=l["val"],
                                            label_available_at=l["avail"]))
    truth = {}
    for l in label_rows:
        truth[(l["e"]["entity_id"], l["obs"])] = l["val"]

    # model registry
    mv = [
        (1, "churn_classifier", "v1", None, "logistic_regression", date(2024, 8, 1), datetime(2024, 9, 20, 14, 0), datetime(2024, 10, 1, 9, 0), datetime(2025, 1, 15, 9, 0), "retired", 0.500,
         {"C": 1.0, "penalty": "l2", "class_weight": None}),
        (2, "churn_classifier", "v2", 1, "gradient_boosting", date(2024, 12, 1), datetime(2025, 1, 10, 16, 30), datetime(2025, 1, 15, 9, 0), datetime(2025, 4, 1, 9, 0), "retired", 0.450,
         {"n_estimators": 300, "max_depth": 4, "learning_rate": 0.05}),
        (3, "churn_classifier", "v3", 2, "gradient_boosting", date(2025, 2, 1), datetime(2025, 3, 25, 11, 0), datetime(2025, 4, 1, 9, 0), None, "production", 0.400,
         {"n_estimators": 500, "max_depth": 5, "learning_rate": 0.03, "scale_pos_weight": 5}),
        (4, "churn_classifier", "v4", 3, "lightgbm", date(2025, 3, 1), datetime(2025, 4, 22, 10, 0), None, None, "shadow", 0.350,
         {"num_leaves": 31, "learning_rate": 0.05, "is_unbalance": True}),
        (5, "upsell_propensity", "v1", None, "logistic_regression", date(2025, 2, 1), datetime(2025, 3, 1, 12, 0), datetime(2025, 3, 10, 9, 0), None, "production", 0.600,
         {"C": 0.5, "penalty": "l1"}),
        (6, "upsell_propensity", "v2", 5, "random_forest", date(2025, 4, 1), datetime(2025, 5, 2, 12, 0), None, None, "archived", 0.550,
         {"n_estimators": 200, "max_depth": 8}),
    ]
    for m in mv:
        rows["model_versions"].append(dict(model_version_id=m[0], model_name=m[1], version_label=m[2],
                                           parent_version_id=m[3], algorithm=m[4], training_data_end=m[5],
                                           trained_at=m[6], deployed_at=m[7], retired_at=m[8], stage=m[9],
                                           default_threshold=m[10], hyperparameters=m[11]))
    noise = {1: 1.25, 2: 0.95, 3: 0.8, 4: 0.7, 5: 1.0}
    preds = []

    def score_for(mid, f, true_val):
        if f is None:
            base = 0.0
        else:
            s28 = f["sessions_28d"] or 0
            dsl = f["days_since_last_session"] if f["days_since_last_session"] is not None else 30
            base = -1.1 - 0.35 * s28 + 0.09 * dsl + (0.25 if (f["open_tickets"] or 0) > 2 else 0.0)
        if true_val == 1:
            base += 1.0
        z = base + rng.gauss(0, noise[mid])
        return round(1 / (1 + math.exp(-z)), 4)

    for obs in OBS_DATES:
        prod = 1 if obs < datetime(2025, 1, 15) else (2 if obs < datetime(2025, 4, 1) else 3)
        runs = [(prod, "a")]
        if obs >= datetime(2025, 5, 1):
            runs.append((4, "a"))      # shadow model scored in parallel
        for mid, suffix in runs:
            thr = {1: 0.5, 2: 0.45, 3: 0.4, 4: 0.35}[mid]
            run_start = obs + timedelta(hours=2, minutes=rng.randint(0, 20))
            for e in entities:
                if e["registered_at"] > obs:
                    continue
                if count_between(e["user"]["session_starts"], obs - timedelta(days=30), obs) < 2:
                    continue
                pt = run_start + timedelta(seconds=rng.randint(0, 5400))
                # latest snapshot available (ingested) at prediction time
                avail = [s for s in SNAPSHOTS if s <= pt and (e["entity_id"], s) in feats
                         and feats[(e["entity_id"], s)]["ingested_at"] <= pt]
                f = feats[(e["entity_id"], avail[-1])] if avail else None
                fas = avail[-1] if avail else None
                tv = truth.get((e["entity_id"], obs))
                sc = score_for(mid, f, tv)
                if rng.random() < 0.01:
                    sc = None
                preds.append(dict(mid=mid, e=e, batch=f"churn-{obs.date()}-{suffix}", at=secs(pt),
                                  score=sc, thr=thr, fas=fas if rng.random() > 0.03 else None))
        # re-run of part of the batch (later, same day) -> duplicates
        if obs in (datetime(2025, 2, 1), datetime(2025, 5, 1)):
            mid = prod
            thr = {1: 0.5, 2: 0.45, 3: 0.4}[mid]
            sub = [p for p in preds if p["batch"] == f"churn-{obs.date()}-a" and p["mid"] == mid]
            for p in rng.sample(sub, int(len(sub) * 0.3)):
                d = dict(p)
                d["batch"] = f"churn-{obs.date()}-b"
                d["at"] = secs(obs + timedelta(hours=9, seconds=rng.randint(0, 3600)))
                d["score"] = None if p["score"] is None else round(min(1.0, max(0.0, p["score"] + rng.gauss(0, 0.03))), 4)
                preds.append(d)
    # leakage bug: the 2025-03-01 run logged the backfilled 2025-02-24 snapshot for some entities
    bug = [p for p in preds if p["batch"] == "churn-2025-03-01-a" and p["fas"] is not None
           and (p["e"]["entity_id"], datetime(2025, 2, 24)) in feats]
    for p in rng.sample(bug, 25):
        p["fas"] = datetime(2025, 2, 24)
    # upsell model: two monthly runs
    for obs in (datetime(2025, 5, 1), datetime(2025, 6, 1)):
        for e in entities:
            if e["registered_at"] > obs or rng.random() < 0.15:
                continue
            pt = obs + timedelta(hours=3, seconds=rng.randint(0, 3000))
            sc = round(rng.betavariate(2, 5), 4)
            preds.append(dict(mid=5, e=e, batch=f"upsell-{obs.date()}-a", at=secs(pt), score=sc, thr=0.6, fas=None))
    preds.sort(key=lambda p: (p["at"], p["mid"], p["e"]["entity_id"]))
    for i, p in enumerate(preds, 1):
        rows["model_predictions"].append(dict(
            prediction_id=i, model_version_id=p["mid"], entity_id=p["e"]["entity_id"], batch_id=p["batch"],
            predicted_at=p["at"], score=p["score"], threshold=p["thr"],
            predicted_label=None if p["score"] is None else (1 if p["score"] >= p["thr"] else 0),
            feature_as_of_ts=p["fas"]))
    # offline evaluations
    ev = {1: {"auc": 0.74, "precision": 0.41, "recall": 0.52, "f1": 0.46, "log_loss": 0.39},
          2: {"auc": 0.81, "precision": 0.48, "recall": 0.61, "f1": 0.54, "log_loss": 0.33},
          3: {"auc": 0.85, "precision": 0.52, "recall": 0.69, "f1": 0.59, "log_loss": 0.30},
          4: {"auc": 0.87, "precision": 0.50, "recall": 0.76, "f1": 0.60, "log_loss": 0.29},
          5: {"auc": 0.71, "precision": 0.35, "recall": 0.44, "f1": 0.39, "log_loss": 0.52},
          6: {"auc": 0.69, "precision": 0.33, "recall": 0.47, "f1": 0.39, "log_loss": 0.55}}
    eid = 0
    for m in mv:
        for split, adj in (("train", 0.06), ("validation", 0.01), ("test", 0.0)):
            for metric, val in ev[m[0]].items():
                eid += 1
                v = val - adj if metric == "log_loss" else min(0.99, val + adj)
                rows["model_evaluations"].append(dict(evaluation_id=eid, model_version_id=m[0], eval_split=split,
                                                      metric_name=metric, metric_value=round(v, 4),
                                                      evaluated_at=m[6] + timedelta(minutes=20 + eid % 7)))
    return entities


# --------------------------------------------------------------------- AI
AREAS = {
    "billing": ["invoice", "refund", "payment method", "annual plan", "seat count", "VAT", "credit card", "proration"],
    "sql_editor": ["query editor", "saved query", "query timeout", "autocomplete", "query history", "parameters"],
    "dashboards": ["dashboard", "chart", "filter", "scheduled refresh", "drill-down", "sharing link"],
    "ai_assist": ["SQL copilot", "AI credits", "support bot", "answer citations", "prompt", "summary"],
    "integrations": ["Snowflake connector", "BigQuery connector", "Kafka source", "webhook", "API token", "CDC sync"],
    "security": ["SSO", "SAML", "audit log", "data retention", "role permissions", "IP allow-list"],
    "admin": ["workspace", "user invite", "seat management", "usage report", "sandbox", "project ownership"],
    "data_import": ["CSV upload", "schema mapping", "data types", "import errors", "incremental load"],
}
VERBS = ["configure", "reset", "enable", "troubleshoot", "update", "export", "connect", "remove", "rotate", "limit"]
SOURCES = [("help_center", "help", 45, "public"), ("api_docs", "api", 20, "public"),
           ("policy", "policy", 10, "customer"), ("release_notes", "release-notes", 10, "public"),
           ("internal_wiki", "wiki", 15, "internal")]
FOOTER = "Still need help? Open the Help menu and choose Contact Support. Our team replies within one business day."


def sentence(area):
    t = rng.choice(AREAS[area])
    v = rng.choice(VERBS)
    templates = [f"To {v} the {t}, open Settings and select the {area.replace('_', ' ')} tab.",
                 f"The {t} can be changed by workspace admins only.",
                 f"If the {t} fails, check the error message and retry after a few minutes.",
                 f"Use the {t} to {v} access for your team.",
                 f"Changes to the {t} apply to new sessions immediately.",
                 f"Billing for the {t} is calculated per seat and month." if area == "billing" else f"The {t} is available on Pro plans and above.",
                 f"Note: the {t} limit is {rng.choice([5, 10, 50, 100, 1000])} per workspace."]
    return rng.choice(templates)


def gen_ai(entities):
    models = [("atlas-large", "Atlas Labs", 128000, False, date(2024, 3, 1)),
              ("atlas-mini", "Atlas Labs", 128000, False, date(2024, 7, 1)),
              ("nimbus-pro", "Nimbus AI", 200000, False, date(2024, 9, 1)),
              ("nimbus-lite", "Nimbus AI", 32000, False, date(2024, 11, 1)),
              ("orbit-8b", "self-hosted", 8192, True, date(2025, 1, 15))]
    for m in models:
        rows["llm_models"].append(dict(model_name=m[0], provider=m[1], context_window=m[2],
                                       is_self_hosted=m[3], released_on=m[4]))
    pricing = [("atlas-large", date(2024, 3, 1), date(2025, 2, 28), 0.01, 0.03),
               ("atlas-large", date(2025, 3, 1), None, 0.005, 0.015),
               ("atlas-mini", date(2024, 7, 1), None, 0.00015, 0.0006),
               ("nimbus-pro", date(2024, 9, 1), date(2025, 4, 30), 0.003, 0.015),
               ("nimbus-pro", date(2025, 5, 1), None, 0.0035, 0.0175),
               ("nimbus-lite", date(2024, 11, 1), None, 0.00025, 0.00125),
               ("orbit-8b", date(2025, 1, 15), None, 0.00002, 0.00002)]
    for p in pricing:
        rows["llm_pricing"].append(dict(model_name=p[0], effective_from=p[1], effective_to=p[2],
                                        input_usd_per_1k=p[3], output_usd_per_1k=p[4]))
    prompts = [("support_answer", 1, datetime(2024, 10, 1, 9), "maya.patel"),
               ("support_answer", 2, datetime(2024, 12, 10, 10), "maya.patel"),
               ("support_answer", 3, datetime(2025, 3, 5, 15), "jonas.weber"),
               ("support_answer", 4, datetime(2025, 5, 20, 11), "maya.patel"),
               ("sql_copilot", 1, datetime(2024, 10, 1, 9), "arjun.iyer"),
               ("sql_copilot", 2, datetime(2025, 1, 20, 13), "arjun.iyer"),
               ("sql_copilot", 3, datetime(2025, 4, 15, 16), "lena.fischer"),
               ("doc_summary", 1, datetime(2024, 11, 1, 9), "omar.khan"),
               ("doc_summary", 2, datetime(2025, 2, 10, 12), "omar.khan")]
    latest = {}
    for p in prompts:
        latest[p[0]] = p[1]
    tmpl = {"support_answer": "You are the Lumen support assistant. Answer using ONLY the context below. Cite sources. Context: {{chunks}} Question: {{question}}",
            "sql_copilot": "You write {{dialect}} SQL for the schema below. Return one query and a short explanation. Schema: {{schema}} Request: {{request}}",
            "doc_summary": "Summarize the document for a busy reader in at most {{max_bullets}} bullet points. Document: {{document}}"}
    for i, p in enumerate(prompts, 1):
        rows["prompts"].append(dict(prompt_version_id=i, prompt_name=p[0], version=p[1],
                                    template_text=f"[v{p[1]}] " + tmpl[p[0]], created_at=p[2], author=p[3],
                                    is_active=(latest[p[0]] == p[1])))
    prompt_ids = {(p[0], p[1]): i for i, p in enumerate(prompts, 1)}
    configs = [(1, "dense_small_512", "embed-small-v2", 512, 0, 5, False, datetime(2024, 9, 20, 10)),
               (2, "dense_large_384_ov64", "embed-large-v3", 384, 64, 5, False, datetime(2025, 1, 25, 10)),
               (3, "hybrid_rerank_k10", "embed-large-v3", 384, 64, 10, True, datetime(2025, 4, 10, 10))]
    for c in configs:
        rows["retrieval_configs"].append(dict(config_id=c[0], config_name=c[1], embedding_model=c[2],
                                              chunk_size_tokens=c[3], chunk_overlap_tokens=c[4], top_k=c[5],
                                              uses_reranker=c[6], created_at=c[7]))

    # ---- documents & chunks
    docs = []
    keys = []
    for src, prefix, w, access in SOURCES:
        n = {"help_center": 150, "api_docs": 60, "policy": 30, "release_notes": 30, "internal_wiki": 50}[src]
        for k in range(n):
            area = rng.choice(list(AREAS))
            if src == "release_notes":
                d = date(2023 + (6 + k) // 12, (6 + k) % 12 + 1, 1)
                key = f"{prefix}/{d.year}-{d.month:02d}"
                title = f"Release notes {d.strftime('%B %Y')}"
            else:
                topic = rng.choice(AREAS[area])
                slug = topic.lower().replace(" ", "-").replace("/", "-")
                key = f"{prefix}/{area.replace('_', '-')}/{rng.choice(VERBS)}-{slug}"
                while key in keys:
                    key = key + "-" + str(rng.randint(2, 9))
                title = f"How to {key.split('/')[-1].split('-')[0]} {topic}" if src == "help_center" else f"{topic.title()} ({src.replace('_', ' ')})"
            keys.append(key)
            docs.append(dict(key=key, area=area, src=src, access=access, title=title))
    rows_docs = []
    for d in docs:
        nver = wchoice([(1, 50), (2, 28), (3, 14), (4, 6), (5, 2)])
        t = rand_between(datetime(2023, 6, 1), datetime(2025, 5, 15))
        lang = wchoice([("en", 80), ("de", 8), ("fr", 6), ("es", 4), (None, 2)])
        words = int(rng.lognormvariate(math.log(700), 0.7))
        words = max(80, min(4000, words))
        d["versions"] = []
        deleted = rng.random() < 0.03
        for v in range(1, nver + 1):
            created = t
            if created >= DATA_END - timedelta(days=1):
                break
            nxt = created + timedelta(days=rng.randint(15, 160))
            upd = created + timedelta(days=rng.uniform(0, 10)) if rng.random() < 0.6 else created
            words = max(80, min(4000, int(words * rng.uniform(0.85, 1.25))))
            d["versions"].append(dict(doc=d, v=v, created=secs(created), updated=secs(min(upd, DATA_END - timedelta(hours=1))),
                                      words=words, lang=lang, deleted=deleted))
            t = nxt
            if t >= DATA_END:
                break
        vers = d["versions"]
        for i, ver in enumerate(vers):
            last = (i == len(vers) - 1)
            ver["status"] = "archived"
            if last:
                ver["status"] = "published"
        if len(vers) >= 2 and rng.random() < 0.08:
            vers[-1]["status"] = "draft"
            vers[-2]["status"] = "published"
        # a later edit of the published version that was never re-indexed
        for ver in vers:
            ver["indexed"] = ver["updated"] + timedelta(hours=rng.uniform(0.2, 20))
        pub = [x for x in vers if x["status"] == "published"][-1]
        r = rng.random()
        if r < 0.10 and pub["updated"] < DATA_END - timedelta(days=3):
            pub["indexed"] = pub["updated"] + timedelta(hours=rng.uniform(0.2, 5))
            pub["updated"] = secs(min(pub["indexed"] + timedelta(days=rng.uniform(1, 90)), DATA_END - timedelta(hours=3)))
        elif r < 0.14:
            pub["indexed"] = None
        for x in vers:
            if x["status"] == "draft":
                x["indexed"] = None
        if vers and vers[-1]["status"] == "draft" and rng.random() < 0.3:
            vers[-1]["indexed"] = vers[-1]["updated"] + timedelta(hours=2)     # draft leaked into index
        for x in vers:
            if x["indexed"] is not None:
                x["indexed"] = secs(min(x["indexed"], DATA_END - timedelta(minutes=5)))
            tags = rng.sample(AREAS[d["area"]], 2)
            x["meta"] = None if rng.random() < 0.05 else {
                "tags": [tg.lower().replace(" ", "-") for tg in tags],
                "product_area": d["area"],
                "owner_team": {"help_center": "support-content", "api_docs": "dev-rel", "policy": "legal",
                               "release_notes": "product", "internal_wiki": "engineering"}[d["src"]]}
            rows_docs.append(x)
    rows_docs.sort(key=lambda x: (x["created"], x["doc"]["key"], x["v"]))
    for i, x in enumerate(rows_docs, 1):
        x["document_id"] = i
        rows["documents"].append(dict(
            document_id=i, doc_key=x["doc"]["key"], version_number=x["v"], title=x["doc"]["title"],
            source_type=x["doc"]["src"], status=x["status"], language=x["lang"], access_level=x["doc"]["access"],
            word_count=x["words"], created_at=x["created"], updated_at=x["updated"],
            last_indexed_at=x["indexed"], is_deleted=x["deleted"], metadata=x["meta"]))
    # chunks
    chunks = []
    for d in docs:
        prev_texts = []
        vers = d["versions"]
        for i, ver in enumerate(vers):
            n = max(1, min(16, ver["words"] // 90 + 1))
            texts = []
            for k in range(n):
                if k < len(prev_texts) and rng.random() < 0.6:
                    texts.append(prev_texts[k])
                else:
                    texts.append(" ".join(sentence(d["area"]) for _ in range(rng.randint(2, 4))))
            if d["src"] == "help_center" and hash_bucket(d["key"]) < 25:
                texts.append(FOOTER)
            if rng.random() < 0.01 and texts:
                texts.insert(1, texts[0])          # duplicated chunk inside one document
            ver["texts"] = texts
            prev_texts = texts
            if ver["indexed"] is None:
                continue
            superseded = ver["status"] == "archived"
            if superseded and rng.random() > 0.12:
                continue          # cleanup job removed old chunks (most of the time)
            emb = "embed-small-v2" if ver["indexed"] < datetime(2025, 2, 1) else "embed-large-v3"
            for k, tx in enumerate(texts):
                failed = rng.random() < 0.015
                chunks.append(dict(ver=ver, idx=k, text=tx, tokens=max(30, min(520, int(len(tx.split()) * 1.35 + rng.randint(0, 25)))),
                                   hash=sha(tx.lower().strip()), emb=None if failed else emb,
                                   emb_at=None if failed else secs(ver["indexed"] + timedelta(seconds=rng.randint(5, 600)))))
    chunks.sort(key=lambda c: (c["ver"]["document_id"], c["idx"]))
    for i, c in enumerate(chunks, 1):
        c["chunk_id"] = i
        rows["document_chunks"].append(dict(chunk_id=i, document_id=c["ver"]["document_id"], chunk_index=c["idx"],
                                            chunk_text=c["text"], token_count=c["tokens"], content_hash=c["hash"],
                                            embedding_model=c["emb"], embedded_at=c["emb_at"]))
    chunks_by_area = {}
    for c in chunks:
        if c["emb"] is not None:
            chunks_by_area.setdefault(c["ver"]["doc"]["area"], []).append(c)
    chunks_by_key = {}
    for c in chunks:
        chunks_by_key.setdefault(c["ver"]["doc"]["key"], []).append(c)

    # ---- LLM requests
    active_users = [u for u in users if u["sessions"] and "dup_of" not in u]
    heavy_orgs = [o["org_id"] for o in orgs if o["segment"] == "Enterprise"][:2]
    reqs = []
    day = date(2024, 10, 1)
    while day < DATA_END.date():
        prog = (day - date(2024, 10, 1)).days / 273
        n = poisson(10 + 38 * prog)
        if day.weekday() >= 5:
            n = int(n * 0.45)
        for _ in range(n):
            ts = business_time(day)
            cand = None
            for _try in range(8):
                u = rng.choice(active_users)
                if u["signup_at"] <= ts and (u["active_until"] is None or ts < u["active_until"]):
                    cand = u
                    break
            feature = wchoice([("support_bot", 42), ("sql_copilot", 42), ("doc_summary", 16 if ts >= datetime(2024, 11, 1) else 0)])
            reqs.append(dict(ts=secs(ts), user=cand, feature=feature))
        day += timedelta(days=1)
    # burst traffic from two heavy orgs in May 2025 (rate limiting)
    heavy_users = [u for u in active_users if u["org"]["org_id"] in heavy_orgs]
    for _ in range(260):
        u = rng.choice(heavy_users)
        ts = business_time(rand_day(date(2025, 5, 5), date(2025, 5, 24)))
        reqs.append(dict(ts=secs(ts), user=u, feature="sql_copilot", heavy=True))
    # incident day: extra support-bot traffic (users retrying) on 2025-03-18
    for _ in range(30):
        u = rng.choice(active_users)
        reqs.append(dict(ts=secs(business_time(date(2025, 3, 18))), user=u, feature="support_bot"))
    reqs.sort(key=lambda r: r["ts"])

    def model_for(feature, ts):
        if feature == "support_bot":
            if ts < datetime(2025, 3, 10):
                return "atlas-large"
            return wchoice([("nimbus-pro", 70), ("atlas-large", 30)])
        if feature == "sql_copilot":
            if ts < datetime(2025, 2, 1):
                return "atlas-mini"
            return wchoice([("orbit-8b", 50), ("atlas-mini", 50)])
        return "nimbus-lite"

    def prompt_for(feature, ts):
        name = {"support_bot": "support_answer", "sql_copilot": "sql_copilot", "doc_summary": "doc_summary"}[feature]
        vers = [(p[1], p[2]) for p in prompts if p[0] == name and p[2] <= ts]
        if not vers:
            return None
        cur = vers[-1]
        if len(vers) >= 2 and ts < cur[1] + timedelta(days=14) and rng.random() < 0.5:
            cur = vers[-2]     # 2-week 50/50 rollout of a new prompt version
        return prompt_ids[(name, cur[0])]

    def config_for(ts):
        if ts < datetime(2025, 2, 1):
            return 1
        if ts < datetime(2025, 4, 15):
            return 3 if (ts >= datetime(2025, 4, 10) and rng.random() < 0.2) else 2
        return 3

    req_rows, rc_rows = [], []
    lat_med = {"atlas-large": 2400, "atlas-mini": 900, "nimbus-pro": 1800, "nimbus-lite": 700, "orbit-8b": 450}
    for i, r in enumerate(reqs, 1):
        u = r["user"]
        org_id = u["org"]["org_id"] if u else rng.choice(orgs[:150])["org_id"]
        feature, ts = r["feature"], r["ts"]
        model = model_for(feature, ts)
        pv = None if rng.random() < 0.04 else prompt_for(feature, ts)
        cfg = config_for(ts) if feature == "support_bot" else None
        status = wchoice([("success", 935), ("error", 25), ("timeout", 15), ("rate_limited", 15),
                          ("content_filtered", 10 if feature == "support_bot" else 0)])
        if feature == "support_bot" and ts.date() == date(2025, 3, 18) and rng.random() < 0.8:
            model = "nimbus-pro"
        if model == "nimbus-pro" and ts.date() == date(2025, 3, 18):
            status = wchoice([("success", 40), ("error", 35), ("timeout", 25)])
        if r.get("heavy") and rng.random() < 0.3:
            status = "rate_limited"
        err = {"success": None, "error": rng.choice(["provider_5xx", "invalid_request", "context_length_exceeded"]),
               "timeout": "gateway_timeout", "rate_limited": "429_too_many_requests",
               "content_filtered": "safety_block"}[status]
        k = rows["retrieval_configs"][cfg - 1]["top_k"] if cfg else 0
        if feature == "support_bot":
            inp = int(450 + k * rng.uniform(180, 380) + rng.lognormvariate(math.log(120), 0.6))
        elif feature == "sql_copilot":
            inp = int(rng.lognormvariate(math.log(1100), 0.5))
        else:
            inp = int(rng.lognormvariate(math.log(4200), 0.6))
        if rng.random() < 0.002:
            inp = rng.randint(60000, 120000)      # pasted logs
        ctx = {m[0]: m[2] for m in models}[model]
        if inp > ctx:
            status, err = "error", "context_length_exceeded"
        out = None
        if status == "success":
            out = int(rng.lognormvariate(math.log({"support_bot": 260, "sql_copilot": 180, "doc_summary": 320}[feature]), 0.5))
        cache = status == "success" and feature != "doc_summary" and rng.random() < 0.06
        if status == "rate_limited":
            lat = None
        elif status == "timeout":
            lat = 30000 + rng.randint(0, 900)
        elif cache:
            lat = rng.randint(40, 160)
        else:
            lat = int(rng.lognormvariate(math.log(lat_med[model]), 0.45) + (out or 0) * rng.uniform(4, 9)
                      + (150 if cfg else 0))
            if rng.random() < 0.006:
                lat *= rng.randint(5, 9)
        trace = uuid_like()
        if rng.random() < 0.02 or (date(2025, 4, 7) <= ts.date() <= date(2025, 4, 9) and rng.random() < 0.4):
            trace = None
        meta = None if rng.random() < 0.03 else {
            "temperature": rng.choice([0.0, 0.2, 0.2, 0.3, 0.7]),
            "client": wchoice([("web", 70), ("api", 20), ("slack", 10)]),
            "region": wchoice([("us-east", 50), ("eu-west", 35), ("ap-south", 15)])}
        if meta is not None and rng.random() < 0.3:
            meta["session_ref"] = hexid(6)
        if meta is not None and rng.random() < 0.025:
            del meta["region"]                   # older SDK versions did not send the region
        req_rows.append(dict(request_id=i, trace_id=trace, org_id=org_id, user_id=u["user_id"] if u and rng.random() > 0.03 else None,
                             feature=feature, model_name=model, prompt_version_id=pv, retrieval_config_id=cfg,
                             requested_at=ts, status=status, error_code=err, latency_ms=lat, input_tokens=inp,
                             output_tokens=out, cache_hit=cache, request_metadata=meta))
        r["row"] = req_rows[-1]
        # retrieval
        r["stale"] = False
        if cfg and status != "rate_limited":
            area = rng.choice(list(AREAS))
            pool = [c for c in chunks_by_area.get(area, []) if c["emb_at"] <= ts]
            if len(pool) >= k:
                picked = rng.sample(pool, k)
                sims = sorted((round(rng.uniform(0.55, 0.93), 4) for _ in range(k)), reverse=True)
                for rank, (c, sim) in enumerate(zip(picked, sims), 1):
                    rc_rows.append(dict(request_id=i, rank_position=rank, chunk_id=c["chunk_id"], similarity=sim))
                    if c["ver"]["status"] != "published":
                        r["stale"] = True
    rows["llm_requests"] = req_rows
    rows["llm_request_chunks"] = rc_rows

    # ---- feedback
    fb = []
    for r in reqs:
        row = r["row"]
        if row["status"] != "success" or rng.random() > 0.22:
            continue
        p_up = 0.72
        pv = row["prompt_version_id"]
        if pv == 3:
            p_up -= 0.12
        if pv == 4:
            p_up += 0.06
        if row["retrieval_config_id"] == 3:
            p_up += 0.06
        if row["model_name"] == "orbit-8b":
            p_up -= 0.08
        if r["stale"]:
            p_up -= 0.15
        if row["latency_ms"] and row["latency_ms"] > 8000:
            p_up -= 0.2
        u = r["user"]
        if u and 6 in u.get("exp", {}) and u["exp"][6][1] <= row["requested_at"] and row["feature"] == "support_bot":
            p_up += 0.10 if u["exp"][6][0] == "treatment" else 0.0
        kind = "thumbs_up" if rng.random() < p_up else "thumbs_down"
        if rng.random() < 0.01:
            kind = "flag"
        reason = None
        if kind == "thumbs_down":
            reason = wchoice([("inaccurate", 35), ("irrelevant", 25), ("too_slow", 15 if (row["latency_ms"] or 0) > 5000 else 3),
                              ("outdated", 25 if r["stale"] else 5), (None, 20)])
        elif kind == "flag":
            reason = "unsafe"
        elif rng.random() < 0.3:
            reason = "helpful"
        comment = None
        if rng.random() < 0.12:
            comment = {"thumbs_up": "Exactly what I needed, thanks!", "thumbs_down": rng.choice(
                ["The answer refers to an old setting that no longer exists.", "Wrong table names in the SQL.",
                 "Took too long to respond.", "Did not answer my question."]),
                "flag": "Answer included internal information."}[kind]
        t = row["requested_at"] + timedelta(seconds=rng.randint(10, 900))
        fb.append(dict(request_id=row["request_id"], user_id=row["user_id"], feedback_type=kind,
                       reason_tag=reason, comment_text=comment, created_at=secs(t)))
        if rng.random() < 0.08:          # changed mind
            kind2 = "thumbs_down" if kind == "thumbs_up" else "thumbs_up"
            fb.append(dict(request_id=row["request_id"], user_id=row["user_id"], feedback_type=kind2,
                           reason_tag="inaccurate" if kind2 == "thumbs_down" else None, comment_text=None,
                           created_at=secs(t + timedelta(minutes=rng.randint(1, 600)))))
    fb.sort(key=lambda f: (f["created_at"], f["request_id"]))
    for i, f in enumerate(fb, 1):
        rows["ai_feedback"].append(dict(feedback_id=i, **f))

    # ---- offline retrieval evaluation
    candidates = [d for d in docs if d["key"] in chunks_by_key and d["src"] in ("help_center", "api_docs", "policy")
                  and not d["versions"][0]["deleted"]]
    qdocs = rng.sample(candidates, min(200, len(candidates)))
    qrows = []
    for i, d in enumerate(qdocs, 1):
        topic = rng.choice(AREAS[d["area"]])
        qt = wchoice([("how_to", 40), ("troubleshooting", 25), ("lookup", 20), ("policy", 15 if d["src"] == "policy" else 0)])
        text = {"how_to": f"How do I {rng.choice(VERBS)} the {topic}?",
                "troubleshooting": f"Why does my {topic} keep failing?",
                "lookup": f"What is the limit for {topic}?",
                "policy": f"What is your policy on {topic}?"}[qt]
        qrows.append(dict(query_id=i, query_text=text, gold_doc_key=d["key"], query_type=qt,
                          created_at=secs(datetime(2025, 1, 20, 9) + timedelta(minutes=i * 7))))
        d["_q"] = i
    rows["eval_queries"] = qrows
    quality = {1: 0.55, 2: 0.70, 3: 0.82}
    ev_at = {1: datetime(2025, 1, 28, 2), 2: datetime(2025, 2, 3, 2), 3: datetime(2025, 4, 12, 2)}
    for cfg in (1, 2, 3):
        k = rows["retrieval_configs"][cfg - 1]["top_k"]
        for d in qdocs:
            qid = d["_q"]
            gold = [c for c in chunks_by_key[d["key"]] if c["emb"] is not None]
            area_pool = [c for c in chunks_by_area[d["area"]] if c["ver"]["doc"]["key"] != d["key"]]
            picks = [None] * k
            if gold and rng.random() < quality[cfg]:
                n_rel = min(len(gold), 1 + poisson(0.8 if cfg == 3 else 0.4))
                ranks = []
                for _ in range(n_rel):
                    r_ = min(k, 1 + int(rng.expovariate(1 / (0.6 if cfg == 3 else 1.6))))
                    while r_ in ranks and r_ < k:
                        r_ += 1
                    if r_ not in ranks:
                        ranks.append(r_)
                for c, r_ in zip(rng.sample(gold, len(ranks)), ranks):
                    picks[r_ - 1] = c
            others = rng.sample(area_pool, k)
            for j in range(k):
                if picks[j] is None:
                    picks[j] = others[j]
            sims = sorted((round(rng.uniform(0.5, 0.95), 4) for _ in range(k)), reverse=True)
            for rank, (c, sim) in enumerate(zip(picks, sims), 1):
                rel = c["ver"]["doc"]["key"] == d["key"]
                if rng.random() < 0.02:
                    rel = not rel
                if rng.random() < 0.03:
                    rel = None
                rows["retrieval_evaluations"].append(dict(config_id=cfg, query_id=qid, rank_position=rank,
                                                          chunk_id=c["chunk_id"], similarity=sim, is_relevant=rel,
                                                          evaluated_at=ev_at[cfg]))


def decay_eval_set():
    """The golden set was written in January 2025; since then two documents were
    renamed (their old keys no longer exist) and three were deleted."""
    q = rows["eval_queries"]
    picks = rng.sample(range(len(q)), 5)
    for i in picks[:2]:
        q[i]["gold_doc_key"] = q[i]["gold_doc_key"].replace("help/", "kb/", 1).replace("api/", "dev/", 1).replace("policy/", "legal/", 1)
    for i in picks[2:]:
        key = q[i]["gold_doc_key"]
        for d in rows["documents"]:
            if d["doc_key"] == key:
                d["is_deleted"] = True


def hash_bucket(s):
    return int(hashlib.md5(s.encode()).hexdigest()[:4], 16) % 100


# --------------------------------------------------------------- pipelines
def gen_pipelines():
    runs = []
    d = date(2025, 1, 1)
    skip = {("events_ingest", date(2025, 4, 12)), ("events_ingest", date(2025, 4, 13)),
            ("events_ingest", date(2025, 5, 30)), ("doc_indexer", date(2025, 3, 9)),
            ("feature_build", date(2025, 6, 14))}
    while d < DATA_END.date():
        for name, hour, base_rows in (("events_ingest", 1, 1800), ("feature_build", 2, 950),
                                      ("label_build", 4, 900), ("doc_indexer", 3, 300)):
            if name == "label_build" and d.weekday() != 0:
                continue
            if (name, d) in skip:
                continue
            fail_streak = (name == "feature_build" and date(2025, 2, 23) <= d <= date(2025, 3, 11)) or \
                          (name == "doc_indexer" and date(2025, 5, 26) <= d <= date(2025, 6, 2))
            attempt = 1
            while True:
                start = datetime(d.year, d.month, d.day, hour) + timedelta(days=1, minutes=rng.randint(0, 25) + 40 * (attempt - 1))
                failed = fail_streak or rng.random() < 0.035
                dur = timedelta(minutes=rng.lognormvariate(math.log(14), 0.4))
                if failed:
                    status, rows_n = "failed", None
                else:
                    status = "success"
                    trend = 1 + (d - date(2025, 1, 1)).days / 250
                    rows_n = int(base_rows * trend * rng.uniform(0.85, 1.15))
                    if name == "events_ingest" and d == date(2025, 5, 12):
                        rows_n = 12           # silent partial failure
                fin = start + dur
                if start >= DATA_END:
                    break
                if fin >= DATA_END:
                    status, fin, rows_n = "running", None, None
                runs.append(dict(pipeline_name=name, run_date=d, attempt=attempt, started_at=secs(start),
                                 finished_at=secs(fin) if fin else None, status=status, rows_processed=rows_n))
                if status != "failed" or attempt >= (1 if fail_streak else 3):
                    break
                if rng.random() < 0.15:
                    break                        # nobody retried
                attempt += 1
        d += timedelta(days=1)
    runs.sort(key=lambda r: (r["started_at"], r["pipeline_name"]))
    for i, r in enumerate(runs, 1):
        rows["pipeline_runs"].append(dict(run_id=i, **r))


# ------------------------------------------------------------------ output
def fmt(v):
    if v is None:
        return ""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, datetime):
        return v.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(v, date):
        return v.isoformat()
    if isinstance(v, (dict, list)):
        return json.dumps(v, ensure_ascii=False, separators=(", ", ": "))
    if isinstance(v, float):
        r = repr(round(v, 6))
        return r[:-2] if r.endswith(".0") else r
    return str(v)


def check_integrity():
    """Fail fast on PK / UNIQUE / FK / NOT NULL violations (intentional data-quality
    issues never violate declared constraints)."""
    by = {t["name"]: t for t in TABLES}
    keysets = {}
    for t in TABLES:
        for key in [t["pk"]] + t["uniques"]:
            seen = set()
            for r in rows[t["name"]]:
                k = tuple(r.get(c) for c in key)
                if any(v is None for v in k):
                    continue
                if k in seen:
                    raise ValueError(f"duplicate {key} in {t['name']}: {k}")
                seen.add(k)
            keysets[(t["name"], tuple(key))] = seen
    for t in TABLES:
        for cols, ref, refcols in t["fks"]:
            ks = keysets[(ref, tuple(refcols))]
            for r in rows[t["name"]]:
                k = tuple(r.get(c) for c in cols)
                if any(v is None for v in k):
                    continue
                if k not in ks:
                    raise ValueError(f"FK violation {t['name']}{cols} -> {ref}: {k}")
    print("  integrity check passed (PK, UNIQUE, FK)")


def write_csvs():
    os.makedirs(OUT, exist_ok=True)
    for t in TABLES:
        cols = [c["name"] for c in t["columns"]]
        path = os.path.join(OUT, f"{t['name']}.csv")
        with open(path, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh, lineterminator="\n")
            w.writerow(cols)
            for r in rows[t["name"]]:
                vals = []
                for c in t["columns"]:
                    v = r.get(c["name"])
                    if v is None and not c["null"]:
                        raise ValueError(f"NULL in NOT NULL column {t['name']}.{c['name']}: {r}")
                    s = fmt(v)
                    if v is not None and s == "":
                        raise ValueError(f"empty string in {t['name']}.{c['name']}")
                    vals.append(s)
                w.writerow(vals)
        print(f"  {t['name']:<24} {len(rows[t['name']]):>7,} rows")


def main():
    print("Generating dataset (seed %d)..." % SEED)
    gen_static()
    gen_orgs()
    gen_subscriptions()
    gen_users()
    gen_sessions()
    gen_experiments()
    gen_orders()
    finalize_orders()
    finalize_sessions_events()
    finalize_orgs()
    gen_tickets()
    ents = gen_ml()
    gen_ai(ents)
    decay_eval_set()
    gen_pipelines()
    check_integrity()
    write_csvs()


if __name__ == "__main__":
    main()

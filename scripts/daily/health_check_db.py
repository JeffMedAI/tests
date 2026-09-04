"""health_check_db.py - database half of the weekday morning health check.

Called by scripts\\daily\\health_check.ps1. Prints ONE JSON object to stdout and
nothing else, so PowerShell can ConvertFrom-Json it directly.

WHY THIS IS SEPARATE FROM THE WATCHDOG
watchdog.ps1 answers "are the services running". It says nothing about whether
work is actually flowing. This answers the second question: are cases piling up
unresolved, are red flags sitting unactioned, is anything stuck.

READ-ONLY BY CONSTRUCTION
Every database is opened with mode=ro via a file: URI. This script cannot write
to, lock, or migrate a database even if it is buggy. It runs while the dashboard
is live, so that guarantee matters.

DATE COLUMN NOTE
`created_at` is NULL on 29 of the 78 existing cases (rows imported before that
column was added). `timestamp` is populated on all of them. So every age
comparison here uses COALESCE(created_at, timestamp) - the same fallback
gdpr_purge.py uses at lines 221/286/304. Using created_at alone silently reports
zero, which looks like good news and is not.

Never raises. A database that is missing, locked or has the wrong shape is
reported as an error entry for that database; the rest still run.

Created: 2026-09-04
"""

import json
import os
import sqlite3
import sys

DBS = [
    ("Main dashboard", r"C:\JeffLocal\dashboard\data\dashboard.sqlite"),
    ("tenant1",        r"C:\JeffLocal\dashboard\data\tenants\tenant1.sqlite"),
    ("tenant2",        r"C:\JeffLocal\dashboard\data\tenants\tenant2.sqlite"),
]

# Anything not in this set counts as still open. Values seen in the live data are
# 'Resolved', 'resolved' and 'Escalated' - Escalated is deliberately still open.
RESOLVED = ("resolved",)

# verification_status values that mean "we could not confidently identify the
# patient". Taken from the live distribution, not invented.
IDENTITY_PROBLEM = ("failed", "no_match", "needs_review",
                    "insufficient_data", "unverified", "partial", "partial_match")

AGE = "COALESCE(created_at, timestamp)"
OPEN = "lower(COALESCE(status,'')) NOT IN ('resolved')"


def one(con, sql, params=()):
    return list(con.execute(sql, params))[0][0]


def check_db(label, path):
    out = {"label": label, "path": path, "ok": False, "error": None}

    if not os.path.exists(path):
        out["error"] = "database file not found"
        return out

    try:
        con = sqlite3.connect("file:%s?mode=ro" % path, uri=True)
    except Exception as exc:
        out["error"] = "cannot open: %s" % exc
        return out

    try:
        cols = [r[1] for r in con.execute("PRAGMA table_info(cases)")]
        if not cols:
            out["error"] = "no 'cases' table"
            return out
        out["missing_columns"] = [c for c in ("created_at", "timestamp", "status")
                                  if c not in cols]

        out["cases_total"] = one(con, "SELECT COUNT(*) FROM cases")
        out["cases_new_24h"] = one(
            con, "SELECT COUNT(*) FROM cases WHERE datetime(%s) > datetime('now','-24 hours')" % AGE)
        out["open_total"] = one(
            con, "SELECT COUNT(*) FROM cases WHERE %s" % OPEN)
        out["open_over_24h"] = one(
            con, "SELECT COUNT(*) FROM cases WHERE %s AND datetime(%s) < datetime('now','-24 hours')"
                 % (OPEN, AGE))
        out["open_red_flags"] = one(
            con, "SELECT COUNT(*) FROM cases WHERE %s AND COALESCE(red_flags_present,0)=1" % OPEN)

        marks = ",".join("?" * len(IDENTITY_PROBLEM))
        out["open_identity_issues"] = one(
            con,
            "SELECT COUNT(*) FROM cases WHERE %s AND lower(COALESCE(verification_status,'')) IN (%s)"
            % (OPEN, marks),
            IDENTITY_PROBLEM)

        # Emergency-priority cases still open. The single loudest number here.
        out["open_emergency"] = one(
            con,
            "SELECT COUNT(*) FROM cases WHERE %s AND lower(COALESCE(priority,'')) LIKE '%%999%%'" % OPEN)

        out["ok"] = True
    except Exception as exc:
        out["error"] = str(exc)
    finally:
        try:
            con.close()
        except Exception:
            pass

    return out


def main():
    results = [check_db(label, path) for label, path in DBS]
    json.dump({"databases": results}, sys.stdout)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # never let the morning brief lose its health block
        json.dump({"databases": [], "fatal": str(exc)}, sys.stdout)
        sys.exit(0)

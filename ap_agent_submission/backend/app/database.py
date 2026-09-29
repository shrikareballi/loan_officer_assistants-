"""Small SQLite repository used by the hackathon demo."""

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Iterator


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def db_path() -> Path:
    configured = os.getenv("AP_DATABASE_PATH", "backend/data/ap_agent.db")
    path = Path(configured)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    connection = sqlite3.connect(db_path(), timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize_database() -> None:
    with connect() as connection:
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vendor TEXT NOT NULL,
                invoice_number TEXT NOT NULL,
                purchase_order TEXT NOT NULL,
                invoice_date TEXT NOT NULL,
                due_date TEXT NOT NULL,
                invoice_amount REAL NOT NULL CHECK(invoice_amount > 0),
                purchase_order_amount REAL NOT NULL CHECK(purchase_order_amount > 0),
                payment_terms TEXT NOT NULL,
                variance_amount REAL NOT NULL,
                variance_pct REAL NOT NULL,
                risk_score INTEGER NOT NULL,
                risk_level TEXT NOT NULL,
                recommendation TEXT NOT NULL,
                factors_json TEXT NOT NULL,
                memory_json TEXT NOT NULL,
                decision TEXT,
                resolution TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                resolved_at TEXT
            )
            """
        )
        connection.execute(
            """CREATE UNIQUE INDEX IF NOT EXISTS ux_invoice_vendor_number
               ON invoices(lower(vendor), lower(invoice_number))"""
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS ix_invoices_vendor ON invoices(lower(vendor))"
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS ix_invoices_created ON invoices(created_at DESC)"
        )


def _as_invoice(row: sqlite3.Row) -> dict[str, Any]:
    value = dict(row)
    value["factors"] = json.loads(value.pop("factors_json"))
    value["memory"] = json.loads(value.pop("memory_json"))
    return value


def invoice_exists(vendor: str, invoice_number: str) -> bool:
    with connect() as connection:
        return connection.execute(
            """SELECT 1 FROM invoices
               WHERE lower(vendor) = lower(?) AND lower(invoice_number) = lower(?)""",
            (vendor, invoice_number),
        ).fetchone() is not None


def insert_invoice(invoice: dict, assessment: dict) -> dict[str, Any]:
    with connect() as connection:
        cursor = connection.execute(
            """INSERT INTO invoices (
                vendor, invoice_number, purchase_order, invoice_date, due_date,
                invoice_amount, purchase_order_amount, payment_terms,
                variance_amount, variance_pct, risk_score, risk_level,
                recommendation, factors_json, memory_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                invoice["vendor"], invoice["invoice_number"], invoice["purchase_order"],
                invoice["invoice_date"], invoice["due_date"], invoice["invoice_amount"],
                invoice["purchase_order_amount"], invoice["payment_terms"],
                assessment["variance_amount"], assessment["variance_pct"],
                assessment["risk_score"], assessment["risk_level"],
                assessment["recommendation"], json.dumps(assessment["factors"]),
                json.dumps(assessment["memory"]),
            ),
        )
        invoice_id = cursor.lastrowid
    return get_invoice(invoice_id)


def save_resolution(invoice_id: int, decision: str, resolution: str) -> dict[str, Any] | None:
    with connect() as connection:
        cursor = connection.execute(
            """UPDATE invoices SET decision = ?, resolution = ?,
                      resolved_at = CURRENT_TIMESTAMP
               WHERE id = ? AND decision IS NULL""",
            (decision, resolution.strip(), invoice_id),
        )
        if cursor.rowcount == 0:
            return None
    return get_invoice(invoice_id)


def get_invoice(invoice_id: int) -> dict[str, Any] | None:
    with connect() as connection:
        row = connection.execute(
            "SELECT * FROM invoices WHERE id = ?", (invoice_id,)
        ).fetchone()
    return _as_invoice(row) if row else None


def list_invoices(limit: int = 100) -> list[dict[str, Any]]:
    with connect() as connection:
        rows = connection.execute(
            "SELECT * FROM invoices ORDER BY created_at DESC, id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [_as_invoice(row) for row in rows]


def vendor_history(vendor: str) -> dict[str, Any]:
    with connect() as connection:
        rows = connection.execute(
            """SELECT invoice_number, purchase_order, invoice_amount,
                      purchase_order_amount, variance_pct, payment_terms,
                      risk_level, decision, resolution, created_at
               FROM invoices
               WHERE lower(vendor) = lower(?) AND decision IS NOT NULL
               ORDER BY created_at DESC LIMIT 30""",
            (vendor,),
        ).fetchall()
    cases = [dict(row) for row in rows]
    tolerance_pct = float(os.getenv("AP_AMOUNT_TOLERANCE_PCT", "2.0"))
    exceptions = [case for case in cases if abs(case["variance_pct"]) > tolerance_pct]
    terms: dict[str, int] = {}
    for case in cases:
        term = case["payment_terms"].strip()
        terms[term] = terms.get(term, 0) + 1
    common_terms = max(terms, key=terms.get) if terms else None
    return {
        "vendor": vendor,
        "resolved_cases": len(cases),
        "prior_variance_cases": len(exceptions),
        "usual_payment_terms": common_terms,
        "cases": cases[:8],
    }


def vendor_profiles() -> list[dict[str, Any]]:
    with connect() as connection:
        vendors = connection.execute(
            "SELECT DISTINCT vendor FROM invoices ORDER BY lower(vendor)"
        ).fetchall()
    profiles = []
    for row in vendors:
        profile = vendor_history(row["vendor"])
        profile["case_count"] = profile["resolved_cases"]
        profiles.append(profile)
    return profiles


def dashboard_summary() -> dict[str, Any]:
    with connect() as connection:
        totals = connection.execute(
            """SELECT COUNT(*) AS invoice_count,
                      SUM(CASE WHEN decision IS NULL THEN 1 ELSE 0 END) AS open_count,
                      SUM(CASE WHEN risk_score >= 30 AND decision IS NULL THEN 1 ELSE 0 END) AS exception_count,
                      SUM(CASE WHEN decision IS NOT NULL THEN 1 ELSE 0 END) AS resolved_count,
                      SUM(CASE WHEN decision IS NULL THEN invoice_amount ELSE 0 END) AS total_open_amount
               FROM invoices"""
        ).fetchone()
        risk_rows = connection.execute(
            """SELECT risk_level, COUNT(*) AS count FROM invoices
               WHERE decision IS NULL GROUP BY risk_level"""
        ).fetchall()
    risk_distribution = {key: 0 for key in ("Low", "Review", "High", "Critical")}
    risk_distribution.update({row["risk_level"]: row["count"] for row in risk_rows})
    result = dict(totals)
    for key in ("invoice_count", "open_count", "exception_count", "resolved_count"):
        result[key] = result[key] or 0
    result["total_open_amount"] = round(result["total_open_amount"] or 0, 2)
    result["risk_distribution"] = risk_distribution
    return result


def seed_demo_invoices() -> list[dict[str, Any]]:
    """Insert transparent fictional cases once to make the first demo usable."""
    today = date.today()
    demo_rows = [
        {
            "vendor": "Northstar Office Supply",
            "invoice_number": "NS-1042",
            "purchase_order": "PO-3308",
            "invoice_date": (today - timedelta(days=70)).isoformat(),
            "due_date": (today - timedelta(days=40)).isoformat(),
            "invoice_amount": 5280.00,
            "purchase_order_amount": 5000.00,
            "payment_terms": "Net 30",
            "decision": "hold",
            "resolution": "The invoice exceeded the PO. Vendor issued a $280 credit note after the AP team requested a line-item explanation.",
        },
        {
            "vendor": "Northstar Office Supply",
            "invoice_number": "NS-1097",
            "purchase_order": "PO-3416",
            "invoice_date": (today - timedelta(days=35)).isoformat(),
            "due_date": (today - timedelta(days=5)).isoformat(),
            "invoice_amount": 4210.00,
            "purchase_order_amount": 4000.00,
            "payment_terms": "Net 30",
            "decision": "escalated",
            "resolution": "Manager held payment until the vendor supplied an amended PO for the extra freight charge.",
        },
        {
            "vendor": "Harbor Facilities Group",
            "invoice_number": "HF-2081",
            "purchase_order": "PO-8820",
            "invoice_date": (today - timedelta(days=25)).isoformat(),
            "due_date": (today + timedelta(days=5)).isoformat(),
            "invoice_amount": 1875.00,
            "purchase_order_amount": 1875.00,
            "payment_terms": "Net 30",
            "decision": "approved",
            "resolution": "Matched the PO and receiving record; approved under the standard Net 30 terms.",
        },
    ]
    inserted = []
    for invoice in demo_rows:
        if invoice_exists(invoice["vendor"], invoice["invoice_number"]):
            continue
        inserted.append(invoice)
    if not inserted:
        return []
    # Seed only an empty database. Do not mix sample data into a real invoice log.
    with connect() as connection:
        has_any = connection.execute("SELECT 1 FROM invoices LIMIT 1").fetchone()
        if has_any:
            return []
        for invoice in inserted:
            variance = invoice["invoice_amount"] - invoice["purchase_order_amount"]
            variance_pct = variance / invoice["purchase_order_amount"] * 100
            factors = []
            if abs(variance_pct) > float(os.getenv("AP_AMOUNT_TOLERANCE_PCT", "2.0")):
                factors.append({"code": "po_variance", "label": "PO variance", "detail": f"Historical invoice differed from PO by {variance_pct:.1f}%.", "points": 0, "source": "rule"})
            connection.execute(
                """INSERT INTO invoices (
                    vendor, invoice_number, purchase_order, invoice_date, due_date,
                    invoice_amount, purchase_order_amount, payment_terms,
                    variance_amount, variance_pct, risk_score, risk_level,
                    recommendation, factors_json, memory_json, decision, resolution,
                    created_at, resolved_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 'Low',
                          'Historical demo case', ?, '{}', ?, ?, ?, ?)""",
                (
                    invoice["vendor"], invoice["invoice_number"], invoice["purchase_order"],
                    invoice["invoice_date"], invoice["due_date"], invoice["invoice_amount"],
                    invoice["purchase_order_amount"], invoice["payment_terms"], variance,
                    variance_pct, json.dumps(factors), invoice["decision"], invoice["resolution"],
                    f"{invoice['invoice_date']} 12:00:00", f"{invoice['invoice_date']} 12:00:00",
                ),
            )
    return inserted

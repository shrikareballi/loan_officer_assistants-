"""FastAPI service for invoice review, vendor history, and Hindsight memory."""

from contextlib import asynccontextmanager
import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from backend.app import database
from backend.app.schemas import InvoiceInput, InvoiceReview, ResolutionInput
from backend.app.services.memory import remember_case, reflect_vendor_case
from backend.app.services.review import assess_invoice


ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")


@asynccontextmanager
async def lifespan(_: FastAPI):
    database.initialize_database()
    seeded = database.seed_demo_invoices()
    if seeded:
        # Preload only synthetic, human-confirmed example cases for the first demo.
        existing = database.list_invoices(limit=100)
        by_key = {(row["vendor"], row["invoice_number"]): row for row in existing}
        for sample in seeded:
            row = by_key.get((sample["vendor"], sample["invoice_number"]))
            if row:
                try:
                    await asyncio.to_thread(remember_case, row)
                except Exception:
                    # Keep the API usable if Hindsight isn't started during setup.
                    pass
    yield


app = FastAPI(
    title="Accounts Payable Agent",
    description="Explainable invoice exception review with vendor-specific Hindsight memory.",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "service": "accounts-payable-agent",
        "hindsight_url": os.getenv("HINDSIGHT_URL", "http://localhost:8888"),
        "hindsight_bank": os.getenv("HINDSIGHT_BANK_ID", "accounts-payable-demo"),
    }


@app.get("/api/dashboard")
def get_dashboard():
    invoices = database.list_invoices(limit=100)
    summary = database.dashboard_summary()
    month_totals: dict[str, float] = {}
    for item in invoices:
        month = item["created_at"][:7]
        month_totals[month] = month_totals.get(month, 0) + float(item["invoice_amount"])
    monthly = [
        {"month": month, "amount": round(amount, 2)}
        for month, amount in sorted(month_totals.items())[-6:]
    ]
    return {
        "summary": summary,
        "monthly_volume": monthly,
        "recent_invoices": invoices[:8],
        "vendors": database.vendor_profiles(),
    }


@app.get("/api/invoices", response_model=list[InvoiceReview])
def get_invoices(limit: int = Query(default=100, ge=1, le=500)):
    return database.list_invoices(limit)


@app.get("/api/invoices/{invoice_id}", response_model=InvoiceReview)
def get_invoice(invoice_id: int):
    invoice = database.get_invoice(invoice_id)
    if invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found.")
    return invoice


@app.post("/api/invoices/review", status_code=201, response_model=InvoiceReview)
def review_new_invoice(payload: InvoiceInput):
    invoice = payload.model_dump(mode="json")
    if database.invoice_exists(invoice["vendor"], invoice["invoice_number"]):
        raise HTTPException(
            status_code=409,
            detail="This vendor and invoice number are already in the log. Open the existing record instead.",
        )
    profile = database.vendor_history(invoice["vendor"])
    memory = reflect_vendor_case(invoice["vendor"], invoice)
    assessment = assess_invoice(invoice, profile, memory)
    try:
        return database.insert_invoice(invoice, assessment)
    except Exception as error:
        # The unique database index closes the race between duplicate check and insert.
        if database.invoice_exists(invoice["vendor"], invoice["invoice_number"]):
            raise HTTPException(status_code=409, detail="This invoice was submitted already.") from error
        raise HTTPException(status_code=500, detail="Could not save the invoice review.") from error


@app.post("/api/invoices/{invoice_id}/resolve", response_model=InvoiceReview)
def resolve_invoice(invoice_id: int, payload: ResolutionInput):
    current = database.get_invoice(invoice_id)
    if current is None:
        raise HTTPException(status_code=404, detail="Invoice not found.")
    if current.get("decision"):
        raise HTTPException(status_code=409, detail="This invoice already has a recorded decision.")

    resolved = database.save_resolution(invoice_id, payload.decision, payload.resolution)
    if resolved is None:
        raise HTTPException(status_code=409, detail="This invoice was resolved by another request.")
    try:
        remember_case(resolved)
        resolved["memory_save"] = {"stored": True, "message": "Human-confirmed case retained in Hindsight."}
    except Exception as error:
        resolved["memory_save"] = {
            "stored": False,
            "message": f"Decision saved locally; Hindsight was unavailable: {str(error)[:250]}",
        }
    return resolved


@app.get("/api/vendors")
def get_vendors():
    return database.vendor_profiles()


@app.get("/api/vendors/{vendor}/memory")
def get_vendor_memory(vendor: str):
    profile = database.vendor_history(vendor)
    if not profile["resolved_cases"]:
        return {"vendor": vendor, "profile": profile, "memory": {"available": False, "sources": [], "summary": "No resolved cases are stored for this vendor yet."}}
    last_case = profile["cases"][0]
    current = {
        "invoice_number": "vendor profile review",
        "variance_pct": last_case["variance_pct"],
    }
    memory = reflect_vendor_case(vendor, current)
    return {"vendor": vendor, "profile": profile, "memory": memory}



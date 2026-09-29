"""Scoped Hindsight integration for vendor-specific case learning."""

import os
import re
from typing import Any

from hindsight_client import Hindsight


AP_TAG = "accounts-payable"
RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "pattern": {
            "type": "string",
            "enum": ["repeated_discrepancy", "stable_history", "insufficient_history"],
        },
        "summary": {"type": "string"},
        "suggested_review_step": {"type": "string"},
        "confidence": {"type": "string", "enum": ["low", "medium", "high"]},
    },
    "required": ["pattern", "summary", "suggested_review_step", "confidence"],
}


def bank_id() -> str:
    return os.getenv("HINDSIGHT_BANK_ID", "accounts-payable-demo")


def vendor_tag(vendor: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", vendor.casefold()).strip("-")
    return f"vendor:{normalized[:80]}"


def _client() -> Hindsight:
    options: dict[str, Any] = {
        "base_url": os.getenv("HINDSIGHT_URL", "http://localhost:8888"),
        "timeout": 20,
        "max_attempts": 1,
    }
    api_key = os.getenv("HINDSIGHT_API_KEY")
    if api_key:
        options["api_key"] = api_key
    return Hindsight(**options)


def remember_case(invoice: dict) -> None:
    """Retain one human-confirmed case, tagged for strict vendor isolation."""
    content = (
        "Confirmed accounts payable case. "
        f"Vendor: {invoice['vendor']}. Invoice: {invoice['invoice_number']}. "
        f"Purchase order: {invoice['purchase_order']}. "
        f"Invoice amount: {invoice['invoice_amount']:.2f}. "
        f"Purchase order amount: {invoice['purchase_order_amount']:.2f}. "
        f"Variance: {invoice['variance_pct']:.2f} percent. "
        f"Payment terms: {invoice['payment_terms']}. "
        f"Human decision: {invoice['decision']}. "
        f"Confirmed resolution: {invoice['resolution']}"
    )
    _client().retain(
        bank_id=bank_id(),
        content=content,
        context="A human-confirmed vendor invoice review and its resolution",
        document_id=f"ap-invoice-{invoice['id']}",
        tags=[AP_TAG, vendor_tag(invoice["vendor"])],
        update_mode="replace",
    )


def reflect_vendor_case(vendor: str, invoice: dict) -> dict:
    """Ask Hindsight to synthesize only this vendor's tagged past cases."""
    try:
        client = _client()
        response = client.reflect(
            bank_id=bank_id(),
            query=(
                f"For vendor {vendor}, review the retained, human-confirmed accounts payable cases. "
                "Use only evidence from those cases. Identify whether a recurring invoice discrepancy "
                "pattern is present, summarize the evidence, and suggest a cautious review step for "
                f"this new invoice #{invoice['invoice_number']} with variance {invoice['variance_pct']:.2f}%. "
                "Do not authorize payment. If no matching evidence is available, say the history is insufficient."
            ),
            budget="low",
            max_tokens=500,
            response_schema=RESPONSE_SCHEMA,
            tags=[AP_TAG, vendor_tag(vendor)],
            tags_match="all_strict",
            include_facts=True,
        )
        based_on = getattr(response, "based_on", None)
        memories = getattr(based_on, "memories", None) if based_on else None
        sources = [item.text for item in (memories or []) if getattr(item, "text", None)]
        structured = getattr(response, "structured_output", None)
        if not sources:
            return {
                "available": True,
                "summary": "Hindsight found no source facts for this vendor yet.",
                "sources": [],
                "structured": None,
                "error": None,
            }
        return {
            "available": True,
            "summary": getattr(response, "text", None),
            "sources": sources,
            "structured": structured if isinstance(structured, dict) else None,
            "error": None,
        }
    except Exception as error:
        # Rule checks remain usable, and the API explicitly reports missing memory.
        return {
            "available": False,
            "summary": None,
            "sources": [],
            "structured": None,
            "error": str(error)[:300],
        }

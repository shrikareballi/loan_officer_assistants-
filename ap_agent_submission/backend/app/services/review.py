"""Transparent invoice risk rules, enriched by verified case history."""

import os
from datetime import date


def assess_invoice(
    invoice: dict,
    profile: dict,
    memory: dict,
    duplicate: bool = False,
) -> dict:
    po_amount = float(invoice["purchase_order_amount"])
    invoice_amount = float(invoice["invoice_amount"])
    variance = invoice_amount - po_amount
    variance_pct = variance / po_amount * 100
    tolerance_pct = float(os.getenv("AP_AMOUNT_TOLERANCE_PCT", "2.0"))

    points = 0
    factors: list[dict] = []

    def add(code: str, label: str, detail: str, score: int, source: str = "rule") -> None:
        nonlocal points
        points += score
        factors.append({
            "code": code,
            "label": label,
            "detail": detail,
            "points": score,
            "source": source,
        })

    if duplicate:
        add("duplicate", "Possible duplicate", "A record with this vendor and invoice number already exists.", 70)

    if abs(variance_pct) > tolerance_pct:
        direction = "above" if variance > 0 else "below"
        severity_points = 40 if abs(variance_pct) >= 10 else 30
        add(
            "po_variance",
            "Purchase order variance",
            f"Invoice is {abs(variance_pct):.1f}% {direction} the purchase order; the configured tolerance is {tolerance_pct:.1f}%.",
            severity_points,
        )

    usual_terms = profile.get("usual_payment_terms")
    if usual_terms and invoice["payment_terms"].casefold() != usual_terms.casefold():
        add(
            "terms_change",
            "Payment terms differ from vendor history",
            f"This invoice says {invoice['payment_terms']}; the vendor's most common confirmed terms are {usual_terms}.",
            15,
            "vendor_history",
        )

    prior_variances = int(profile.get("prior_variance_cases", 0))
    if prior_variances >= 2 and abs(variance_pct) > tolerance_pct:
        add(
            "repeated_vendor_variance",
            "Recurring vendor discrepancy",
            f"The local audit log contains {prior_variances} resolved PO-variance cases for this vendor.",
            15,
            "vendor_history",
        )

    pattern = (memory.get("structured") or {}).get("pattern")
    if pattern == "repeated_discrepancy" and abs(variance_pct) > tolerance_pct:
        add(
            "hindsight_pattern",
            "Hindsight recalled a repeated exception pattern",
            "Hindsight found vendor-specific, human-confirmed cases describing recurring invoice discrepancies.",
            10,
            "hindsight",
        )

    if date.fromisoformat(invoice["due_date"]) < date.today():
        add("past_due", "Past due date", "The invoice due date has already passed.", 10)

    score = min(points, 100)
    if score >= 70:
        level = "Critical"
        recommendation = "Escalate to an AP manager before any payment decision."
    elif score >= 45:
        level = "High"
        recommendation = "Hold for supporting documents or a second approver before payment."
    elif score >= 25:
        level = "Review"
        recommendation = "Check the flagged details against the purchase order and receiving record."
    else:
        level = "Low"
        recommendation = "No configured exception was detected; complete the normal approval process."

    # Memory output is advisory and only counts when Hindsight cites source facts.
    memory_guidance = (memory.get("structured") or {}).get("suggested_review_step")
    if memory_guidance and memory.get("sources"):
        recommendation += f" Hindsight context: {memory_guidance}"

    return {
        "variance_amount": round(variance, 2),
        "variance_pct": round(variance_pct, 2),
        "risk_score": score,
        "risk_level": level,
        "recommendation": recommendation,
        "factors": factors,
        "memory": memory,
        "vendor_profile": {
            key: profile.get(key)
            for key in ("resolved_cases", "prior_variance_cases", "usual_payment_terms")
        },
    }

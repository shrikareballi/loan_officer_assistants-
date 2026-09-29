from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class InvoiceInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    vendor: str = Field(min_length=2, max_length=120)
    invoice_number: str = Field(min_length=1, max_length=80)
    purchase_order: str = Field(min_length=1, max_length=80)
    invoice_date: date
    due_date: date
    invoice_amount: float = Field(gt=0, le=100_000_000)
    purchase_order_amount: float = Field(gt=0, le=100_000_000)
    payment_terms: str = Field(min_length=2, max_length=80)

    @field_validator("vendor", "invoice_number", "purchase_order", "payment_terms")
    @classmethod
    def reject_blank_strings(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("This field cannot be blank.")
        return value.strip()


class ResolutionInput(BaseModel):
    decision: Literal["approved", "hold", "escalated"]
    resolution: str = Field(min_length=8, max_length=1200)


class ReviewFactor(BaseModel):
    code: str
    label: str
    detail: str
    points: int = 0
    source: Literal["rule", "vendor_history", "hindsight"] = "rule"


class MemoryEvidence(BaseModel):
    summary: str | None = None
    sources: list[str] = Field(default_factory=list)
    available: bool = False
    error: str | None = None
    structured: dict | None = None


class InvoiceReview(BaseModel):
    id: int
    vendor: str
    invoice_number: str
    purchase_order: str
    invoice_date: date
    due_date: date
    invoice_amount: float
    purchase_order_amount: float
    payment_terms: str
    variance_amount: float
    variance_pct: float
    risk_score: int
    risk_level: Literal["Low", "Review", "High", "Critical"]
    recommendation: str
    factors: list[ReviewFactor]
    memory: MemoryEvidence
    vendor_profile: dict
    decision: str | None = None
    resolution: str | None = None
    resolved_at: str | None = None
    created_at: str
    memory_save: dict | None = None


class DashboardSummary(BaseModel):
    invoice_count: int
    open_count: int
    exception_count: int
    resolved_count: int
    total_open_amount: float
    risk_distribution: dict[str, int]

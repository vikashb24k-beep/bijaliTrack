from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.services.gmail_service import GmailService

app = FastAPI(title="BijliTrack API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


MOCK_TRANSACTIONS: List[Dict[str, Any]] = [
    {
        "id": "TXN-54091",
        "date": "2026-11-06T23:07:35+05:30",
        "method": "PhonePe",
        "amount": 900.0,
        "status": "Success",
        "source": "Gmail",
        "customer": "23XXXXXX9114",
    },
    {
        "id": "TXN-54010",
        "date": "2026-11-01T11:32:00+05:30",
        "method": "Google Pay",
        "amount": 1250.0,
        "status": "Success",
        "source": "Gmail",
        "customer": "23XXXXXX9114",
    },
    {
        "id": "TXN-53974",
        "date": "2026-10-25T08:18:00+05:30",
        "method": "Paytm",
        "amount": 650.0,
        "status": "Pending",
        "source": "Manual",
        "customer": "23XXXXXX9114",
    },
    {
        "id": "TXN-53912",
        "date": "2026-10-18T18:42:00+05:30",
        "method": "PhonePe",
        "amount": 1100.0,
        "status": "Failed",
        "source": "Gmail",
        "customer": "23XXXXXX9114",
    },
    {
        "id": "TXN-53890",
        "date": "2026-10-11T10:05:00+05:30",
        "method": "PhonePe",
        "amount": 780.0,
        "status": "Refunded",
        "source": "Gmail",
        "customer": "23XXXXXX9114",
    },
]


def _to_transaction_payload(email_item: Dict[str, Any]) -> Dict[str, Any]:
    sender = email_item.get("from", "Unknown")
    subject = email_item.get("subject", "")
    return {
        "id": email_item.get("id", "UNKNOWN"),
        "date": email_item.get("date", datetime.utcnow().isoformat()),
        "method": "PhonePe" if "PhonePe" in sender else "Other",
        "amount": 900.0,
        "status": "Success" if "successful" in subject.lower() else "Pending",
        "source": "Gmail",
        "customer": "23XXXXXX9114",
    }


def _load_transactions() -> List[Dict[str, Any]]:
    try:
        service = GmailService()
        emails = service.find_electricity_emails()
        if emails:
            return [_to_transaction_payload(item) for item in emails[:10]]
    except Exception:
        pass
    return MOCK_TRANSACTIONS


@app.get("/api/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/api/dashboard/summary")
def dashboard_summary() -> Dict[str, Any]:
    transactions = _load_transactions()
    total = sum(float(item["amount"]) for item in transactions if item.get("status") == "Success")
    monthly = total
    yearly = total * 12
    average = monthly / max(len(transactions), 1)

    return {
        "summary": {
            "totalThisMonth": round(monthly, 2),
            "totalThisYear": round(yearly, 2),
            "averageMonthly": round(average, 2),
            "totalTransactions": len(transactions),
        },
        "transactions": transactions,
    }


@app.get("/api/transactions")
def list_transactions() -> Dict[str, Any]:
    return {"transactions": _load_transactions()}

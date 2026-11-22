from __future__ import annotations

import csv
import io
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse, Response

from app.services.automation_service import (
    DEMO_EMAIL_ACTIVITIES,
    DEMO_SBPDCL_TRANSACTIONS,
    calculate_monthly_spending,
    compute_dashboard_metrics,
    parse_raw_text_receipt,
)
from app.services.database_service import DatabaseService
from app.services.gmail_service import GmailService
from app.services.scheduler_service import sync_manager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("bijlitrack.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: trigger scheduler
    logger.info("Initializing BijliTrack API service...")
    await sync_manager.start()
    yield
    # Shutdown
    logger.info("Stopping BijliTrack API service...")
    await sync_manager.stop()


app = FastAPI(
    title="BijliTrack SBPDCL API",
    version="2.0.0",
    description="Automatic SBPDCL Electricity Bill Payment Tracker powered by Gmail API & PhonePe",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _get_active_transactions() -> Tuple[List[Dict[str, Any]], bool]:
    """Retrieve verified transactions from DB or fallback to clean SBPDCL demo data."""
    db = DatabaseService()
    real_txns = db.fetch_recent_transactions(only_sbpdcl=True, limit=1000)
    if real_txns:
        return real_txns, False
    return DEMO_SBPDCL_TRANSACTIONS, True


# -----------------------------------------------------------------------------
# Core Dashboard & Analytics
# -----------------------------------------------------------------------------

@app.get("/api/health")
def health() -> Dict[str, Any]:
    db = DatabaseService()
    gmail = GmailService()
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "supabase_connected": db.is_supabase_connected,
        "gmail_configured": gmail.get_auth_status()["connected"],
    }


@app.get("/api/dashboard/summary")
def get_dashboard_summary(
    range: str = Query("12m", pattern="^(6m|12m|year|custom|all)$"),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> Dict[str, Any]:
    """Retrieve the 4 primary summary cards and monthly payment chart."""
    transactions, is_demo = _get_active_transactions()
    db = DatabaseService()

    metrics = compute_dashboard_metrics(
        transactions,
        date_filter=range,
        start_date=start_date,
        end_date=end_date,
    )

    sync_status = sync_manager.get_status()

    return {
        "summary": metrics["summary"],
        "monthlySpending": metrics["monthlySpending"],
        "transactions": metrics["transactions"],
        "is_demo": is_demo,
        "supabase_connected": db.is_supabase_connected,
        "sync_status": sync_status,
    }


@app.get("/api/monthly-spending")
def get_monthly_spending(
    range: str = Query("12m", pattern="^(6m|12m|year|custom|all)$"),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> Dict[str, Any]:
    transactions, is_demo = _get_active_transactions()
    monthly = calculate_monthly_spending(
        transactions,
        date_filter=range,
        start_date=start_date,
        end_date=end_date,
    )
    return {
        "monthlySpending": monthly,
        "is_demo": is_demo,
    }


# -----------------------------------------------------------------------------
# Transactions Ledger & CSV Export
# -----------------------------------------------------------------------------

@app.get("/api/transactions")
def list_transactions(
    search: str = "",
    month: str = "",
    year: str = "",
    status: Optional[str] = None,
    limit: int = 1000,
) -> Dict[str, Any]:
    db = DatabaseService()
    real_txns = db.fetch_recent_transactions(
        search=search,
        month=month,
        year=year,
        status=status,
        only_sbpdcl=True,
        limit=limit,
    )

    if real_txns:
        return {"transactions": real_txns, "is_demo": False}

    # If DB is empty, apply filters to demo transactions
    filtered = DEMO_SBPDCL_TRANSACTIONS
    if status and status.lower() != "all":
        filtered = [t for t in filtered if str(t.get("status", "")).lower() == status.lower()]

    if search:
        s = search.lower()
        filtered = [
            t for t in filtered
            if s in t["id"].lower()
            or s in t.get("consumer_number", "").lower()
            or s in t.get("biller_name", "").lower()
            or s in t.get("upi_ref_no", "").lower()
            or s in str(t.get("amount", "")).lower()
            or s in t.get("subject", "").lower()
            or s in t.get("payment_method", "").lower()
        ]
    if month and year:
        prefix = f"{year}-{int(month):02d}"
        filtered = [t for t in filtered if str(t.get("date", "")).startswith(prefix)]
    elif year:
        filtered = [t for t in filtered if str(t.get("date", "")).startswith(year)]
    elif month:
        m_str = f"-{int(month):02d}-"
        filtered = [t for t in filtered if m_str in str(t.get("date", ""))]

    return {"transactions": filtered, "is_demo": True}


@app.get("/api/transactions/export")
def export_transactions_csv(
    search: str = "",
    month: str = "",
    year: str = "",
    status: Optional[str] = None,
) -> Response:
    """Export filtered verified transactions to CSV."""
    db = DatabaseService()
    real_txns = db.fetch_recent_transactions(
        search=search,
        month=month,
        year=year,
        status=status,
        only_sbpdcl=True,
        limit=5000,
    )
    data = real_txns if real_txns else DEMO_SBPDCL_TRANSACTIONS
    if not real_txns:
        if status and status.lower() != "all":
            data = [t for t in data if str(t.get("status", "")).lower() == status.lower()]
        if month and year:
            prefix = f"{year}-{int(month):02d}"
            data = [t for t in data if str(t.get("date", "")).startswith(prefix)]
        elif year:
            data = [t for t in data if str(t.get("date", "")).startswith(year)]
        elif month:
            m_str = f"-{int(month):02d}-"
            data = [t for t in data if m_str in str(t.get("date", ""))]
        if search:
            s = search.lower()
            data = [t for t in data if s in t["id"].lower() or s in t.get("consumer_number", "").lower() or s in str(t.get("amount", "")).lower()]

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Payment Date",
        "Amount (INR)",
        "Biller Name",
        "Transaction ID",
        "UPI Reference (UTR)",
        "Consumer Number",
        "Payment Method",
        "Status",
        "Email Subject",
    ])

    for row in data:
        writer.writerow([
            row.get("transaction_date") or row.get("date"),
            row.get("amount", 0.0),
            row.get("biller_name", "SBPDCL"),
            row.get("transaction_id") or row.get("id"),
            row.get("upi_ref_no", ""),
            row.get("consumer_number") or row.get("customer", ""),
            row.get("payment_method") or row.get("method", "PhonePe"),
            row.get("status", "Success"),
            row.get("subject", ""),
        ])

    csv_content = output.getvalue()
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=sbpdcl_transactions.csv"
        },
    )


@app.post("/api/transactions/parse-text")
def parse_and_save_receipt_text(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Parse raw PhonePe receipt text pasted by user and save to database."""
    raw_text = str(payload.get("text", "")).strip()
    if not raw_text:
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    date_hint = payload.get("date")
    parsed = parse_raw_text_receipt(raw_text, date_hint)

    db = DatabaseService()
    # Save into email activities
    db.upsert_email_activities([parsed])

    # If verified, save into transactions
    saved_txn = 0
    if parsed.get("is_sbpdcl") and parsed.get("verification_status") == "verified":
        saved_txn = db.upsert_transactions([parsed])

    return {
        "status": "ok",
        "parsed": parsed,
        "saved_to_ledger": bool(saved_txn),
    }


# -----------------------------------------------------------------------------
# Email Activity & Review Section
# -----------------------------------------------------------------------------

@app.get("/api/email-activity")
def list_email_activity(
    status: str = "all",
    search: str = "",
    limit: int = 200,
) -> Dict[str, Any]:
    """Retrieve scanned Gmail payment emails with extraction & verification states."""
    db = DatabaseService()
    real_acts = db.fetch_email_activities(status_filter=status, search=search, limit=limit)
    if real_acts:
        return {"activities": real_acts, "is_demo": False}

    # Demo activities fallback
    filtered = DEMO_EMAIL_ACTIVITIES
    if status != "all":
        filtered = [a for a in filtered if a.get("verification_status", "").lower() == status.lower()]
    if search:
        s = search.lower()
        filtered = [
            a for a in filtered
            if s in a.get("subject", "").lower()
            or s in a.get("sender", "").lower()
            or s in a.get("detected_biller", "").lower()
            or s in a.get("consumer_number", "").lower()
        ]

    return {"activities": filtered, "is_demo": True}


@app.post("/api/email-activity/{email_id}/verify")
def verify_email_activity(email_id: str) -> Dict[str, Any]:
    """Manually mark an uncertain email activity as a verified SBPDCL payment."""
    db = DatabaseService()
    success = db.update_email_status(email_id, verification_status="verified", rejection_reason="")
    if not success:
        raise HTTPException(status_code=404, detail="Email record not found or could not be updated")
    return {"status": "ok", "message": "Email verified as SBPDCL transaction"}


@app.post("/api/email-activity/{email_id}/reject")
def reject_email_activity(
    email_id: str,
    payload: Dict[str, str] = None,
) -> Dict[str, Any]:
    """Reject an email activity."""
    reason = (payload or {}).get("reason", "Manually rejected by user")
    db = DatabaseService()
    success = db.update_email_status(email_id, verification_status="rejected", rejection_reason=reason)
    if not success:
        raise HTTPException(status_code=404, detail="Email record not found")
    return {"status": "ok", "message": "Email marked as rejected"}


# -----------------------------------------------------------------------------
# Gmail Synchronization & Background Worker
# -----------------------------------------------------------------------------

@app.post("/api/sync/gmail")
async def trigger_gmail_sync() -> Dict[str, Any]:
    """Manually initiate on-demand synchronization with Gmail."""
    result = await sync_manager.run_sync_job()
    return result


@app.get("/api/sync/status")
def get_sync_status() -> Dict[str, Any]:
    """Get real-time background synchronization status."""
    return sync_manager.get_status()


# -----------------------------------------------------------------------------
# Settings & Configuration
# -----------------------------------------------------------------------------

@app.get("/api/settings")
def get_settings() -> Dict[str, Any]:
    db = DatabaseService()
    gmail = GmailService()
    settings = db.get_all_settings()
    auth_status = gmail.get_auth_status()

    return {
        "settings": settings,
        "gmail": auth_status,
        "database": {
            "supabase_connected": db.is_supabase_connected,
            "backend_storage": "Supabase (PostgreSQL) + Local SQLite" if db.is_supabase_connected else "Local SQLite (Offline fallback active)",
        },
    }


@app.post("/api/settings")
def update_settings(payload: Dict[str, Any]) -> Dict[str, Any]:
    db = DatabaseService()
    for key, val in payload.items():
        db.set_setting(str(key), str(val))
    return {"status": "ok", "settings": db.get_all_settings()}


# -----------------------------------------------------------------------------
# Google OAuth Helpers
# -----------------------------------------------------------------------------

@app.get("/api/auth/gmail/url")
def get_gmail_auth_url(redirect_uri: str = "http://localhost:8000/auth/gmail/callback") -> Dict[str, str]:
    gmail = GmailService()
    db = DatabaseService()
    try:
        url, state, code_verifier = gmail.generate_authorization_url(redirect_uri)
        if state and code_verifier:
            db.set_setting(f"oauth_verifier_{state}", code_verifier)
            db.set_setting("latest_oauth_verifier", code_verifier)
        return {"auth_url": url, "state": state}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/auth/gmail/callback")
def gmail_oauth_callback(
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
):
    if error:
        return HTMLResponse(
            f"<h3>Google Authentication Error</h3><p>{error}</p><a href='http://localhost:5173/'>Return to BijliTrack</a>"
        )

    if not code:
        return HTMLResponse(
            "<h3>Missing authorization code.</h3><a href='http://localhost:5173/'>Return to BijliTrack</a>"
        )

    gmail = GmailService()
    db = DatabaseService()
    try:
        redirect_uri = "http://localhost:8000/auth/gmail/callback"
        code_verifier = None
        if state:
            code_verifier = db.get_setting(f"oauth_verifier_{state}")
        if not code_verifier:
            code_verifier = db.get_setting("latest_oauth_verifier")

        gmail.exchange_code_for_token(
            code=code,
            redirect_uri=redirect_uri,
            code_verifier=code_verifier,
            state=state,
        )
        return RedirectResponse(url="http://localhost:5173/?auth=success")
    except Exception as exc:
        logger.error("OAuth token exchange failed: %s", exc)
        return HTMLResponse(
            f"<h3>Token Exchange Failed</h3><p>{exc}</p>"
            f"<p>Tip: You can also run <code>python auth_gmail.py</code> in the backend folder to connect instantly.</p>"
            f"<br><a href='http://localhost:5173/'>Return to BijliTrack</a>"
        )

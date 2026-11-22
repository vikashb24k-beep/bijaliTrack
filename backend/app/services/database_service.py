from __future__ import annotations

import json
import logging
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")

logger = logging.getLogger("bijlitrack.database")
SQLITE_PATH = BASE_DIR / "bijlitrack.db"


class DatabaseService:
    """Robust dual-backend database service for BijliTrack.

    Uses Supabase (PostgreSQL) when online and configured, with transparent
    local SQLite fallback to ensure zero data loss and uninterrupted operation.
    """

    _cached_client = None
    _cached_healthy: Optional[bool] = None
    _last_check_timestamp: float = 0.0

    def __init__(self, url: Optional[str] = None, key: Optional[str] = None) -> None:
        self.url = url or os.getenv("SUPABASE_URL", "")
        self.key = key or os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY", "")
        self._init_sqlite()
        self._check_supabase()

    def _init_sqlite(self) -> None:
        """Initialize local SQLite schema if not already present."""
        try:
            with sqlite3.connect(SQLITE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS recharge_transactions (
                        id TEXT PRIMARY KEY,
                        transaction_id TEXT UNIQUE,
                        upi_ref_no TEXT DEFAULT '',
                        transaction_date TEXT NOT NULL,
                        amount REAL NOT NULL DEFAULT 0,
                        refund_amount REAL DEFAULT 0,
                        payment_method TEXT DEFAULT 'PhonePe',
                        status TEXT DEFAULT 'Success',
                        biller_name TEXT DEFAULT 'South Bihar Power Distribution Company Limited (SBPDCL)',
                        consumer_number TEXT DEFAULT '',
                        is_sbpdcl INTEGER DEFAULT 1,
                        verification_status TEXT DEFAULT 'verified',
                        rejection_reason TEXT DEFAULT '',
                        source TEXT DEFAULT 'Gmail',
                        subject TEXT DEFAULT '',
                        email_id TEXT DEFAULT '',
                        snippet TEXT DEFAULT '',
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS email_activities (
                        id TEXT PRIMARY KEY,
                        email_id TEXT UNIQUE NOT NULL,
                        sender TEXT DEFAULT '',
                        subject TEXT DEFAULT '',
                        received_date TEXT,
                        extracted_amount REAL DEFAULT 0,
                        detected_biller TEXT DEFAULT 'Unknown',
                        consumer_number TEXT DEFAULT '',
                        transaction_id TEXT DEFAULT '',
                        upi_ref_no TEXT DEFAULT '',
                        verification_status TEXT DEFAULT 'review',
                        rejection_reason TEXT DEFAULT '',
                        snippet TEXT DEFAULT '',
                        raw_payload TEXT DEFAULT '',
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS app_settings (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                conn.commit()
        except Exception as exc:
            logger.error("Failed to initialize SQLite: %s", exc)

    def _check_supabase(self) -> None:
        """Attempt to initialize Supabase client and test basic connectivity with caching."""
        import time
        now = time.time()
        if DatabaseService._cached_healthy is not None and (now - DatabaseService._last_check_timestamp) < 300:
            self._client = DatabaseService._cached_client
            self._supabase_healthy = DatabaseService._cached_healthy
            return

        if not self.url or not self.key or "your-project" in self.url:
            self._client = None
            self._supabase_healthy = False
            DatabaseService._cached_client = None
            DatabaseService._cached_healthy = False
            DatabaseService._last_check_timestamp = now
            return

        try:
            from supabase import create_client
            client = create_client(self.url, self.key)
            client.table("recharge_transactions").select("id").limit(1).execute()
            self._client = client
            self._supabase_healthy = True
            DatabaseService._cached_client = client
            DatabaseService._cached_healthy = True
        except Exception:
            self._client = None
            self._supabase_healthy = False
            DatabaseService._cached_client = None
            DatabaseService._cached_healthy = False

        DatabaseService._last_check_timestamp = now

    @property
    def is_supabase_connected(self) -> bool:
        return self._supabase_healthy

    # -------------------------------------------------------------------------
    # Transaction Management
    # -------------------------------------------------------------------------

    def upsert_transactions(self, transactions: List[Dict[str, Any]]) -> int:
        if not transactions:
            return 0

        # Always persist to local SQLite
        saved_count = 0
        try:
            with sqlite3.connect(SQLITE_PATH) as conn:
                cursor = conn.cursor()
                for item in transactions:
                    item_id = str(item.get("id") or item.get("transaction_id") or item.get("email_id") or "")
                    txn_id = str(item.get("transaction_id") or item_id)
                    upi_ref = str(item.get("upi_ref_no") or "")
                    date_val = str(item.get("transaction_date") or item.get("date") or datetime.utcnow().isoformat())
                    amount = float(item.get("amount") or 0)
                    refund = float(item.get("refund_amount") or 0)
                    method = str(item.get("payment_method") or item.get("method") or "PhonePe")
                    status = str(item.get("status") or "Success")
                    biller = str(item.get("biller_name") or "South Bihar Power Distribution Company Limited (SBPDCL)")
                    consumer = str(item.get("consumer_number") or item.get("customer") or "")
                    is_sbpdcl = 1 if item.get("is_sbpdcl", True) else 0
                    ver_status = str(item.get("verification_status") or "verified")
                    rej_reason = str(item.get("rejection_reason") or "")
                    source = str(item.get("source") or "Gmail")
                    subject = str(item.get("subject") or "")
                    email_id = str(item.get("email_id") or "")
                    snippet = str(item.get("snippet") or "")

                    cursor.execute("""
                        INSERT INTO recharge_transactions (
                            id, transaction_id, upi_ref_no, transaction_date, amount, refund_amount,
                            payment_method, status, biller_name, consumer_number, is_sbpdcl,
                            verification_status, rejection_reason, source, subject, email_id, snippet, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                        ON CONFLICT(id) DO UPDATE SET
                            transaction_id=excluded.transaction_id,
                            upi_ref_no=excluded.upi_ref_no,
                            transaction_date=excluded.transaction_date,
                            amount=excluded.amount,
                            refund_amount=excluded.refund_amount,
                            payment_method=excluded.payment_method,
                            status=excluded.status,
                            biller_name=excluded.biller_name,
                            consumer_number=excluded.consumer_number,
                            is_sbpdcl=excluded.is_sbpdcl,
                            verification_status=excluded.verification_status,
                            rejection_reason=excluded.rejection_reason,
                            subject=excluded.subject,
                            email_id=excluded.email_id,
                            snippet=excluded.snippet,
                            updated_at=CURRENT_TIMESTAMP
                    """, (
                        item_id, txn_id, upi_ref, date_val, amount, refund,
                        method, status, biller, consumer, is_sbpdcl,
                        ver_status, rej_reason, source, subject, email_id, snippet
                    ))
                    saved_count += 1
                conn.commit()
        except Exception as exc:
            logger.error("SQLite upsert_transactions failed: %s", exc)

        # Sync to Supabase if connected
        if self._supabase_healthy and self._client:
            try:
                payload = []
                for item in transactions:
                    item_id = str(item.get("id") or item.get("transaction_id") or item.get("email_id") or "")
                    payload.append({
                        "id": item_id,
                        "transaction_id": str(item.get("transaction_id") or item_id),
                        "upi_ref_no": str(item.get("upi_ref_no") or ""),
                        "transaction_date": str(item.get("transaction_date") or item.get("date") or datetime.utcnow().isoformat()),
                        "amount": float(item.get("amount") or 0),
                        "refund_amount": float(item.get("refund_amount") or 0),
                        "payment_method": str(item.get("payment_method") or item.get("method") or "PhonePe"),
                        "status": str(item.get("status") or "Success"),
                        "biller_name": str(item.get("biller_name") or "South Bihar Power Distribution Company Limited (SBPDCL)"),
                        "consumer_number": str(item.get("consumer_number") or item.get("customer") or ""),
                        "is_sbpdcl": bool(item.get("is_sbpdcl", True)),
                        "verification_status": str(item.get("verification_status") or "verified"),
                        "rejection_reason": str(item.get("rejection_reason") or ""),
                        "source": str(item.get("source") or "Gmail"),
                        "subject": str(item.get("subject") or ""),
                        "email_id": str(item.get("email_id") or ""),
                        "snippet": str(item.get("snippet") or ""),
                    })
                self._client.table("recharge_transactions").upsert(payload, on_conflict="id").execute()
            except Exception as exc:
                logger.warning("Supabase upsert failed, retained in SQLite: %s", exc)

        return saved_count

    def fetch_recent_transactions(
        self,
        search: str = "",
        month: str = "",
        year: str = "",
        status: Optional[str] = None,
        only_sbpdcl: bool = True,
        limit: int = 1000,
    ) -> List[Dict[str, Any]]:
        """Fetch transactions from local store with optional filters."""
        query = "SELECT * FROM recharge_transactions WHERE 1=1"
        params: List[Any] = []

        if only_sbpdcl:
            query += " AND is_sbpdcl = 1 AND verification_status = 'verified'"

        if status and status.lower() != "all":
            query += " AND LOWER(status) = LOWER(?)"
            params.append(status)

        if month and year:
            month_prefix = f"{year}-{int(month):02d}"
            query += " AND transaction_date LIKE ?"
            params.append(f"{month_prefix}%")
        elif year:
            query += " AND transaction_date LIKE ?"
            params.append(f"{year}%")
        elif month:
            m_str = f"{int(month):02d}"
            query += " AND (strftime('%m', transaction_date) = ? OR transaction_date LIKE ?)"
            params.extend([m_str, f"%-{m_str}-%"])

        if search:
            search_param = f"%{search}%"
            query += " AND (id LIKE ? OR transaction_id LIKE ? OR consumer_number LIKE ? OR biller_name LIKE ? OR upi_ref_no LIKE ? OR CAST(amount AS TEXT) LIKE ? OR subject LIKE ? OR payment_method LIKE ?)"
            params.extend([search_param, search_param, search_param, search_param, search_param, search_param, search_param, search_param])

        query += " ORDER BY transaction_date DESC LIMIT ?"
        params.append(limit)

        try:
            with sqlite3.connect(SQLITE_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(query, params)
                rows = cursor.fetchall()
                results = []
                for row in rows:
                    results.append({
                        "id": row["id"],
                        "transaction_id": row["transaction_id"],
                        "upi_ref_no": row["upi_ref_no"],
                        "transaction_date": row["transaction_date"],
                        "date": row["transaction_date"],
                        "amount": float(row["amount"]),
                        "refund_amount": float(row["refund_amount"]),
                        "payment_method": row["payment_method"],
                        "method": row["payment_method"],
                        "status": row["status"],
                        "biller_name": row["biller_name"],
                        "consumer_number": row["consumer_number"],
                        "customer": row["consumer_number"],
                        "is_sbpdcl": bool(row["is_sbpdcl"]),
                        "verification_status": row["verification_status"],
                        "rejection_reason": row["rejection_reason"],
                        "source": row["source"],
                        "subject": row["subject"],
                        "email_id": row["email_id"],
                        "snippet": row["snippet"],
                        "created_at": row["created_at"],
                    })
                return results
        except Exception as exc:
            logger.error("Failed to fetch transactions from SQLite: %s", exc)
            return []

    # -------------------------------------------------------------------------
    # Email Activities Management
    # -------------------------------------------------------------------------

    def upsert_email_activities(self, activities: List[Dict[str, Any]]) -> int:
        if not activities:
            return 0

        saved_count = 0
        try:
            with sqlite3.connect(SQLITE_PATH) as conn:
                cursor = conn.cursor()
                for item in activities:
                    email_id = str(item.get("email_id") or item.get("id") or "")
                    if not email_id:
                        continue
                    act_id = f"ACT-{email_id}"
                    sender = str(item.get("sender") or item.get("from") or "")
                    subject = str(item.get("subject") or "")
                    received_date = str(item.get("received_date") or item.get("date") or datetime.utcnow().isoformat())
                    amount = float(item.get("extracted_amount") or item.get("amount") or 0)
                    biller = str(item.get("detected_biller") or item.get("biller_name") or "Unknown")
                    consumer = str(item.get("consumer_number") or item.get("customer") or "")
                    txn_id = str(item.get("transaction_id") or "")
                    upi_ref = str(item.get("upi_ref_no") or "")
                    ver_status = str(item.get("verification_status") or "review")
                    rej_reason = str(item.get("rejection_reason") or "")
                    snippet = str(item.get("snippet") or "")
                    raw_payload = json.dumps(item) if not isinstance(item.get("raw_payload"), str) else item.get("raw_payload", "")

                    cursor.execute("""
                        INSERT INTO email_activities (
                            id, email_id, sender, subject, received_date, extracted_amount,
                            detected_biller, consumer_number, transaction_id, upi_ref_no,
                            verification_status, rejection_reason, snippet, raw_payload
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(email_id) DO UPDATE SET
                            sender=excluded.sender,
                            subject=excluded.subject,
                            received_date=excluded.received_date,
                            extracted_amount=excluded.extracted_amount,
                            detected_biller=excluded.detected_biller,
                            consumer_number=excluded.consumer_number,
                            transaction_id=excluded.transaction_id,
                            upi_ref_no=excluded.upi_ref_no,
                            verification_status=excluded.verification_status,
                            rejection_reason=excluded.rejection_reason,
                            snippet=excluded.snippet,
                            raw_payload=excluded.raw_payload
                    """, (
                        act_id, email_id, sender, subject, received_date, amount,
                        biller, consumer, txn_id, upi_ref, ver_status, rej_reason, snippet, raw_payload
                    ))
                    saved_count += 1
                conn.commit()
        except Exception as exc:
            logger.error("SQLite upsert_email_activities failed: %s", exc)

        return saved_count

    def fetch_email_activities(
        self,
        status_filter: str = "all",
        search: str = "",
        limit: int = 200,
    ) -> List[Dict[str, Any]]:
        query = "SELECT * FROM email_activities WHERE 1=1"
        params: List[Any] = []

        if status_filter and status_filter.lower() != "all":
            query += " AND LOWER(verification_status) = LOWER(?)"
            params.append(status_filter)

        if search:
            search_param = f"%{search}%"
            query += " AND (subject LIKE ? OR sender LIKE ? OR detected_biller LIKE ? OR consumer_number LIKE ? OR transaction_id LIKE ?)"
            params.extend([search_param, search_param, search_param, search_param, search_param])

        query += " ORDER BY received_date DESC LIMIT ?"
        params.append(limit)

        try:
            with sqlite3.connect(SQLITE_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(query, params)
                rows = cursor.fetchall()
                results = []
                for row in rows:
                    results.append({
                        "id": row["id"],
                        "email_id": row["email_id"],
                        "sender": row["sender"],
                        "subject": row["subject"],
                        "received_date": row["received_date"],
                        "date": row["received_date"],
                        "extracted_amount": float(row["extracted_amount"]),
                        "amount": float(row["extracted_amount"]),
                        "detected_biller": row["detected_biller"],
                        "consumer_number": row["consumer_number"],
                        "transaction_id": row["transaction_id"],
                        "upi_ref_no": row["upi_ref_no"],
                        "verification_status": row["verification_status"],
                        "rejection_reason": row["rejection_reason"],
                        "snippet": row["snippet"],
                        "created_at": row["created_at"],
                    })
                return results
        except Exception as exc:
            logger.error("Failed to fetch email activities: %s", exc)
            return []

    def update_email_status(
        self,
        email_id: str,
        verification_status: str,
        rejection_reason: str = "",
    ) -> bool:
        """Update verification status of an email activity and mirror to transactions if verified."""
        try:
            with sqlite3.connect(SQLITE_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE email_activities
                    SET verification_status = ?, rejection_reason = ?
                    WHERE email_id = ? OR id = ?
                """, (verification_status, rejection_reason, email_id, email_id))

                if verification_status == "verified":
                    # Fetch email details to promote to recharge_transactions
                    cursor.execute("SELECT * FROM email_activities WHERE email_id = ? OR id = ?", (email_id, email_id))
                    row = cursor.fetchone()
                    if row:
                        cursor.execute("""
                            INSERT INTO recharge_transactions (
                                id, transaction_id, upi_ref_no, transaction_date, amount,
                                payment_method, status, biller_name, consumer_number, is_sbpdcl,
                                verification_status, source, subject, email_id, snippet
                            ) VALUES (?, ?, ?, ?, ?, 'PhonePe', 'Success', 'South Bihar Power Distribution Company Limited (SBPDCL)', ?, 1, 'verified', 'Gmail', ?, ?, ?)
                            ON CONFLICT(id) DO UPDATE SET
                                verification_status = 'verified',
                                is_sbpdcl = 1,
                                status = 'Success'
                        """, (
                            row["email_id"],
                            row["transaction_id"] or f"TXN-{row['email_id']}",
                            row["upi_ref_no"],
                            row["received_date"],
                            row["extracted_amount"],
                            row["consumer_number"],
                            row["subject"],
                            row["email_id"],
                            row["snippet"],
                        ))
                elif verification_status == "rejected":
                    # Mark transaction as rejected or delete from main ledger
                    cursor.execute("""
                        UPDATE recharge_transactions
                        SET verification_status = 'rejected', is_sbpdcl = 0
                        WHERE email_id = ? OR id = ?
                    """, (email_id, email_id))

                conn.commit()
                return True
        except Exception as exc:
            logger.error("Failed to update email status: %s", exc)
            return False

    # -------------------------------------------------------------------------
    # App Settings (Key-Value)
    # -------------------------------------------------------------------------

    def get_setting(self, key: str, default: str = "") -> str:
        try:
            with sqlite3.connect(SQLITE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT value FROM app_settings WHERE key = ?", (key,))
                row = cursor.fetchone()
                return str(row[0]) if row else default
        except Exception:
            return default

    def set_setting(self, key: str, value: str) -> bool:
        try:
            with sqlite3.connect(SQLITE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO app_settings (key, value, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(key) DO UPDATE SET
                        value = excluded.value,
                        updated_at = CURRENT_TIMESTAMP
                """, (key, value))
                conn.commit()
                return True
        except Exception as exc:
            logger.error("Failed to set setting %s: %s", key, exc)
            return False

    def get_all_settings(self) -> Dict[str, str]:
        defaults = {
            "consumer_number": "23XXXXXX9114",
            "sync_interval_minutes": "30",
            "auto_sync_enabled": "true",
            "last_sync_time": "",
            "last_sync_status": "Never synced",
            "biller_filter": "South Bihar Power Distribution Company Limited (SBPDCL)",
        }
        try:
            with sqlite3.connect(SQLITE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT key, value FROM app_settings")
                for key, val in cursor.fetchall():
                    defaults[key] = val
        except Exception:
            pass
        return defaults

    def count_transactions(self) -> int:
        try:
            with sqlite3.connect(SQLITE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM recharge_transactions WHERE is_sbpdcl = 1 AND verification_status = 'verified'")
                row = cursor.fetchone()
                return int(row[0]) if row else 0
        except Exception:
            return 0

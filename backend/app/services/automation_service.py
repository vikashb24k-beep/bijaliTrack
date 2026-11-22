from __future__ import annotations

import html
import logging
import re
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Any, Dict, List, Optional, Tuple

from app.services.database_service import DatabaseService
from app.services.gmail_service import GmailService

logger = logging.getLogger("bijlitrack.automation")

STANDARD_SBPDCL_BILLER = "South Bihar Power Distribution Company Limited (SBPDCL)"

# Realistic demo transactions for SBPDCL
DEMO_SBPDCL_TRANSACTIONS: List[Dict[str, Any]] = [
    {
        "id": "T2611062307359114829102",
        "transaction_id": "T2611062307359114829102",
        "upi_ref_no": "431289104921",
        "date": "2026-11-06T23:07:35+05:30",
        "transaction_date": "2026-11-06T23:07:35+05:30",
        "method": "PhonePe",
        "payment_method": "PhonePe",
        "amount": 900.0,
        "refund_amount": 0.0,
        "status": "Success",
        "source": "Gmail",
        "customer": "2341902819",
        "consumer_number": "2341902819",
        "biller_name": STANDARD_SBPDCL_BILLER,
        "is_sbpdcl": True,
        "verification_status": "verified",
        "subject": "Payment of Rs. 900 to South Bihar Power Distribution Company Limited (SBPDCL) is successful",
        "email_id": "msg-phonepe-sbpdcl-101",
        "snippet": "Paid Rs. 900.00 to SBPDCL. Txn ID: T2611062307359114829102. Consumer No: 2341902819.",
    },
    {
        "id": "T2610281145127632918451",
        "transaction_id": "T2610281145127632918451",
        "upi_ref_no": "430198273615",
        "date": "2026-10-28T11:45:12+05:30",
        "transaction_date": "2026-10-28T11:45:12+05:30",
        "method": "PhonePe",
        "payment_method": "PhonePe",
        "amount": 1250.0,
        "refund_amount": 0.0,
        "status": "Success",
        "source": "Gmail",
        "customer": "2341902819",
        "consumer_number": "2341902819",
        "biller_name": STANDARD_SBPDCL_BILLER,
        "is_sbpdcl": True,
        "verification_status": "verified",
        "subject": "Payment of Rs. 1,250 to South Bihar Power Distribution Company Limited (SBPDCL) is successful",
        "email_id": "msg-phonepe-sbpdcl-102",
        "snippet": "Paid Rs. 1,250.00 to SBPDCL. Txn ID: T2610281145127632918451. Consumer No: 2341902819.",
    },
    {
        "id": "T2609151820458192039182",
        "transaction_id": "T2609151820458192039182",
        "upi_ref_no": "425910283746",
        "date": "2026-09-15T18:20:45+05:30",
        "transaction_date": "2026-09-15T18:20:45+05:30",
        "method": "PhonePe",
        "payment_method": "PhonePe",
        "amount": 1100.0,
        "refund_amount": 0.0,
        "status": "Success",
        "source": "Gmail",
        "customer": "2341902819",
        "consumer_number": "2341902819",
        "biller_name": STANDARD_SBPDCL_BILLER,
        "is_sbpdcl": True,
        "verification_status": "verified",
        "subject": "Payment of Rs. 1,100 to South Bihar Power Distribution Company Limited is successful",
        "email_id": "msg-phonepe-sbpdcl-103",
        "snippet": "Paid Rs. 1,100.00 to South Bihar Power Distribution. Txn ID: T2609151820458192039182.",
    },
    {
        "id": "T2608100912301928374652",
        "transaction_id": "T2608100912301928374652",
        "upi_ref_no": "422198304918",
        "date": "2026-08-10T09:12:30+05:30",
        "transaction_date": "2026-08-10T09:12:30+05:30",
        "method": "PhonePe",
        "payment_method": "PhonePe",
        "amount": 1450.0,
        "refund_amount": 0.0,
        "status": "Success",
        "source": "Gmail",
        "customer": "2341902819",
        "consumer_number": "2341902819",
        "biller_name": STANDARD_SBPDCL_BILLER,
        "is_sbpdcl": True,
        "verification_status": "verified",
        "subject": "Payment of Rs. 1,450 to SBPDCL is successful",
        "email_id": "msg-phonepe-sbpdcl-104",
        "snippet": "Paid Rs. 1,450.00 to SBPDCL. Txn ID: T2608100912301928374652. Consumer No: 2341902819.",
    },
    {
        "id": "T2607141630119283746501",
        "transaction_id": "T2607141630119283746501",
        "upi_ref_no": "419203948571",
        "date": "2026-07-14T16:30:11+05:30",
        "transaction_date": "2026-07-14T16:30:11+05:30",
        "method": "PhonePe",
        "payment_method": "PhonePe",
        "amount": 1320.0,
        "refund_amount": 0.0,
        "status": "Success",
        "source": "Gmail",
        "customer": "2341902819",
        "consumer_number": "2341902819",
        "biller_name": STANDARD_SBPDCL_BILLER,
        "is_sbpdcl": True,
        "verification_status": "verified",
        "subject": "Payment of Rs. 1,320 to South Bihar Power Distribution is successful",
        "email_id": "msg-phonepe-sbpdcl-105",
        "snippet": "Paid Rs. 1,320.00 to SBPDCL. Txn ID: T2607141630119283746501.",
    },
    {
        "id": "T2606081015228192039481",
        "transaction_id": "T2606081015228192039481",
        "upi_ref_no": "415920384756",
        "date": "2026-06-08T10:15:22+05:30",
        "transaction_date": "2026-06-08T10:15:22+05:30",
        "method": "PhonePe",
        "payment_method": "PhonePe",
        "amount": 950.0,
        "refund_amount": 0.0,
        "status": "Success",
        "source": "Gmail",
        "customer": "2341902819",
        "consumer_number": "2341902819",
        "biller_name": STANDARD_SBPDCL_BILLER,
        "is_sbpdcl": True,
        "verification_status": "verified",
        "subject": "Payment of Rs. 950 to SBPDCL electricity is successful",
        "email_id": "msg-phonepe-sbpdcl-106",
        "snippet": "Paid Rs. 950.00 to SBPDCL. Txn ID: T2606081015228192039481.",
    },
]

DEMO_EMAIL_ACTIVITIES: List[Dict[str, Any]] = [
    {
        "id": "ACT-msg-phonepe-sbpdcl-101",
        "email_id": "msg-phonepe-sbpdcl-101",
        "sender": "no-reply@phonepe.com",
        "subject": "Payment of Rs. 900 to South Bihar Power Distribution Company Limited (SBPDCL) is successful",
        "received_date": "2026-11-06T23:07:35+05:30",
        "date": "2026-11-06T23:07:35+05:30",
        "extracted_amount": 900.0,
        "amount": 900.0,
        "detected_biller": STANDARD_SBPDCL_BILLER,
        "consumer_number": "2341902819",
        "transaction_id": "T2611062307359114829102",
        "upi_ref_no": "431289104921",
        "verification_status": "verified",
        "rejection_reason": "",
        "snippet": "Paid Rs. 900.00 to SBPDCL. Txn ID: T2611062307359114829102. Consumer No: 2341902819.",
    },
    {
        "id": "ACT-msg-phonepe-mobile-201",
        "email_id": "msg-phonepe-mobile-201",
        "sender": "no-reply@phonepe.com",
        "subject": "Recharge of Rs. 299 for Jio Prepaid Mobile is successful",
        "received_date": "2026-11-04T14:15:00+05:30",
        "date": "2026-11-04T14:15:00+05:30",
        "extracted_amount": 299.0,
        "amount": 299.0,
        "detected_biller": "Jio Mobile Recharge",
        "consumer_number": "98XXXXXXXX",
        "transaction_id": "T2611041415009182736451",
        "upi_ref_no": "430819283746",
        "verification_status": "rejected",
        "rejection_reason": "Non-SBPDCL: Mobile recharge detected",
        "snippet": "Your Jio prepaid mobile recharge of Rs. 299.00 was successful.",
    },
    {
        "id": "ACT-msg-phonepe-ambiguous-301",
        "email_id": "msg-phonepe-ambiguous-301",
        "sender": "no-reply@phonepe.com",
        "subject": "Electricity bill payment of Rs. 500 is successful",
        "received_date": "2026-10-15T09:30:00+05:30",
        "date": "2026-10-15T09:30:00+05:30",
        "extracted_amount": 500.0,
        "amount": 500.0,
        "detected_biller": "Uncertain Electricity Biller",
        "consumer_number": "104928192",
        "transaction_id": "T2610150930008192039485",
        "upi_ref_no": "428819203948",
        "verification_status": "review",
        "rejection_reason": "Uncertain biller: Electricity payment found, but SBPDCL was not explicitly confirmed",
        "snippet": "Electricity bill payment of Rs. 500.00 successful. Please verify biller.",
    },
]


# -----------------------------------------------------------------------------
# Parser & Regular Expressions (Robust Extraction)
# -----------------------------------------------------------------------------

def _extract_amount(text: str) -> float:
    """Extract payment amount in INR from text, handling commas, HTML entities, and symbols."""
    if not text:
        return 0.0

    # Unescape HTML entities (e.g. &#8377; for ₹, &nbsp;)
    clean = html.unescape(text)
    clean = clean.replace(",", "").replace("/-", "").replace("&nbsp;", " ")

    patterns = [
        # Explicit labels with currency or amount
        r"(?:paid|recharged?|amount|bill\s*amount|total(?:\s*amount)?)\s*[:\-=]?\s*(?:₹|INR|Rs\.?|Rs)?\s*([0-9]+(?:\.[0-9]{1,2})?)",
        # Currency prefix with numeric amount
        r"(?:₹|INR|Rs\.?|Rs)\s*([0-9]+(?:\.[0-9]{1,2})?)",
        # Amount followed by paid/debited/credited
        r"\b([0-9]+(?:\.[0-9]{1,2})?)\s*(?:paid|debited|credited|recharged)\b",
        # "Payment of Rs. X" or "Recharge of Rs. X"
        r"(?:payment|recharge)\s*of\s*(?:₹|INR|Rs\.?|Rs)?\s*([0-9]+(?:\.[0-9]{1,2})?)",
    ]

    for pattern in patterns:
        match = re.search(pattern, clean, flags=re.IGNORECASE)
        if match:
            try:
                amt = float(match.group(1))
                if 1.0 <= amt <= 1000000.0:
                    return round(amt, 2)
            except ValueError:
                continue

    return 0.0


def _extract_transaction_id(text: str, fallback_id: str) -> str:
    """Extract PhonePe Transaction ID (e.g. T26..., TXN..., P26...)."""
    clean = html.unescape(text or "")
    patterns = [
        r"(?:Txn\s*ID|Transaction\s*ID|PhonePe\s*Txn\s*ID|Reference\s*ID)\s*[:\-=]?\s*([A-Za-z0-9\-_]{10,32})",
        r"\b(T[0-9]{16,24})\b",
        r"\b(P[0-9]{16,24})\b",
        r"\b(TXN-[0-9A-Za-z]{5,})\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, clean, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return f"TXN-{fallback_id}"


def _extract_upi_ref(text: str) -> str:
    """Extract UPI reference / UTR number (usually 12 digits)."""
    clean = html.unescape(text or "")
    patterns = [
        r"(?:UPI\s*Ref(?:\s*No)?|UTR(?:\s*No)?|UPI\s*Txn\s*ID|Bank\s*Ref(?:\s*No)?)\s*[:\-=]?\s*([0-9]{10,14})",
        r"\bUTR\s*[:\-=]?\s*([0-9]{12})\b",
        r"\b([0-9]{12})\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, clean, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return ""


def _extract_consumer_number(text: str) -> str:
    """Extract SBPDCL consumer ID or CA number (e.g. CA No, Consumer ID, 9-12 digits)."""
    clean = html.unescape(text or "")
    patterns = [
        r"(?:Consumer\s*(?:No|Number|ID)|CA\s*No\.?|Account\s*No\.?|K\s*No\.?|Service\s*No\.?)\s*[:\-=]?\s*([0-9]{6,}X{2,}[0-9]{2,}|[0-9]{9,12})",
        r"\b(23[0-9]{8,10})\b",  # SBPDCL consumer numbers commonly start with 23
        r"\b([0-9]{10,12})\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, clean, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return ""


def _parse_payment_date(raw_date_header: str, text: str) -> str:
    """Parse actual payment date/time from body or Date header, outputting ISO 8601."""
    # First attempt to parse from standard email Date header
    if raw_date_header:
        try:
            dt = parsedate_to_datetime(raw_date_header)
            return dt.isoformat()
        except Exception:
            pass

    # Attempt to parse inline date like '06 Nov 2026, 11:07 PM' or '2026-11-06'
    date_match = re.search(
        r"(\d{1,2}\s+[A-Za-z]{3}\s+\d{4}(?:,?\s+\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM)?)?)",
        text or "",
    )
    if date_match:
        try:
            raw_str = date_match.group(1).replace(",", "")
            for fmt in (
                "%d %b %Y %I:%M:%S %p",
                "%d %b %Y %I:%M %p",
                "%d %b %Y %H:%M:%S",
                "%d %b %Y %H:%M",
                "%d %b %Y",
            ):
                try:
                    dt = datetime.strptime(raw_str, fmt)
                    return dt.isoformat()
                except ValueError:
                    continue
        except Exception:
            pass

    return datetime.utcnow().isoformat()


def _detect_status_and_refund(text: str) -> Tuple[str, float]:
    """Detect transaction status and refund amount."""
    low = (text or "").lower()
    if any(k in low for k in ["refunded", "refund initiated", "refund successful", "reversed"]):
        amt = _extract_amount(text)
        return "Refunded", amt
    if any(k in low for k in ["failed", "failure", "declined", "cancelled", "unsuccessful"]):
        return "Failed", 0.0
    if any(k in low for k in ["successful", "success", "paid", "completed", "credited", "recharged"]):
        return "Success", 0.0
    if any(k in low for k in ["pending", "processing", "in progress"]):
        return "Pending", 0.0
    return "Success", 0.0


def classify_and_verify_email(email_data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze email content to extract fields and verify whether it is an SBPDCL electricity receipt."""
    sender = str(email_data.get("from") or "")
    subject = str(email_data.get("subject") or "")
    snippet = str(email_data.get("snippet") or "")
    body = str(email_data.get("body") or "")
    raw_date = str(email_data.get("date") or "")
    email_id = str(email_data.get("id") or "unknown")

    combined_text = f"{sender} {subject} {snippet} {body}"
    lower = combined_text.lower()

    amount = _extract_amount(f"{subject} {snippet} {body}")
    txn_id = _extract_transaction_id(f"{subject} {snippet} {body}", email_id)
    upi_ref = _extract_upi_ref(f"{snippet} {body}")
    consumer_no = _extract_consumer_number(f"{subject} {snippet} {body}")
    txn_date = _parse_payment_date(raw_date, f"{snippet} {body}")
    status, refund_amount = _detect_status_and_refund(f"{subject} {snippet} {body}")

    # Check against user's configured default consumer number in settings
    db = DatabaseService()
    configured_consumer = db.get_setting("consumer_number", "")
    is_consumer_match = bool(configured_consumer and configured_consumer in combined_text)

    # Check for EXPLICIT non-electricity rejections
    # (Note: Standalone 'prepaid' or 'recharge' is NOT rejected because Bihar Smart Meters are Prepaid!)
    non_electricity_rejections = [
        (r"\b(mobile\s*recharge|prepaid\s*mobile|jio|airtel|vi\s*prepaid|vodafone|bsnl\s*mobile)\b", "Non-SBPDCL: Mobile recharge detected"),
        (r"\b(dth\s*recharge|tata\s*play|tata\s*sky|dish\s*tv|sun\s*direct|videocon\s*d2h)\b", "Non-SBPDCL: DTH recharge detected"),
        (r"\b(fastag|toll\s*payment)\b", "Non-SBPDCL: FASTag payment detected"),
        (r"\b(credit\s*card\s*bill|credit\s*card\s*payment)\b", "Non-SBPDCL: Credit card bill detected"),
        (r"\b(north\s*bihar|nbpdcl)\b", "Non-SBPDCL: North Bihar (NBPDCL) detected, not SBPDCL"),
        (r"\b(google\s*play\s*recharge|google\s*play\s*code)\b", "Non-SBPDCL: Google Play payment detected"),
        (r"\b(water\s*bill|cylinder|lpg\s*gas|piped\s*gas)\b", "Non-SBPDCL: Water or Gas bill detected"),
        (r"\b(paid\s*to\s+[a-z]+|money\s*sent\s*to|transfer\s*to\s*bank)\b", "Non-SBPDCL: Peer/Bank transfer detected"),
    ]

    # Check if this email is an explicit non-electricity payment
    has_sbpdcl_keyword = any(ind in lower for ind in ["sbpdcl", "south bihar", "bihar bijli", "bsphcl", "sugam"])
    for pattern, reason in non_electricity_rejections:
        if re.search(pattern, lower) and not has_sbpdcl_keyword and not is_consumer_match:
            return {
                "email_id": email_id,
                "id": txn_id,
                "transaction_id": txn_id,
                "upi_ref_no": upi_ref,
                "date": txn_date,
                "transaction_date": txn_date,
                "amount": amount,
                "refund_amount": refund_amount,
                "status": status,
                "source": "Gmail",
                "payment_method": "PhonePe",
                "method": "PhonePe",
                "biller_name": "Non-SBPDCL",
                "detected_biller": "Non-SBPDCL",
                "consumer_number": consumer_no or configured_consumer,
                "customer": consumer_no or configured_consumer,
                "is_sbpdcl": False,
                "verification_status": "rejected",
                "rejection_reason": reason,
                "subject": subject,
                "sender": sender,
                "snippet": snippet,
            }

    # SBPDCL identification indicators (comprehensive coverage for Bihar electricity)
    sbpdcl_indicators = [
        "sbpdcl",
        "south bihar power distribution",
        "south bihar power",
        "south bihar",
        "bihar bijli",
        "bihar sugam",
        "sugam smart meter",
        "bsphcl",
        "south bihar power - rapdrp",
        "south bihar power - non-rapdrp",
        "bihar state power holding",
    ]
    is_sbpdcl_confirmed = any(ind in lower for ind in sbpdcl_indicators) or is_consumer_match

    # General electricity keywords
    electricity_indicators = [
        "electricity",
        "power distribution",
        "bijli",
        "smart meter",
        "electric bill",
        "power recharge",
    ]
    is_general_electricity = any(ind in lower for ind in electricity_indicators)

    if is_sbpdcl_confirmed:
        return {
            "email_id": email_id,
            "id": txn_id,
            "transaction_id": txn_id,
            "upi_ref_no": upi_ref,
            "date": txn_date,
            "transaction_date": txn_date,
            "amount": amount,
            "refund_amount": refund_amount,
            "status": status,
            "source": "Gmail",
            "payment_method": "PhonePe",
            "method": "PhonePe",
            "biller_name": STANDARD_SBPDCL_BILLER,
            "detected_biller": STANDARD_SBPDCL_BILLER,
            "consumer_number": consumer_no or configured_consumer,
            "customer": consumer_no or configured_consumer,
            "is_sbpdcl": True,
            "verification_status": "verified",
            "rejection_reason": "",
            "subject": subject,
            "sender": sender,
            "snippet": snippet,
        }
    elif is_general_electricity:
        # Flag for user review in Email Activity
        return {
            "email_id": email_id,
            "id": txn_id,
            "transaction_id": txn_id,
            "upi_ref_no": upi_ref,
            "date": txn_date,
            "transaction_date": txn_date,
            "amount": amount,
            "refund_amount": refund_amount,
            "status": status,
            "source": "Gmail",
            "payment_method": "PhonePe",
            "method": "PhonePe",
            "biller_name": "Uncertain Electricity Biller",
            "detected_biller": "Uncertain Electricity Biller",
            "consumer_number": consumer_no or configured_consumer,
            "customer": consumer_no or configured_consumer,
            "is_sbpdcl": False,
            "verification_status": "review",
            "rejection_reason": "Uncertain biller: Electricity payment found, but SBPDCL biller was not confirmed. Click 'Verify' if this is your bill.",
            "subject": subject,
            "sender": sender,
            "snippet": snippet,
        }
    else:
        return {
            "email_id": email_id,
            "id": txn_id,
            "transaction_id": txn_id,
            "upi_ref_no": upi_ref,
            "date": txn_date,
            "transaction_date": txn_date,
            "amount": amount,
            "refund_amount": refund_amount,
            "status": status,
            "source": "Gmail",
            "payment_method": "PhonePe",
            "method": "PhonePe",
            "biller_name": "Unrelated",
            "detected_biller": "Unrelated",
            "consumer_number": consumer_no,
            "customer": consumer_no,
            "is_sbpdcl": False,
            "verification_status": "rejected",
            "rejection_reason": "Unrelated: Neither electricity nor SBPDCL keywords detected",
            "subject": subject,
            "sender": sender,
            "snippet": snippet,
        }


def parse_raw_text_receipt(raw_text: str, date_hint: Optional[str] = None) -> Dict[str, Any]:
    """Parse raw pasted receipt text from PhonePe or SMS/Email."""
    synthetic_id = f"manual-{int(datetime.utcnow().timestamp())}"
    email_data = {
        "id": synthetic_id,
        "from": "manual-entry@phonepe.com",
        "subject": raw_text[:80],
        "snippet": raw_text[:200],
        "body": raw_text,
        "date": date_hint or datetime.utcnow().isoformat(),
    }
    return classify_and_verify_email(email_data)


# -----------------------------------------------------------------------------
# Calculations & Aggregations
# -----------------------------------------------------------------------------

def calculate_monthly_spending(
    transactions: List[Dict[str, Any]],
    date_filter: str = "12m",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Calculate Net monthly expenditure = Successful payments - Refunds."""
    filtered = []
    now = datetime.now()

    for txn in transactions:
        if not txn.get("is_sbpdcl", True) or str(txn.get("verification_status", "")).lower() != "verified":
            continue

        raw_date = str(txn.get("transaction_date") or txn.get("date") or "")
        try:
            dt = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            continue

        # Range filter
        if date_filter == "6m":
            if (now.date() - dt.date()).days > 185:
                continue
        elif date_filter == "12m":
            if (now.date() - dt.date()).days > 370:
                continue
        elif date_filter == "year":
            if dt.year != now.year:
                continue
        elif date_filter == "all":
            pass
        elif date_filter == "custom":
            try:
                if start_date:
                    s_dt = datetime.fromisoformat(start_date)
                    if dt.date() < s_dt.date():
                        continue
                if end_date:
                    e_dt = datetime.fromisoformat(end_date)
                    if dt.date() > e_dt.date():
                        continue
            except Exception:
                pass

        filtered.append((dt, txn))

    # Aggregate by Year-Month
    monthly_data: Dict[str, Dict[str, Any]] = {}

    for dt, txn in filtered:
        month_key = dt.strftime("%Y-%m")
        month_label = dt.strftime("%B %Y")
        status = str(txn.get("status") or "").lower()

        if month_key not in monthly_data:
            monthly_data[month_key] = {
                "monthKey": month_key,
                "month": month_label,
                "totalPaid": 0.0,
                "refunds": 0.0,
                "amount": 0.0,
                "transactions": 0,
            }

        amount = float(txn.get("amount") or 0)
        refund = float(txn.get("refund_amount") or 0)

        if status == "success":
            monthly_data[month_key]["totalPaid"] += amount
            monthly_data[month_key]["transactions"] += 1
        elif status == "refunded":
            monthly_data[month_key]["refunds"] += (refund or amount)

    # Compute net amount: totalPaid - refunds
    result = []
    for month_key in sorted(monthly_data.keys()):
        item = monthly_data[month_key]
        net_amount = max(round(item["totalPaid"] - item["refunds"], 2), 0.0)
        item["amount"] = net_amount
        item["totalPaid"] = round(item["totalPaid"], 2)
        item["refunds"] = round(item["refunds"], 2)
        result.append(item)

    return result


def compute_dashboard_metrics(
    transactions: List[Dict[str, Any]],
    date_filter: str = "12m",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> Dict[str, Any]:
    """Compute the 4 important summary cards and chart data."""
    sbpdcl_txns = [
        t for t in transactions
        if t.get("is_sbpdcl", True) and str(t.get("verification_status", "")).lower() == "verified"
    ]

    now = datetime.now()
    current_month_key = now.strftime("%Y-%m")

    total_all_time = 0.0
    paid_this_month = 0.0
    payments_this_month_count = 0
    last_payment = None

    sorted_txns = sorted(
        sbpdcl_txns,
        key=lambda x: str(x.get("transaction_date") or x.get("date") or ""),
        reverse=True,
    )

    for txn in sorted_txns:
        status = str(txn.get("status") or "").lower()
        amount = float(txn.get("amount") or 0)
        refund = float(txn.get("refund_amount") or 0)
        raw_date = str(txn.get("transaction_date") or txn.get("date") or "")

        if status == "success":
            total_all_time += amount
            if raw_date.startswith(current_month_key):
                paid_this_month += amount
                payments_this_month_count += 1
            if last_payment is None:
                last_payment = {
                    "amount": amount,
                    "date": raw_date,
                    "transaction_id": txn.get("transaction_id") or txn.get("id"),
                    "biller": txn.get("biller_name") or STANDARD_SBPDCL_BILLER,
                }
        elif status == "refunded":
            total_all_time -= (refund or amount)
            if raw_date.startswith(current_month_key):
                paid_this_month -= (refund or amount)

    total_all_time = max(round(total_all_time, 2), 0.0)
    paid_this_month = max(round(paid_this_month, 2), 0.0)

    monthly_spending = calculate_monthly_spending(
        sbpdcl_txns,
        date_filter=date_filter,
        start_date=start_date,
        end_date=end_date,
    )

    return {
        "summary": {
            "totalPaidAllTime": total_all_time,
            "totalThisMonth": paid_this_month,
            "paymentsThisMonth": payments_this_month_count,
            "lastPayment": last_payment or {
                "amount": 0.0,
                "date": None,
                "transaction_id": "None",
                "biller": STANDARD_SBPDCL_BILLER,
            },
        },
        "monthlySpending": monthly_spending,
        "transactions": sorted_txns,
    }


# -----------------------------------------------------------------------------
# Main Sync Orchestration
# -----------------------------------------------------------------------------

def sync_gmail_transactions() -> Dict[str, Any]:
    """Execute complete synchronization flow with Gmail API."""
    db = DatabaseService()
    gmail = GmailService()

    auth_status = gmail.get_auth_status()
    if not auth_status["connected"]:
        db.set_setting("last_sync_status", f"Auth error: {auth_status['status']}")
        raise RuntimeError(f"Gmail synchronization blocked: {auth_status['status']}")

    # Search with pagination for all candidate messages over the last 2 years
    messages = gmail.search_electricity_messages(max_results=500)
    if not messages:
        now_iso = datetime.utcnow().isoformat()
        db.set_setting("last_sync_time", now_iso)
        db.set_setting("last_sync_status", "Success (0 new messages found)")
        return {
            "status": "ok",
            "message": "No new matching messages found",
            "saved_transactions": 0,
            "saved_activities": 0,
            "transactions": [],
        }

    transactions_to_save: List[Dict[str, Any]] = []
    activities_to_save: List[Dict[str, Any]] = []

    for msg_ref in messages:
        try:
            full_details = gmail.get_message_full_details(msg_ref["id"])
            classified = classify_and_verify_email(full_details)

            # Record in email activity log
            activities_to_save.append(classified)

            # If verified as SBPDCL, persist into main transactions
            if classified.get("is_sbpdcl") and classified.get("verification_status") == "verified":
                transactions_to_save.append(classified)
        except Exception as exc:
            logger.warning("Error processing email message %s: %s", msg_ref.get("id"), exc)
            continue

    saved_acts = db.upsert_email_activities(activities_to_save)
    saved_txns = db.upsert_transactions(transactions_to_save)

    now_iso = datetime.utcnow().isoformat()
    db.set_setting("last_sync_time", now_iso)
    db.set_setting("last_sync_status", f"Success ({saved_txns} verified payments saved)")

    return {
        "status": "ok",
        "last_sync_time": now_iso,
        "saved_transactions": saved_txns,
        "saved_activities": saved_acts,
        "total_scanned": len(messages),
        "transactions": transactions_to_save,
    }

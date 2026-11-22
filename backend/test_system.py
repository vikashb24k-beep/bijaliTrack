from __future__ import annotations

import json
from datetime import datetime

from app.services.automation_service import (
    calculate_monthly_spending,
    classify_and_verify_email,
    compute_dashboard_metrics,
)
from app.services.database_service import DatabaseService


def test_payment_calculations():
    print("Testing Payment Calculation Rules...")
    test_txns = [
        # Two successful payments in Nov 2026
        {
            "id": "T-1",
            "transaction_date": "2026-11-02T10:00:00+05:30",
            "amount": 1000.0,
            "refund_amount": 0.0,
            "status": "Success",
            "is_sbpdcl": True,
            "verification_status": "verified",
        },
        {
            "id": "T-2",
            "transaction_date": "2026-11-15T12:00:00+05:30",
            "amount": 500.0,
            "refund_amount": 0.0,
            "status": "Success",
            "is_sbpdcl": True,
            "verification_status": "verified",
        },
        # One refund in Nov 2026: 200
        {
            "id": "T-3",
            "transaction_date": "2026-11-20T14:00:00+05:30",
            "amount": 200.0,
            "refund_amount": 200.0,
            "status": "Refunded",
            "is_sbpdcl": True,
            "verification_status": "verified",
        },
        # One failed transaction in Nov 2026 (should NOT be counted)
        {
            "id": "T-4",
            "transaction_date": "2026-11-22T08:00:00+05:30",
            "amount": 800.0,
            "refund_amount": 0.0,
            "status": "Failed",
            "is_sbpdcl": True,
            "verification_status": "verified",
        },
        # One pending transaction in Nov 2026 (should NOT be counted)
        {
            "id": "T-5",
            "transaction_date": "2026-11-23T09:00:00+05:30",
            "amount": 400.0,
            "refund_amount": 0.0,
            "status": "Pending",
            "is_sbpdcl": True,
            "verification_status": "verified",
        },
        # Non-SBPDCL transaction (should NOT be counted)
        {
            "id": "T-6",
            "transaction_date": "2026-11-10T09:00:00+05:30",
            "amount": 999.0,
            "refund_amount": 0.0,
            "status": "Success",
            "is_sbpdcl": False,
            "verification_status": "rejected",
        },
    ]

    monthly = calculate_monthly_spending(test_txns, date_filter="12m")
    assert len(monthly) == 1, f"Expected 1 month, got {len(monthly)}"
    nov_data = monthly[0]
    # Net = (1000 + 500) - 200 = 1300
    expected_net = 1300.0
    assert nov_data["amount"] == expected_net, f"Expected {expected_net}, got {nov_data['amount']}"
    assert nov_data["transactions"] == 2, f"Expected 2 successful transactions, got {nov_data['transactions']}"
    print(f"✓ Calculation check passed: Net Nov 2026 = ₹{nov_data['amount']} (Total ₹{nov_data['totalPaid']} - Refunds ₹{nov_data['refunds']})")


def test_sbpdcl_email_verification():
    print("\nTesting SBPDCL Email Parsing & Verification...")

    # Case 1: Legitimate SBPDCL PhonePe receipt
    email_sbpdcl = {
        "id": "18c21a4f",
        "from": "no-reply@phonepe.com",
        "subject": "Payment of Rs. 1,200 to South Bihar Power Distribution Company Limited (SBPDCL) is successful",
        "snippet": "Paid Rs. 1,200.00 to SBPDCL. Txn ID: T2611062307359114829102. UTR: 431289104921. Consumer No: 2341902819.",
        "date": "Wed, 06 Nov 2026 23:07:35 +0530",
    }
    res1 = classify_and_verify_email(email_sbpdcl)
    assert res1["verification_status"] == "verified", f"Expected verified, got {res1['verification_status']}"
    assert res1["is_sbpdcl"] is True
    assert res1["amount"] == 1200.0
    assert res1["transaction_id"] == "T2611062307359114829102"
    assert res1["upi_ref_no"] == "431289104921"
    assert res1["consumer_number"] == "2341902819"
    print("✓ Confirmed SBPDCL payment correctly verified with all fields extracted")

    # Case 2: Mobile recharge (Must be rejected)
    email_mobile = {
        "id": "18c21a50",
        "from": "no-reply@phonepe.com",
        "subject": "Recharge of Rs. 299 for Jio Prepaid is successful",
        "snippet": "Your Jio prepaid mobile recharge of Rs. 299 was successful. Txn ID: T261104141500.",
        "date": "Tue, 04 Nov 2026 14:15:00 +0530",
    }
    res2 = classify_and_verify_email(email_mobile)
    assert res2["verification_status"] == "rejected", f"Expected rejected, got {res2['verification_status']}"
    assert res2["is_sbpdcl"] is False
    print(f"✓ Mobile recharge correctly rejected: '{res2['rejection_reason']}'")

    # Case 3: Uncertain electricity bill (Must be placed in review)
    email_uncertain = {
        "id": "18c21a51",
        "from": "no-reply@phonepe.com",
        "subject": "Electricity bill payment of Rs. 650 is successful",
        "snippet": "Paid Rs. 650.00 for electricity bill. Txn ID: T261015093000.",
        "date": "Thu, 15 Oct 2026 09:30:00 +0530",
    }
    res3 = classify_and_verify_email(email_uncertain)
    assert res3["verification_status"] == "review", f"Expected review, got {res3['verification_status']}"
    print(f"✓ Ambiguous biller correctly flagged for review: '{res3['rejection_reason']}'")


def test_database_service():
    print("\nTesting Database Storage & SQLite Fallback...")
    db = DatabaseService()
    print(f"Database Service online. Supabase connected: {db.is_supabase_connected}")

    # Set and get settings
    db.set_setting("consumer_number", "2341902819")
    val = db.get_setting("consumer_number")
    assert val == "2341902819", f"Expected 2341902819, got {val}"
    print("✓ App settings storage verified")


if __name__ == "__main__":
    test_payment_calculations()
    test_sbpdcl_email_verification()
    test_database_service()
    print("\nALL SYSTEM TESTS PASSED!")

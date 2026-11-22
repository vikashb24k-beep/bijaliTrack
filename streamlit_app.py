import html
import io
import os
import sys
from datetime import datetime
from pathlib import Path

# Add backend directory to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR / "backend"))

import streamlit as st

# Propagate Streamlit Cloud secrets to environment variables if present
try:
    if hasattr(st, "secrets"):
        for _k, _v in st.secrets.items():
            if isinstance(_v, str) and _k not in os.environ:
                os.environ[_k] = _v
except Exception:
    pass

try:
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
except ImportError:
    pd = None
    px = None
    go = None

from app.services.automation_service import (
    DEMO_EMAIL_ACTIVITIES,
    DEMO_SBPDCL_TRANSACTIONS,
    STANDARD_SBPDCL_BILLER,
    calculate_monthly_spending,
    compute_dashboard_metrics,
    parse_raw_text_receipt,
    sync_gmail_transactions,
)
from app.services.database_service import DatabaseService
from app.services.gmail_service import GmailService

# -----------------------------------------------------------------------------
# Streamlit App Configuration & Custom Theme
# -----------------------------------------------------------------------------

st.set_page_config(
    page_title="BijliTrack – SBPDCL Electricity Bill Tracker",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    /* Metric & Card styling */
    .metric-card {
        background: rgba(17, 24, 39, 0.7);
        border: 1px solid rgba(148, 163, 184, 0.18);
        border-radius: 16px;
        padding: 18px 20px;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
        margin-bottom: 12px;
    }
    .metric-title {
        font-size: 0.76rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #94A3B8;
        margin-bottom: 6px;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        color: #F8FAFC;
    }
    .metric-subtitle {
        font-size: 0.8rem;
        color: #60A5FA;
        margin-top: 4px;
    }

    /* Badges */
    .badge-verified {
        background-color: rgba(34, 197, 94, 0.18);
        color: #86EFAC;
        border: 1px solid rgba(34, 197, 94, 0.3);
        padding: 3px 10px;
        border-radius: 999px;
        font-size: 0.74rem;
        font-weight: 700;
        display: inline-block;
    }
    .badge-review {
        background-color: rgba(245, 158, 11, 0.18);
        color: #FBBF24;
        border: 1px solid rgba(245, 158, 11, 0.3);
        padding: 3px 10px;
        border-radius: 999px;
        font-size: 0.74rem;
        font-weight: 700;
        display: inline-block;
    }
    .badge-rejected {
        background-color: rgba(239, 68, 68, 0.18);
        color: #FCA5A5;
        border: 1px solid rgba(239, 68, 68, 0.3);
        padding: 3px 10px;
        border-radius: 999px;
        font-size: 0.74rem;
        font-weight: 700;
        display: inline-block;
    }

    /* Custom banner */
    .demo-callout {
        background: rgba(99, 102, 241, 0.12);
        border: 1px solid rgba(99, 102, 241, 0.3);
        border-radius: 12px;
        padding: 12px 18px;
        margin-bottom: 20px;
        color: #C7D2FE;
        font-size: 0.9rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def format_inr(amount: float) -> str:
    """Format floating currency into Indian Rupee format."""
    return f"₹{amount:,.2f}"


def format_date(date_str: str) -> str:
    if not date_str:
        return "Unknown"
    try:
        dt = datetime.fromisoformat(str(date_str).replace("Z", "+00:00"))
        return dt.strftime("%d %b %Y, %I:%M %p")
    except Exception:
        return str(date_str)[:19]


# -----------------------------------------------------------------------------
# Core State & Services
# -----------------------------------------------------------------------------

db = DatabaseService()
gmail = GmailService()
gmail_auth = gmail.get_auth_status()
all_settings = db.get_all_settings()

real_txns = db.fetch_recent_transactions(only_sbpdcl=True, limit=1000)
is_demo = len(real_txns) == 0
active_txns = real_txns if not is_demo else DEMO_SBPDCL_TRANSACTIONS


# -----------------------------------------------------------------------------
# Sidebar Navigation
# -----------------------------------------------------------------------------

with st.sidebar:
    st.markdown("### ⚡ **BijliTrack**")
    st.caption("Exclusively for SBPDCL, Bihar")
    st.markdown("---")

    page = st.radio(
        "Navigation",
        ["📊 Dashboard", "💳 Transactions", "✉️ Email Activity", "⚙️ Settings"],
        index=0,
    )

    st.markdown("---")
    st.markdown("#### 🔄 Gmail Synchronization")

    last_sync = all_settings.get("last_sync_time")
    if last_sync:
        st.caption(f"Last synced: {format_date(last_sync)}")
    else:
        st.caption("Last synced: Never")

    if gmail_auth.get("connected"):
        st.success("Gmail: Connected (Active)", icon="✅")
    else:
        st.warning("Gmail: Action Required", icon="⚠️")

    if st.button("⚡ Sync Gmail Now", use_container_width=True, type="primary"):
        with st.spinner("Connecting to Gmail and scanning SBPDCL PhonePe receipts..."):
            try:
                res = sync_gmail_transactions()
                st.success(f"Sync complete! Saved {res.get('saved_transactions', 0)} verified bills.")
                st.rerun()
            except Exception as exc:
                st.error(f"Sync error: {exc}")

    st.markdown("---")
    st.caption("Utility: **SBPDCL (South Bihar Power)**")
    st.caption(f"Backend: {'Supabase + SQLite' if db.is_supabase_connected else 'Local SQLite'}")


# -----------------------------------------------------------------------------
# PAGE 1: 📊 DASHBOARD
# -----------------------------------------------------------------------------

if page == "📊 Dashboard":
    st.title("⚡ SBPDCL Electricity Bill Dashboard")
    st.caption(f"Smart meter finance overview • Today is {datetime.now().strftime('%A, %d %B %Y')}")

    if is_demo:
        st.markdown(
            """
            <div class="demo-callout">
                <strong>💡 Sample Demonstration Mode:</strong>
                You are currently viewing verified SBPDCL sample bills. Connect your Gmail account in <strong>Settings</strong> or click <strong>Sync Gmail Now</strong> to load your live current bills.
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Date Range Filter Controls
    col_range, col_custom1, col_custom2 = st.columns([2, 1, 1])

    with col_range:
        range_choice = st.radio(
            "Time Range Filter:",
            ["Last 6 Months", "Last 12 Months", "Current Year", "All Time", "Custom Range"],
            index=1,
            horizontal=True,
        )

    range_map = {
        "Last 6 Months": "6m",
        "Last 12 Months": "12m",
        "Current Year": "year",
        "All Time": "all",
        "Custom Range": "custom",
    }
    active_range_code = range_map[range_choice]

    start_date_val = None
    end_date_val = None

    if active_range_code == "custom":
        with col_custom1:
            d_start = st.date_input("Start Date", value=None)
            if d_start:
                start_date_val = d_start.isoformat()
        with col_custom2:
            d_end = st.date_input("End Date", value=None)
            if d_end:
                end_date_val = d_end.isoformat()

    metrics = compute_dashboard_metrics(
        active_txns,
        date_filter=active_range_code,
        start_date=start_date_val,
        end_date=end_date_val,
    )
    summary = metrics["summary"]

    # 4 Summary Cards
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Total Electricity Payments</div>
                <div class="metric-value">{format_inr(summary['totalPaidAllTime'])}</div>
                <div class="metric-subtitle">All-time net successful recharges</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Total Paid This Month</div>
                <div class="metric-value" style="color: #86EFAC;">{format_inr(summary['totalThisMonth'])}</div>
                <div class="metric-subtitle">Net expenditure this calendar month</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c3:
        p_count = summary["paymentsThisMonth"]
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Payments This Month</div>
                <div class="metric-value" style="color: #C4B5FD;">{p_count} {'recharge' if p_count == 1 else 'recharges'}</div>
                <div class="metric-subtitle">Confirmed PhonePe transactions</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c4:
        lp = summary.get("lastPayment")
        lp_val = format_inr(lp["amount"]) if lp and lp.get("amount") else "₹0.00"
        lp_date = format_date(lp["date"]) if lp and lp.get("date") else "No payment recorded"
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Last Payment Amount & Date</div>
                <div class="metric-value" style="color: #67E8F9;">{lp_val}</div>
                <div class="metric-subtitle">{lp_date}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Monthly Payment Summary: Chart & Table
    st.subheader("📈 Monthly Payment Summary")
    st.caption("Net monthly expenditure = Successful payments − Refunds")

    monthly_spending = metrics["monthlySpending"]

    chart_col, table_col = st.columns([1.4, 1.0])

    with chart_col:
        if monthly_spending and px is not None:
            df_chart = pd.DataFrame(monthly_spending)
            fig = px.bar(
                df_chart,
                x="month",
                y="amount",
                labels={"month": "Month", "amount": "Total Paid (₹)"},
                title="Electricity Money Paid in Each Month",
                text="amount",
            )
            fig.update_traces(
                marker_color="#6366F1",
                texttemplate="₹%{text:,.0f}",
                textposition="outside",
                hovertemplate="<b>%{x}</b><br>Paid: ₹%{y:,.2f}<extra></extra>",
            )
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=20, r=20, t=40, b=20),
                height=350,
                font=dict(color="#94A3B8"),
            )
            st.plotly_chart(fig, use_container_width=True)
        elif monthly_spending:
            st.bar_chart({row["month"]: row["amount"] for row in monthly_spending})
        else:
            st.info("No monthly payment records match the current filter.")

    with table_col:
        if monthly_spending:
            df_table = pd.DataFrame([
                {
                    "Month": row["month"],
                    "Total Paid": format_inr(row["amount"]),
                    "Transactions": f"{row['transactions']} payments",
                }
                for row in monthly_spending
            ])
            st.dataframe(df_table, use_container_width=True, hide_index=True)
        else:
            st.info("No monthly breakdown available.")

    st.markdown("<br>", unsafe_allow_html=True)

    # Recent Verified Transactions Table
    st.subheader("🧾 Recent Verified SBPDCL Payments")
    recent = active_txns[:6]
    if recent:
        df_recent = pd.DataFrame([
            {
                "Date": format_date(r.get("transaction_date") or r.get("date")),
                "Amount": format_inr(r.get("amount", 0.0)),
                "Biller": r.get("biller_name", STANDARD_SBPDCL_BILLER),
                "Transaction ID": r.get("transaction_id") or r.get("id"),
                "Consumer No": r.get("consumer_number") or r.get("customer") or "—",
                "Status": r.get("status", "Success"),
            }
            for r in recent
        ])
        st.dataframe(df_recent, use_container_width=True, hide_index=True)


# -----------------------------------------------------------------------------
# PAGE 2: 💳 TRANSACTIONS LEDGER
# -----------------------------------------------------------------------------

elif page == "💳 Transactions":
    st.title("💳 SBPDCL Payment Ledger")
    st.caption("Complete verified electricity bill payment records")

    # Add Receipt & Export Buttons
    col_act1, col_act2 = st.columns([3, 1])

    with col_act1:
        with st.expander("➕ Paste / Detect Bill Receipt (Manual Entry / SMS)"):
            st.caption("Paste any PhonePe receipt email text, subject, or SMS message below:")
            raw_input_text = st.text_area(
                "Receipt Text",
                placeholder="e.g. Payment of Rs. 950 to South Bihar Power Distribution Company Limited (SBPDCL) is successful. Txn ID: T2611... Consumer No: 2341902819.",
                height=100,
            )
            manual_date = st.date_input("Payment Date (Optional)", value=None)
            if st.button("Parse & Save Bill", type="primary"):
                if raw_input_text.strip():
                    parsed = parse_raw_text_receipt(
                        raw_input_text,
                        d_hint=manual_date.isoformat() if manual_date else None,
                    )
                    db.upsert_email_activities([parsed])
                    if parsed.get("is_sbpdcl") and parsed.get("verification_status") == "verified":
                        db.upsert_transactions([parsed])
                        st.success(f"Success! Detected {format_inr(parsed['amount'])} for {parsed['detected_biller']}. Added to ledger.")
                        st.rerun()
                    else:
                        st.warning("Receipt logged in Email Activity under review.")

    with col_act2:
        # Formatted CSV Export
        if pd is not None and active_txns:
            df_export = pd.DataFrame([
                {
                    "Payment Date": format_date(r.get("transaction_date") or r.get("date")),
                    "Amount (INR)": r.get("amount", 0.0),
                    "Biller": r.get("biller_name", STANDARD_SBPDCL_BILLER),
                    "Transaction ID": r.get("transaction_id") or r.get("id", ""),
                    "UPI Reference (UTR)": r.get("upi_ref_no", ""),
                    "Consumer Number": r.get("consumer_number") or r.get("customer", ""),
                    "Status": r.get("status", "Success"),
                }
                for r in active_txns
            ])
            csv_data = df_export.to_csv(index=False)
            st.download_button(
                label="📥 Export to CSV",
                data=csv_data,
                file_name="sbpdcl_transactions.csv",
                mime="text/csv",
                use_container_width=True,
            )

    st.markdown("---")

    # Filter Bar
    f1, f2, f3, f4 = st.columns([2, 1, 1, 1])

    with f1:
        search_query = st.text_input("🔍 Search", placeholder="Txn ID, Consumer No, Amount, UTR...")

    with f2:
        status_filter = st.selectbox(
            "Status",
            ["All", "Success", "Refunded", "Failed", "Pending"],
            index=0,
        )

    with f3:
        month_names = ["All Months", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        selected_month = st.selectbox("Month", month_names, index=0)

    with f4:
        selected_year = st.selectbox("Year", ["All Years", "2026", "2025", "2024"], index=0)

    month_num_map = {name: f"{i:02d}" for i, name in enumerate(month_names[1:], start=1)}
    target_month_num = month_num_map.get(selected_month, "")

    filtered = []
    for t in active_txns:
        # Search filter
        if search_query:
            sq = search_query.lower()
            text_match = (
                sq in str(t.get("id", "")).lower()
                or sq in str(t.get("transaction_id", "")).lower()
                or sq in str(t.get("consumer_number", "")).lower()
                or sq in str(t.get("upi_ref_no", "")).lower()
                or sq in str(t.get("amount", "")).lower()
                or sq in str(t.get("biller_name", "")).lower()
            )
            if not text_match:
                continue

        # Status filter
        if status_filter != "All":
            if str(t.get("status", "")).lower() != status_filter.lower():
                continue

        # Month & Year filters
        dt_str = str(t.get("transaction_date") or t.get("date") or "")
        if selected_year != "All Years" and not dt_str.startswith(selected_year):
            continue
        if target_month_num and f"-{target_month_num}-" not in dt_str:
            continue

        filtered.append(t)

    st.caption(f"Showing **{len(filtered)}** matching {'payment' if len(filtered) == 1 else 'payments'}")

    if filtered and pd is not None:
        df_ledger = pd.DataFrame([
            {
                "Date & Time": format_date(r.get("transaction_date") or r.get("date")),
                "Amount": format_inr(r.get("amount", 0.0)),
                "Biller": r.get("biller_name", STANDARD_SBPDCL_BILLER),
                "Transaction ID": r.get("transaction_id") or r.get("id"),
                "UPI Reference (UTR)": r.get("upi_ref_no") or "—",
                "Consumer No": r.get("consumer_number") or r.get("customer") or "—",
                "Status": r.get("status", "Success"),
            }
            for r in filtered
        ])
        st.dataframe(df_ledger, use_container_width=True, hide_index=True)

        with st.expander("🔍 Inspect Full Transaction Details"):
            id_options = [str(t.get("transaction_id") or t.get("id") or f"TXN-{idx}") for idx, t in enumerate(filtered)]
            selected_id = st.selectbox(
                "Select Transaction ID to inspect:",
                id_options,
            )
            matched = next(
                (t for idx, t in enumerate(filtered) if str(t.get("transaction_id") or t.get("id") or f"TXN-{idx}") == selected_id),
                None,
            )
            if matched:
                d1, d2 = st.columns(2)
                with d1:
                    st.write(f"**Amount:** {format_inr(matched.get('amount', 0))}")
                    st.write(f"**Status:** {matched.get('status')}")
                    st.write(f"**Date:** {format_date(matched.get('transaction_date') or matched.get('date'))}")
                    st.write(f"**Biller:** {matched.get('biller_name')}")
                with d2:
                    st.write(f"**Txn ID:** `{matched.get('transaction_id') or matched.get('id')}`")
                    st.write(f"**UPI Ref:** `{matched.get('upi_ref_no') or 'None'}`")
                    st.write(f"**Consumer No:** `{matched.get('consumer_number') or 'None'}`")
                    st.write(f"**Source:** {matched.get('source')}")
                if matched.get("snippet"):
                    st.text_area("Email Snippet", matched.get("snippet"), disabled=True)
    else:
        st.info("No verified SBPDCL transactions match the current filter criteria.")


# -----------------------------------------------------------------------------
# PAGE 3: ✉️ EMAIL ACTIVITY
# -----------------------------------------------------------------------------

elif page == "✉️ Email Activity":
    st.title("✉️ Gmail Detection & Audit Activity")
    st.caption("Complete record of scanned PhonePe confirmation emails")

    real_acts = db.fetch_email_activities(limit=200)
    activities = real_acts if real_acts else DEMO_EMAIL_ACTIVITIES

    # Tabs
    tab_all, tab_ver, tab_rev, tab_rej = st.tabs([
        f"All ({len(activities)})",
        f"Verified ({sum(1 for a in activities if a.get('verification_status') == 'verified')})",
        f"Review Needed ({sum(1 for a in activities if a.get('verification_status') == 'review')})",
        f"Rejected ({sum(1 for a in activities if a.get('verification_status') == 'rejected')})",
    ])

    search_act = st.text_input("Filter email subject or biller name", "")

    def render_email_list(items: list):
        if search_act:
            items = [
                a for a in items
                if search_act.lower() in str(a.get("subject", "")).lower()
                or search_act.lower() in str(a.get("detected_biller", "")).lower()
                or search_act.lower() in str(a.get("sender", "")).lower()
            ]

        if not items:
            st.info("No email activity records in this view.")
            return

        for act in items:
            v_status = act.get("verification_status", "review")
            badge_class = f"badge-{v_status}"
            badge_text = "Verified SBPDCL" if v_status == "verified" else ("Review Needed" if v_status == "review" else "Rejected")

            with st.container():
                st.markdown(
                    f"""
                    <div style="border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 12px; padding: 14px 18px; margin-bottom: 12px; background: rgba(17, 24, 39, 0.4);">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <strong style="font-size: 1.05rem;">{html.escape(str(act.get('subject') or 'No subject'))}</strong>
                            <span class="{badge_class}">{badge_text}</span>
                        </div>
                        <div style="margin-top: 6px; color: #94A3B8; font-size: 0.85rem;">
                            <span>📅 {format_date(act.get('received_date') or act.get('date'))}</span> &nbsp;•&nbsp;
                            <span>💰 {format_inr(act.get('extracted_amount') or act.get('amount') or 0)}</span> &nbsp;•&nbsp;
                            <span>🏢 {html.escape(str(act.get('detected_biller') or 'Unknown'))}</span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                with st.expander(f"View details for {act.get('email_id')}"):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.write(f"**Sender:** {act.get('sender')}")
                        st.write(f"**Amount Extracted:** {format_inr(act.get('extracted_amount') or act.get('amount') or 0)}")
                        st.write(f"**Txn ID:** `{act.get('transaction_id') or 'None'}`")
                    with c2:
                        st.write(f"**Biller:** {act.get('detected_biller')}")
                        st.write(f"**Consumer No:** {act.get('consumer_number') or 'None'}")
                        st.write(f"**UPI Ref:** {act.get('upi_ref_no') or 'None'}")

                    if act.get("rejection_reason"):
                        st.error(f"Reason: {act.get('rejection_reason')}")

                    if act.get("snippet"):
                        st.text_area("Email Snippet", act.get("snippet"), key=f"snip_{act.get('email_id')}", disabled=True)

                    btn_c1, btn_c2, btn_c3 = st.columns([1, 1, 2])
                    email_msg_id = act.get("email_id") or act.get("id")
                    with btn_c1:
                        st.link_button("🌐 Open in Gmail", f"https://mail.google.com/mail/u/0/#inbox/{email_msg_id}")

                    if v_status == "review":
                        with btn_c2:
                            if st.button("✅ Verify as SBPDCL", key=f"ver_{email_msg_id}", type="primary"):
                                db.update_email_status(email_msg_id, "verified")
                                st.success("Verified and promoted to transactions ledger!")
                                st.rerun()
                        with btn_c3:
                            if st.button("❌ Reject", key=f"rej_{email_msg_id}"):
                                db.update_email_status(email_msg_id, "rejected", "Manually rejected by user")
                                st.warning("Marked as rejected.")
                                st.rerun()

    with tab_all:
        render_email_list(activities)

    with tab_ver:
        render_email_list([a for a in activities if a.get("verification_status") == "verified"])

    with tab_rev:
        render_email_list([a for a in activities if a.get("verification_status") == "review"])

    with tab_rej:
        render_email_list([a for a in activities if a.get("verification_status") == "rejected"])


# -----------------------------------------------------------------------------
# PAGE 4: ⚙️ SETTINGS
# -----------------------------------------------------------------------------

elif page == "⚙️ Settings":
    st.title("⚙️ BijliTrack Preferences & Settings")
    st.caption("Manage Gmail authentication, consumer number, and sync rules")

    # Gmail Connection Section
    st.subheader("🔑 Google Gmail OAuth2 Integration")
    if gmail_auth.get("connected"):
        st.success("Gmail API is authenticated with read-only access (gmail.readonly).", icon="✅")
    else:
        st.warning("Gmail token is expired, revoked, or not yet authorized.", icon="⚠️")
        if gmail_auth.get("error"):
            st.error(f"Status Note: {gmail_auth.get('error')}")

    col_auth1, col_auth2 = st.columns([1, 1])
    with col_auth1:
        if st.button("🔄 Local OAuth Browser Sign-in", type="primary", use_container_width=True):
            with st.spinner("Opening Google OAuth consent flow..."):
                try:
                    cred_path = BASE_DIR / "backend" / "credentials.json"
                    if not cred_path.exists():
                        st.error("Missing backend/credentials.json! Download your OAuth Client ID JSON from Google Cloud Console.")
                    else:
                        from google_auth_oauthlib.flow import InstalledAppFlow
                        flow = InstalledAppFlow.from_client_secrets_file(
                            str(cred_path),
                            ["https://www.googleapis.com/auth/gmail.readonly"],
                        )
                        creds = flow.run_local_server(port=0, prompt="consent")
                        token_file = BASE_DIR / "backend" / "token.json"
                        token_file.write_text(creds.to_json(), encoding="utf-8")
                        st.success("Gmail authenticated successfully! You can now scan for your bills.")
                        st.rerun()
                except Exception as exc:
                    st.error(f"Authentication failed: {exc}")
                    st.caption("For headless or cloud servers, use the Cloud Token Setup below.")

    with col_auth2:
        with st.expander("☁️ Cloud Deployment Token Setup (Streamlit Cloud / Docker)"):
            st.caption("When deploying to Streamlit Cloud or remote servers, paste your authorized token or upload `token.json` directly:")
            token_upload = st.file_uploader("Upload token.json", type=["json"], key="cloud_tok_upload")
            if token_upload:
                try:
                    tok_content = token_upload.read().decode("utf-8")
                    token_file = BASE_DIR / "backend" / "token.json"
                    token_file.write_text(tok_content, encoding="utf-8")
                    st.success("Uploaded token.json saved successfully!")
                    st.rerun()
                except Exception as e_tok:
                    st.error(f"Error saving token file: {e_tok}")

            token_pasted = st.text_area("Or Paste token.json contents:", placeholder='{"token": "ya29...", "refresh_token": "..."}', height=70)
            if st.button("Save Pasted Token"):
                if token_pasted.strip():
                    try:
                        token_file = BASE_DIR / "backend" / "token.json"
                        token_file.write_text(token_pasted.strip(), encoding="utf-8")
                        st.success("Token saved successfully!")
                        st.rerun()
                    except Exception as e_paste:
                        st.error(f"Error: {e_paste}")

    st.markdown("---")

    # Consumer Number & Preferences Form
    st.subheader("⚡ Electricity Preferences")
    with st.form("settings_form"):
        cons_num = st.text_input(
            "Default SBPDCL Consumer Number (CA No.)",
            value=all_settings.get("consumer_number", "2341902819"),
            help="Your 9-12 digit SBPDCL consumer account number.",
        )
        sync_int = st.selectbox(
            "Automatic Background Sync Interval",
            ["15 minutes", "30 minutes (Recommended)", "1 hour", "6 hours"],
            index=1,
        )
        auto_sync = st.checkbox(
            "Enable background automated synchronization",
            value=all_settings.get("auto_sync_enabled", "true").lower() == "true",
        )

        submitted = st.form_submit_button("Save Preferences", type="primary")
        if submitted:
            int_map = {
                "15 minutes": "15",
                "30 minutes (Recommended)": "30",
                "1 hour": "60",
                "6 hours": "360",
            }
            db.set_setting("consumer_number", cons_num.strip())
            db.set_setting("sync_interval_minutes", int_map.get(sync_int, "30"))
            db.set_setting("auto_sync_enabled", "true" if auto_sync else "false")
            st.success("Preferences updated successfully!")
            st.rerun()

    st.markdown("---")

    # Storage Architecture
    st.subheader("🗄️ Storage & Database Status")
    st.write(f"**Cloud Database:** {'Connected to Supabase PostgreSQL' if db.is_supabase_connected else 'Offline / Local SQLite Cache Active'}")
    st.write(f"**Local Database File:** `{BASE_DIR / 'backend' / 'bijlitrack.db'}`")
    st.caption("Dual-layer persistence ensures zero data loss even when offline or if cloud projects are paused.")

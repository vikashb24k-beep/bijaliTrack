# BijliTrack – Automatic SBPDCL Electricity Bill Payment Tracker

**BijliTrack** is a simple, dedicated personal electricity bill payment tracking website built exclusively for **South Bihar Power Distribution Company Limited (SBPDCL)**, Bihar.

It connects to your Gmail account using the Gmail API, automatically detects PhonePe electricity payment confirmation emails, verifies SBPDCL biller receipts, extracts transaction details, and computes your net monthly electricity expenses.

---

## ⚡ Key Features

1. **Focused Dashboard:**
   - **4 Summary Cards:**
     - Total electricity bill payments (all-time net).
     - Total paid this month.
     - Number of payments this month.
     - Last payment amount and date.
   - **Monthly Payment Summary:**
     - Interactive monthly payment bar chart.
     - Monthly breakdown table: `Month | Total Paid | Transactions`.
     - Multi-range filters: Last 6 Months, Last 12 Months, Current Year, and Custom Date Range.
   - **Recent SBPDCL Transactions:** Quick view of the latest verified payments.

2. **Dedicated Email Activity & Audit Section:**
   - Displays all detected emails with verification status:
     - `Verified`: Confirmed SBPDCL electricity receipts.
     - `Review Needed`: Uncertain biller / ambiguous receipts flagged for manual review.
     - `Rejected`: Non-SBPDCL transactions (e.g. mobile recharges, DTH, shopping).
   - View extracted details, raw snippets, and rejection reasons.
   - One-click **"Open in Gmail"** button directly opening the message in Google Inbox.
   - Review controls: **Verify as SBPDCL** or **Reject**.

3. **Complete Transactions Ledger:**
   - Full history of verified SBPDCL payments.
   - Live search by Transaction ID, UPI reference (UTR), or Consumer Number.
   - Month and Year dropdown filters.
   - Detailed transaction inspector modal.
   - **Export to CSV** functionality (`/api/transactions/export`).

4. **Reliable Dual-Layer Storage:**
   - Primary: **Supabase (PostgreSQL)** for cloud synchronization.
   - Local Fallback: **SQLite (`bijlitrack.db`)** ensuring zero data loss and uninterrupted operation when offline or if cloud projects are paused.

5. **Background Automation & Scheduling:**
   - Built-in FastAPI async background worker.
   - Configurable synchronization intervals (15 min, 30 min, 1 hr, 6 hr).
   - "Sync Now" button for instant on-demand scanning.
   - Idempotent upserts preventing duplicate transactions.

---

## 🏗️ Architecture & Technology Stack

```
   ┌─────────────────────────────────────────────────────────┐
   │             BijliTrack Frontend (React 19 + Vite)       │
   │   - Recharts (Monthly Bar & Area Charting)              │
   │   - Lucide React Icons & Dynamic Theme Engine           │
   └───────────────────────────┬─────────────────────────────┘
                               │ HTTP / REST API
                               ▼
   ┌─────────────────────────────────────────────────────────┐
   │               FastAPI Backend (Python 3.12)             │
   │  - [main.py] REST API & Lifespan Event Loop             │
   │  - [scheduler_service.py] Background Sync Worker        │
   │  - [automation_service.py] Regex Extraction & SBPDCL Ver│
   │  - [gmail_service.py] OAuth2 & Gmail API Client         │
   │  - [database_service.py] Supabase (Postgres) + SQLite   │
   └───────────────┬─────────────────────────┬───────────────┘
                   │                         │
                   ▼                         ▼
   ┌──────────────────────────────┐   ┌──────────────────────┐
   │       Google Gmail API       │   │  Supabase / SQLite   │
   │  - Scope: gmail.readonly     │   │  - recharge_         │
   │  - PhonePe SBPDCL receipts   │   │    transactions      │
   │                              │   │  - email_activities  │
   │                              │   │  - app_settings      │
   └──────────────────────────────┘   └──────────────────────┘
```

---

## 🚀 Quick Start with Streamlit (Unified App)

You can run BijliTrack as a single, full-featured Python Streamlit application with no separate node/frontend build required:

```bash
# Launch BijliTrack Streamlit App
backend\venv\Scripts\streamlit.exe run streamlit_app.py
```
This opens the BijliTrack dashboard at `http://localhost:8501` featuring:
- 📊 **Dashboard:** 4 live summary metric cards, interactive Plotly monthly bar chart, summary table, and date range filters (6m, 12m, current year, custom).
- 💳 **Transactions Ledger:** Complete searchable/filterable payment history, instant CSV export, and receipt detection tool.
- ✉️ **Email Activity:** Full audit trail for Gmail PhonePe receipts (Verified, Review Needed, Rejected), rejection reasons, and direct Gmail inbox links.
- ⚙️ **Settings:** One-click Gmail OAuth connection, default consumer CA number, sync interval, and database status.

---

## 🏗️ Alternative: React + FastAPI Setup

### 1. Backend Setup

```bash
cd backend

# Activate virtual environment
# Windows:
venv\Scripts\activate

# Run database schema migration in Supabase SQL editor (from database/schema.sql)
# or let the backend run with local SQLite automatically.

# Start FastAPI server
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Setup

```bash
cd frontend

# Install packages
npm install

# Start Vite dev server
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## 🔑 Gmail Integration Setup

1. Place your Google Cloud OAuth client credentials in `backend/credentials.json`.
2. Required OAuth scope: `https://www.googleapis.com/auth/gmail.readonly`.
3. To connect or re-authenticate your Gmail account, navigate to the **Settings** tab in the BijliTrack UI and click **Connect / Reconnect Gmail**.
4. The system scans messages newer than 2 years matching PhonePe SBPDCL electricity receipts.

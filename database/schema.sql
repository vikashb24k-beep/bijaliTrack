-- BijliTrack Database Schema (PostgreSQL / Supabase)
-- Exclusively designed for South Bihar Power Distribution Company Limited (SBPDCL) electricity bill payments

-- Main transactions table: verified SBPDCL electricity bill payments
create table if not exists public.recharge_transactions (
    id text primary key,
    transaction_id text unique,
    upi_ref_no text default '',
    transaction_date timestamptz not null,
    amount numeric(12,2) not null default 0,
    refund_amount numeric(12,2) default 0,
    payment_method text default 'PhonePe',
    status text default 'Success',
    biller_name text default 'South Bihar Power Distribution Company Limited (SBPDCL)',
    consumer_number text default '',
    is_sbpdcl boolean default true,
    verification_status text default 'verified',
    rejection_reason text default '',
    source text default 'Gmail',
    subject text default '',
    email_id text default '',
    snippet text default '',
    created_at timestamptz default now(),
    updated_at timestamptz default now()
);

-- Email activity table: all scanned Gmail emails for audit, review, and transparency
create table if not exists public.email_activities (
    id text primary key,
    email_id text unique not null,
    sender text default '',
    subject text default '',
    received_date timestamptz,
    extracted_amount numeric(12,2) default 0,
    detected_biller text default 'Unknown',
    consumer_number text default '',
    transaction_id text default '',
    upi_ref_no text default '',
    verification_status text default 'review', -- 'verified', 'review', 'rejected'
    rejection_reason text default '',
    snippet text default '',
    raw_payload text default '',
    created_at timestamptz default now()
);

-- Application settings table (key-value configuration)
create table if not exists public.app_settings (
    key text primary key,
    value text not null,
    updated_at timestamptz default now()
);

-- Performance indexes
create index if not exists idx_recharge_transactions_date
    on public.recharge_transactions (transaction_date desc);

create index if not exists idx_recharge_transactions_status
    on public.recharge_transactions (status);

create index if not exists idx_recharge_transactions_consumer
    on public.recharge_transactions (consumer_number);

create index if not exists idx_email_activities_status
    on public.email_activities (verification_status);

create index if not exists idx_email_activities_date
    on public.email_activities (received_date desc);

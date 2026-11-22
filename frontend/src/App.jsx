import { useEffect, useMemo, useState } from 'react'
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import {
  AlertCircle,
  ArrowDownRight,
  ArrowUpRight,
  CheckCircle2,
  ChevronRight,
  Download,
  ExternalLink,
  Eye,
  Filter,
  HelpCircle,
  LayoutDashboard,
  MailCheck,
  Moon,
  Plus,
  Power,
  RefreshCw,
  Search,
  Settings,
  SunMedium,
  Wallet,
  X,
  XCircle,
  Zap,
} from 'lucide-react'
import './App.css'

const API_BASE = 'http://localhost:8000'

const navItems = [
  { id: 'overview', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'transactions', label: 'Transactions', icon: Wallet },
  { id: 'emails', label: 'Email Activity', icon: MailCheck },
  { id: 'settings', label: 'Settings', icon: Settings },
]

const formatCurrency = (value) =>
  new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: 2,
  }).format(value || 0)

const formatDisplayDate = (value) => {
  if (!value) return 'Unknown date'
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) return value
  return parsed.toLocaleDateString('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  })
}

const formatDisplayDateTime = (value) => {
  if (!value) return 'Unknown'
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) return value
  return parsed.toLocaleString('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: true,
  })
}

function App() {
  const [activePage, setActivePage] = useState('overview')
  const [isDark, setIsDark] = useState(true)
  const [loading, setLoading] = useState(true)
  const [syncing, setSyncing] = useState(false)

  // Data states
  const [summaryData, setSummaryData] = useState({
    totalPaidAllTime: 0,
    totalThisMonth: 0,
    paymentsThisMonth: 0,
    lastPayment: null,
  })
  const [monthlySpending, setMonthlySpending] = useState([])
  const [transactions, setTransactions] = useState([])
  const [emailActivities, setEmailActivities] = useState([])
  const [appSettings, setAppSettings] = useState({})
  const [gmailStatus, setGmailStatus] = useState({})
  const [databaseStatus, setDatabaseStatus] = useState({})
  const [syncStatus, setSyncStatus] = useState({})
  const [isDemo, setIsDemo] = useState(false)

  // Filters
  const [dateRangeFilter, setDateRangeFilter] = useState('12m')
  const [customStartDate, setCustomStartDate] = useState('')
  const [customEndDate, setCustomEndDate] = useState('')
  const [searchTxn, setSearchTxn] = useState('')
  const [filterMonth, setFilterMonth] = useState('')
  const [filterYear, setFilterYear] = useState('')
  const [filterStatus, setFilterStatus] = useState('all')
  const [activityTab, setActivityTab] = useState('all')
  const [searchActivity, setSearchActivity] = useState('')

  // Modals
  const [selectedTxn, setSelectedTxn] = useState(null)
  const [selectedEmail, setSelectedEmail] = useState(null)
  const [showPasteModal, setShowPasteModal] = useState(false)
  const [pasteText, setPasteText] = useState('')
  const [pasteDate, setPasteDate] = useState('')
  const [pasteResultMsg, setPasteResultMsg] = useState('')

  // Settings form
  const [consumerNumberInput, setConsumerNumberInput] = useState('')
  const [syncIntervalInput, setSyncIntervalInput] = useState('30')
  const [autoSyncInput, setAutoSyncInput] = useState(true)
  const [settingsSavedMsg, setSettingsSavedMsg] = useState('')

  useEffect(() => {
    document.documentElement.dataset.theme = isDark ? 'dark' : 'light'
  }, [isDark])

  // Fetch Dashboard Summary
  const fetchDashboard = async (range = dateRangeFilter, start = customStartDate, end = customEndDate) => {
    try {
      let url = `${API_BASE}/api/dashboard/summary?range=${range}`
      if (range === 'custom') {
        if (start) url += `&start_date=${start}`
        if (end) url += `&end_date=${end}`
      }
      const res = await fetch(url)
      if (!res.ok) throw new Error('API error')
      const data = await res.json()
      setSummaryData(data.summary || {})
      setMonthlySpending(data.monthlySpending || [])
      setTransactions(data.transactions || [])
      setIsDemo(Boolean(data.is_demo))
      if (data.sync_status) setSyncStatus(data.sync_status)
    } catch (err) {
      console.error('Failed to load dashboard:', err)
    } finally {
      setLoading(false)
    }
  }

  // Fetch Transactions list
  const fetchTransactions = async () => {
    try {
      let url = `${API_BASE}/api/transactions?search=${encodeURIComponent(searchTxn)}`
      if (filterMonth) url += `&month=${filterMonth}`
      if (filterYear) url += `&year=${filterYear}`
      if (filterStatus && filterStatus !== 'all') url += `&status=${filterStatus}`
      const res = await fetch(url)
      if (!res.ok) throw new Error('API error')
      const data = await res.json()
      setTransactions(data.transactions || [])
      if (data.is_demo !== undefined) setIsDemo(data.is_demo)
    } catch (err) {
      console.error('Failed to load transactions:', err)
    }
  }

  // Fetch Email Activities
  const fetchEmailActivities = async () => {
    try {
      const url = `${API_BASE}/api/email-activity?status=${activityTab}&search=${encodeURIComponent(searchActivity)}`
      const res = await fetch(url)
      if (!res.ok) throw new Error('API error')
      const data = await res.json()
      setEmailActivities(data.activities || [])
    } catch (err) {
      console.error('Failed to load activities:', err)
    }
  }

  // Fetch Settings
  const fetchSettings = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/settings`)
      if (!res.ok) throw new Error('API error')
      const data = await res.json()
      setAppSettings(data.settings || {})
      setGmailStatus(data.gmail || {})
      setDatabaseStatus(data.database || {})
      setConsumerNumberInput(data.settings?.consumer_number || '')
      setSyncIntervalInput(data.settings?.sync_interval_minutes || '30')
      setAutoSyncInput(data.settings?.auto_sync_enabled !== 'false')
    } catch (err) {
      console.error('Failed to load settings:', err)
    }
  }

  useEffect(() => {
    fetchDashboard(dateRangeFilter, customStartDate, customEndDate)
    fetchSettings()
  }, [])

  useEffect(() => {
    if (activePage === 'overview') {
      fetchDashboard(dateRangeFilter, customStartDate, customEndDate)
    } else if (activePage === 'transactions') {
      fetchTransactions()
    } else if (activePage === 'emails') {
      fetchEmailActivities()
    } else if (activePage === 'settings') {
      fetchSettings()
    }
  }, [activePage, dateRangeFilter, customStartDate, customEndDate, searchTxn, filterMonth, filterYear, filterStatus, activityTab, searchActivity])

  // Handle Manual Sync
  const handleSyncNow = async () => {
    setSyncing(true)
    try {
      const res = await fetch(`${API_BASE}/api/sync/gmail`, { method: 'POST' })
      const result = await res.json()
      if (result.status === 'error') {
        alert(`Sync warning: ${result.message}`)
      }
      await fetchDashboard(dateRangeFilter, customStartDate, customEndDate)
      await fetchSettings()
    } catch (err) {
      console.error('Manual sync failed:', err)
    } finally {
      setSyncing(false)
    }
  }

  // Handle Verify / Reject for uncertain email
  const handleVerifyEmail = async (emailId) => {
    try {
      const res = await fetch(`${API_BASE}/api/email-activity/${emailId}/verify`, { method: 'POST' })
      if (!res.ok) throw new Error('Failed to verify')
      setSelectedEmail(null)
      fetchEmailActivities()
      fetchDashboard()
    } catch (err) {
      alert(`Error verifying: ${err.message}`)
    }
  }

  const handleRejectEmail = async (emailId) => {
    try {
      const res = await fetch(`${API_BASE}/api/email-activity/${emailId}/reject`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reason: 'Manually rejected by user' }),
      })
      if (!res.ok) throw new Error('Failed to reject')
      setSelectedEmail(null)
      fetchEmailActivities()
      fetchDashboard()
    } catch (err) {
      alert(`Error rejecting: ${err.message}`)
    }
  }

  // Save Settings
  const handleSaveSettings = async (e) => {
    e.preventDefault()
    try {
      const payload = {
        consumer_number: consumerNumberInput,
        sync_interval_minutes: syncIntervalInput,
        auto_sync_enabled: autoSyncInput ? 'true' : 'false',
      }
      const res = await fetch(`${API_BASE}/api/settings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      if (!res.ok) throw new Error('Failed to save settings')
      setSettingsSavedMsg('Preferences successfully updated!')
      setTimeout(() => setSettingsSavedMsg(''), 4000)
      fetchSettings()
    } catch (err) {
      alert(`Error saving settings: ${err.message}`)
    }
  }

  // Handle Parse / Paste Receipt Text
  const handleParsePaste = async (e) => {
    e.preventDefault()
    if (!pasteText.trim()) return
    try {
      const res = await fetch(`${API_BASE}/api/transactions/parse-text`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: pasteText, date: pasteDate || undefined }),
      })
      if (!res.ok) throw new Error('Parsing failed')
      const data = await res.json()
      setPasteResultMsg(`Detected ₹${data.parsed.amount} for ${data.parsed.detected_biller}!`)
      setTimeout(() => {
        setShowPasteModal(false)
        setPasteText('')
        setPasteDate('')
        setPasteResultMsg('')
        fetchTransactions()
        fetchDashboard()
        fetchEmailActivities()
      }, 1400)
    } catch (err) {
      alert(`Error parsing text: ${err.message}`)
    }
  }

  // Handle Connect Gmail
  const handleConnectGmail = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/auth/gmail/url`)
      if (!res.ok) throw new Error('Could not get auth URL')
      const data = await res.json()
      if (data.auth_url) {
        window.location.href = data.auth_url
      }
    } catch (err) {
      alert(`OAuth initialization error: ${err.message}`)
    }
  }

  // Current Date display
  const currentDate = useMemo(
    () =>
      new Date().toLocaleDateString('en-IN', {
        weekday: 'long',
        day: 'numeric',
        month: 'long',
        year: 'numeric',
      }),
    [],
  )

  const titleMap = {
    overview: 'Dashboard',
    transactions: 'Transaction History',
    emails: 'Email Activity',
    settings: 'Settings & Preferences',
  }

  // =========================================================================
  // VIEW: 1. DASHBOARD
  // =========================================================================
  const renderDashboard = () => (
    <>
      {isDemo && (
        <div className="demo-banner">
          <div className="demo-banner-content">
            <span className="demo-pill">Demo Mode</span>
            <span>
              You are currently viewing <strong>sample SBPDCL demo data</strong> (latest sample: 6 Nov) because your live Gmail account is not yet connected or its login token expired. Re-authenticate Gmail to load your <strong>current live bills</strong>.
            </span>
          </div>
          <button type="button" className="ghost-button" onClick={() => setActivePage('settings')}>
            <Settings size={14} /> Connect Gmail in Settings
          </button>
        </div>
      )}

      {/* Hero Panel */}
      <header className="hero-panel">
        <div>
          <div className="eyebrow">SBPDCL Electricity Bill Payment Tracker</div>
          <h1>Track your electricity recharge expenses automatically.</h1>
          <p>{currentDate}</p>
        </div>

        <div className="hero-actions">
          <button
            type="button"
            className="sync-button primary-button"
            onClick={handleSyncNow}
            disabled={syncing}
          >
            <Zap size={16} className={syncing ? 'animate-spin' : ''} />
            {syncing ? 'Scanning Gmail...' : 'Sync Now'}
          </button>
          <div className="sync-status">
            <span
              className="status-dot"
              style={{
                backgroundColor: gmailStatus?.connected ? '#22c55e' : '#f59e0b',
                boxShadow: gmailStatus?.connected ? '0 0 0 6px rgba(34, 197, 94, 0.15)' : '0 0 0 6px rgba(245, 158, 11, 0.15)',
              }}
            />
            <div>
              <strong>{gmailStatus?.connected ? 'Gmail Connected' : 'Gmail Reconnect Needed'}</strong>
              <small>
                {syncStatus?.last_sync_time
                  ? `Last synced ${formatDisplayDateTime(syncStatus.last_sync_time)}`
                  : 'Auto-sync active'}
              </small>
            </div>
          </div>
        </div>
      </header>

      {/* 4 Summary Cards */}
      <section className="stats-grid">
        <StatCard
          label="Total Electricity Bill Payments"
          value={formatCurrency(summaryData.totalPaidAllTime)}
          subtitle="All-time net successful SBPDCL payments"
          accent="electric"
        />
        <StatCard
          label="Total Paid This Month"
          value={formatCurrency(summaryData.totalThisMonth)}
          subtitle="Net recharge in current month"
          accent="green"
        />
        <StatCard
          label="Number of Payments This Month"
          value={`${summaryData.paymentsThisMonth} ${summaryData.paymentsThisMonth === 1 ? 'payment' : 'payments'}`}
          subtitle="Confirmed PhonePe transactions"
          accent="purple"
        />
        <StatCard
          label="Last Payment Amount & Date"
          value={summaryData.lastPayment ? formatCurrency(summaryData.lastPayment.amount) : '₹0.00'}
          subtitle={
            summaryData.lastPayment?.date
              ? `Paid on ${formatDisplayDate(summaryData.lastPayment.date)}`
              : 'No payment recorded'
          }
          accent="cyan"
        />
      </section>

      {/* Monthly Payment Summary (Chart + Table) */}
      <section className="panel" style={{ marginTop: '24px' }}>
        <div className="panel-header">
          <div>
            <p className="panel-label">Primary Feature</p>
            <h2>Monthly Payment Summary</h2>
          </div>

          <div className="segmented-control">
            <button
              type="button"
              className={dateRangeFilter === '6m' ? 'active' : ''}
              onClick={() => setDateRangeFilter('6m')}
            >
              Last 6 Months
            </button>
            <button
              type="button"
              className={dateRangeFilter === '12m' ? 'active' : ''}
              onClick={() => setDateRangeFilter('12m')}
            >
              Last 12 Months
            </button>
            <button
              type="button"
              className={dateRangeFilter === 'year' ? 'active' : ''}
              onClick={() => setDateRangeFilter('year')}
            >
              Current Year
            </button>
            <button
              type="button"
              className={dateRangeFilter === 'all' ? 'active' : ''}
              onClick={() => setDateRangeFilter('all')}
            >
              All Time
            </button>
            <button
              type="button"
              className={dateRangeFilter === 'custom' ? 'active' : ''}
              onClick={() => setDateRangeFilter('custom')}
            >
              Custom Range
            </button>
          </div>
        </div>

        {dateRangeFilter === 'custom' && (
          <div className="custom-range-row">
            <span>From:</span>
            <input
              type="date"
              value={customStartDate}
              onChange={(e) => setCustomStartDate(e.target.value)}
            />
            <span>To:</span>
            <input
              type="date"
              value={customEndDate}
              onChange={(e) => setCustomEndDate(e.target.value)}
            />
            <button
              type="button"
              className="primary-button"
              style={{ padding: '6px 12px', fontSize: '0.8rem' }}
              onClick={() => fetchDashboard('custom', customStartDate, customEndDate)}
            >
              Apply Filter
            </button>
          </div>
        )}

        <div className="monthly-container">
          {/* Chart */}
          <div className="chart-wrap">
            {monthlySpending.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={monthlySpending}>
                  <defs>
                    <linearGradient id="barGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#6366f1" stopOpacity={0.9} />
                      <stop offset="100%" stopColor="#3b82f6" stopOpacity={0.6} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid stroke="rgba(148,163,184,0.12)" vertical={false} />
                  <XAxis
                    dataKey="month"
                    tickLine={false}
                    axisLine={false}
                    tick={{ fill: '#94A3B8', fontSize: 12 }}
                  />
                  <YAxis
                    tickLine={false}
                    axisLine={false}
                    tick={{ fill: '#94A3B8', fontSize: 12 }}
                    tickFormatter={(value) => `₹${value}`}
                  />
                  <Tooltip
                    formatter={(val) => [formatCurrency(Number(val)), 'Total Paid']}
                    contentStyle={{
                      backgroundColor: '#111827',
                      borderColor: '#1e293b',
                      borderRadius: 12,
                      color: '#F8FAFC',
                    }}
                  />
                  <Bar dataKey="amount" radius={[8, 8, 0, 0]} fill="url(#barGradient)" />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="empty-state-cell">No payment records found for the selected range.</div>
            )}
          </div>

          {/* Table */}
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Month</th>
                  <th>Total Paid</th>
                  <th>Transactions</th>
                </tr>
              </thead>
              <tbody>
                {monthlySpending.length > 0 ? (
                  monthlySpending.map((row) => (
                    <tr key={row.monthKey}>
                      <td>
                        <strong>{row.month}</strong>
                      </td>
                      <td style={{ color: '#86efac', fontWeight: 600 }}>
                        {formatCurrency(row.amount)}
                      </td>
                      <td>
                        <span className="method-pill">{row.transactions} {row.transactions === 1 ? 'payment' : 'payments'}</span>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="3" className="empty-state-cell">
                      No monthly summary available.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* Recent Transactions List */}
      <section className="panel" style={{ marginTop: '24px' }}>
        <div className="panel-header">
          <div>
            <p className="panel-label">Recent SBPDCL Payments</p>
            <h2>Verified Electricity Transactions</h2>
          </div>
          <button type="button" className="text-button" onClick={() => setActivePage('transactions')}>
            View all payments <ChevronRight size={16} />
          </button>
        </div>

        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Date</th>
                <th>Amount</th>
                <th>Biller</th>
                <th>Transaction ID</th>
                <th>Status</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {transactions.slice(0, 6).map((item) => (
                <tr key={item.id}>
                  <td>{formatDisplayDate(item.transaction_date || item.date)}</td>
                  <td style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                    {formatCurrency(item.amount)}
                  </td>
                  <td>
                    <span style={{ fontSize: '0.85rem' }}>{item.biller_name || 'SBPDCL'}</span>
                  </td>
                  <td>
                    <code style={{ fontSize: '0.78rem' }}>{item.transaction_id || item.id}</code>
                  </td>
                  <td>
                    <span className={`status-badge ${String(item.status).toLowerCase()}`}>
                      {item.status}
                    </span>
                  </td>
                  <td>
                    <button
                      type="button"
                      className="ghost-button"
                      style={{ padding: '6px 10px', fontSize: '0.75rem' }}
                      onClick={() => setSelectedTxn(item)}
                    >
                      <Eye size={14} /> Details
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </>
  )

  // =========================================================================
  // VIEW: 2. TRANSACTIONS PAGE
  // =========================================================================
  const renderTransactionsPage = () => (
    <div className="page-panel">
      <div className="page-header">
        <div>
          <p className="panel-label">Payment Ledger</p>
          <h2>SBPDCL Electricity Bill Payment History</h2>
        </div>
        <div className="page-actions">
          <button
            type="button"
            className="primary-button"
            style={{ padding: '8px 14px', fontSize: '0.85rem' }}
            onClick={() => setShowPasteModal(true)}
          >
            <Plus size={16} /> Paste / Add Receipt
          </button>
          <a
            href={`${API_BASE}/api/transactions/export?search=${encodeURIComponent(searchTxn)}&month=${filterMonth}&year=${filterYear}&status=${filterStatus}`}
            className="ghost-button"
            download="sbpdcl_transactions.csv"
          >
            <Download size={16} /> Export CSV
          </a>
        </div>
      </div>

      {/* Filter Row */}
      <div className="filter-row">
        <div className="search-mini">
          <Search size={16} />
          <input
            type="text"
            placeholder="Search by Txn ID, Amount, UPI Ref, Consumer No..."
            value={searchTxn}
            onChange={(e) => setSearchTxn(e.target.value)}
          />
        </div>

        <select
          className="setting-select"
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
        >
          <option value="all">All Statuses</option>
          <option value="success">Success</option>
          <option value="refunded">Refunded</option>
          <option value="failed">Failed</option>
          <option value="pending">Pending</option>
        </select>

        <select
          className="setting-select"
          value={filterMonth}
          onChange={(e) => setFilterMonth(e.target.value)}
        >
          <option value="">All Months</option>
          <option value="1">January</option>
          <option value="2">February</option>
          <option value="3">March</option>
          <option value="4">April</option>
          <option value="5">May</option>
          <option value="6">June</option>
          <option value="7">July</option>
          <option value="8">August</option>
          <option value="9">September</option>
          <option value="10">October</option>
          <option value="11">November</option>
          <option value="12">December</option>
        </select>

        <select
          className="setting-select"
          value={filterYear}
          onChange={(e) => setFilterYear(e.target.value)}
        >
          <option value="">All Years</option>
          <option value="2026">2026</option>
          <option value="2025">2025</option>
          <option value="2024">2024</option>
        </select>

        {(searchTxn || filterMonth || filterYear || filterStatus !== 'all') && (
          <button
            type="button"
            className="ghost-button"
            onClick={() => {
              setSearchTxn('')
              setFilterMonth('')
              setFilterYear('')
              setFilterStatus('all')
            }}
          >
            Clear Filters
          </button>
        )}
      </div>

      <div style={{ margin: '8px 4px 14px', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
        Showing <strong>{transactions.length}</strong> {transactions.length === 1 ? 'transaction' : 'transactions'}
      </div>

      {/* Transactions Table */}
      <div className="table-wrap elevated-table">
        <table>
          <thead>
            <tr>
              <th>Date & Time</th>
              <th>Amount</th>
              <th>Biller</th>
              <th>Transaction ID</th>
              <th>Status</th>
              <th>Consumer No</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {transactions.length > 0 ? (
              transactions.map((item) => (
                <tr key={item.id}>
                  <td>{formatDisplayDateTime(item.transaction_date || item.date)}</td>
                  <td style={{ fontWeight: 700, color: 'var(--text-primary)' }}>
                    {formatCurrency(item.amount)}
                  </td>
                  <td>
                    <span style={{ fontSize: '0.85rem' }}>{item.biller_name || 'SBPDCL'}</span>
                  </td>
                  <td>
                    <code style={{ fontSize: '0.78rem' }}>{item.transaction_id || item.id}</code>
                  </td>
                  <td>
                    <span className={`status-badge ${String(item.status).toLowerCase()}`}>
                      {item.status}
                    </span>
                  </td>
                  <td>
                    <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                      {item.consumer_number || item.customer || '—'}
                    </span>
                  </td>
                  <td>
                    <button
                      type="button"
                      className="ghost-button"
                      style={{ padding: '6px 12px', fontSize: '0.78rem' }}
                      onClick={() => setSelectedTxn(item)}
                    >
                      <Eye size={14} /> Details
                    </button>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan="7" className="empty-state-cell">
                  No verified SBPDCL electricity transactions found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )

  // =========================================================================
  // VIEW: 3. EMAIL ACTIVITY PAGE
  // =========================================================================
  const renderEmailActivityPage = () => (
    <div className="page-panel">
      <div className="page-header">
        <div>
          <p className="panel-label">Audit & Verification</p>
          <h2>Gmail Detection & Extraction Activity</h2>
        </div>
        <div className="page-actions">
          <button
            type="button"
            className="ghost-button"
            onClick={() => setShowPasteModal(true)}
          >
            <Plus size={16} /> Paste / Test Receipt
          </button>
          <button
            type="button"
            className="primary-button"
            onClick={handleSyncNow}
            disabled={syncing}
          >
            <RefreshCw size={16} className={syncing ? 'animate-spin' : ''} />
            {syncing ? 'Scanning...' : 'Scan Gmail Now'}
          </button>
        </div>
      </div>

      <p style={{ color: 'var(--text-secondary)', marginBottom: '16px', fontSize: '0.9rem' }}>
        BijliTrack scans your Gmail inbox for PhonePe electricity payment receipts. Below is the complete record of processed messages.
      </p>

      {/* Tabs */}
      <div className="activity-tabs">
        <button
          type="button"
          className={`tab-btn ${activityTab === 'all' ? 'active' : ''}`}
          onClick={() => setActivityTab('all')}
        >
          All Detected Emails
        </button>
        <button
          type="button"
          className={`tab-btn ${activityTab === 'verified' ? 'active' : ''}`}
          onClick={() => setActivityTab('verified')}
        >
          Verified SBPDCL
        </button>
        <button
          type="button"
          className={`tab-btn ${activityTab === 'review' ? 'active' : ''}`}
          onClick={() => setActivityTab('review')}
        >
          Review Needed
        </button>
        <button
          type="button"
          className={`tab-btn ${activityTab === 'rejected' ? 'active' : ''}`}
          onClick={() => setActivityTab('rejected')}
        >
          Rejected (Non-SBPDCL)
        </button>
      </div>

      {/* Search */}
      <div className="filter-row">
        <div className="search-mini">
          <Search size={16} />
          <input
            type="text"
            placeholder="Search email subject, sender, or biller..."
            value={searchActivity}
            onChange={(e) => setSearchActivity(e.target.value)}
          />
        </div>
      </div>

      {/* Table */}
      <div className="table-wrap elevated-table">
        <table>
          <thead>
            <tr>
              <th>Received Date</th>
              <th>Email Subject</th>
              <th>Detected Biller</th>
              <th>Extracted Amount</th>
              <th>Verification Status</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {emailActivities.length > 0 ? (
              emailActivities.map((act) => (
                <tr key={act.id || act.email_id}>
                  <td>{formatDisplayDateTime(act.received_date || act.date)}</td>
                  <td style={{ maxWidth: '340px', color: 'var(--text-primary)' }}>
                    <div style={{ fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {act.subject || 'No subject'}
                    </div>
                    <small style={{ color: 'var(--text-secondary)' }}>{act.sender}</small>
                  </td>
                  <td>{act.detected_biller || 'Unknown'}</td>
                  <td style={{ fontWeight: 600 }}>{formatCurrency(act.extracted_amount || act.amount)}</td>
                  <td>
                    {act.verification_status === 'verified' && (
                      <span className="badge-verified">
                        <CheckCircle2 size={12} /> Verified
                      </span>
                    )}
                    {act.verification_status === 'review' && (
                      <span className="badge-review">
                        <HelpCircle size={12} /> Review Needed
                      </span>
                    )}
                    {act.verification_status === 'rejected' && (
                      <span className="badge-rejected">
                        <XCircle size={12} /> Rejected
                      </span>
                    )}
                  </td>
                  <td>
                    <button
                      type="button"
                      className="ghost-button"
                      style={{ padding: '6px 12px', fontSize: '0.78rem' }}
                      onClick={() => setSelectedEmail(act)}
                    >
                      Inspect
                    </button>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan="6" className="empty-state-cell">
                  No matching email activities found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )

  // =========================================================================
  // VIEW: 4. SETTINGS PAGE
  // =========================================================================
  const renderSettingsPage = () => (
    <div className="page-panel">
      <div className="page-header">
        <div>
          <p className="panel-label">Configuration</p>
          <h2>Preferences & Integration Settings</h2>
        </div>
      </div>

      <div className="settings-panel">
        {/* Gmail OAuth Card */}
        <div className="email-card">
          <div className="email-status-row">
            <div>
              <span className={`status-pill ${gmailStatus?.connected ? 'success' : 'failed'}`}>
                {gmailStatus?.connected ? 'Connected' : 'Action Required'}
              </span>
              <h3>Google Gmail Integration</h3>
            </div>
            <button
              type="button"
              className="primary-button"
              onClick={handleConnectGmail}
            >
              <Zap size={16} /> {gmailStatus?.connected ? 'Reconnect Gmail' : 'Connect Gmail Account'}
            </button>
          </div>
          <p style={{ marginTop: '10px' }}>
            BijliTrack connects securely via Google OAuth2 with read-only access (<code>gmail.readonly</code>).
            It only searches for PhonePe SBPDCL electricity receipts and never modifies or sends emails.
          </p>
          {gmailStatus?.error && (
            <p style={{ color: '#f87171', fontSize: '0.85rem' }}>
              Authentication note: {gmailStatus.error}
            </p>
          )}
        </div>

        {/* Preferences Form */}
        <form className="email-card" onSubmit={handleSaveSettings}>
          <h3>Tracking & Automation Preferences</h3>

          <div className="setting-form-group" style={{ marginTop: '12px' }}>
            <label className="detail-label">Default SBPDCL Consumer Number (CA No.)</label>
            <input
              type="text"
              className="setting-input"
              placeholder="e.g. 2341902819"
              value={consumerNumberInput}
              onChange={(e) => setConsumerNumberInput(e.target.value)}
            />
            <small style={{ color: 'var(--text-secondary)' }}>
              Used to associate payments and verify consumer accounts.
            </small>
          </div>

          <div className="setting-form-group" style={{ marginTop: '14px' }}>
            <label className="detail-label">Background Synchronization Interval</label>
            <select
              className="setting-select"
              value={syncIntervalInput}
              onChange={(e) => setSyncIntervalInput(e.target.value)}
            >
              <option value="15">Every 15 minutes</option>
              <option value="30">Every 30 minutes (Recommended)</option>
              <option value="60">Every 1 hour</option>
              <option value="360">Every 6 hours</option>
            </select>
          </div>

          <div style={{ marginTop: '14px', display: 'flex', alignItems: 'center', gap: '10px' }}>
            <input
              type="checkbox"
              id="autoSyncCheck"
              checked={autoSyncInput}
              onChange={(e) => setAutoSyncInput(e.target.checked)}
            />
            <label htmlFor="autoSyncCheck" style={{ cursor: 'pointer', fontSize: '0.9rem' }}>
              Enable automatic background synchronization worker
            </label>
          </div>

          <div style={{ marginTop: '18px', display: 'flex', alignItems: 'center', gap: '14px' }}>
            <button type="submit" className="primary-button">
              Save Preferences
            </button>
            {settingsSavedMsg && (
              <span style={{ color: '#86efac', fontSize: '0.88rem' }}>{settingsSavedMsg}</span>
            )}
          </div>
        </form>

        {/* Storage State Card */}
        <div className="email-card">
          <h3>Storage & Reliability Architecture</h3>
          <p style={{ marginTop: '6px' }}>
            <strong>Active Backend:</strong> {databaseStatus?.backend_storage || 'Local SQLite + Supabase Sync'}
          </p>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
            All detected transactions and email audit records are maintained safely with dual persistence. If the cloud database is paused or offline, BijliTrack continues tracking locally without interruption.
          </p>
        </div>

        {/* Theme Card */}
        <div className="setting-card">
          <div>
            <strong>Interface Theme</strong>
            <small style={{ display: 'block', color: 'var(--text-secondary)' }}>
              Currently set to {isDark ? 'Dark mode' : 'Light mode'}
            </small>
          </div>
          <button
            type="button"
            className="ghost-button"
            onClick={() => setIsDark((val) => !val)}
          >
            {isDark ? <SunMedium size={16} /> : <Moon size={16} />}
            {isDark ? 'Switch to Light mode' : 'Switch to Dark mode'}
          </button>
        </div>
      </div>
    </div>
  )

  return (
    <div className="app-shell">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="brand-row">
          <div className="brand-mark">
            <Power size={18} />
          </div>
          <div>
            <strong>BijliTrack</strong>
            <small>SBPDCL Payment Tracker</small>
          </div>
        </div>

        <nav className="nav-menu">
          {navItems.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              type="button"
              className={`nav-item ${activePage === id ? 'active' : ''}`}
              onClick={() => setActivePage(id)}
            >
              <Icon size={18} />
              <span>{label}</span>
            </button>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="profile-chip">
            <div className="avatar">SB</div>
            <div>
              <strong>SBPDCL</strong>
              <small>Bihar Electricity</small>
            </div>
          </div>

          <button
            type="button"
            className="theme-toggle"
            aria-label="Toggle theme"
            onClick={() => setIsDark((val) => !val)}
          >
            {isDark ? <SunMedium size={16} /> : <Moon size={16} />}
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="main-panel">
        <header className="topbar">
          <div className="topbar-left">
            <div className="breadcrumb">
              <span>BijliTrack</span>
              <ChevronRight size={16} />
              <strong>{titleMap[activePage] || 'Dashboard'}</strong>
            </div>
          </div>

          <div className="topbar-right">
            <div className="month-pill">
              <span>Utility</span>
              <strong>SBPDCL Bihar</strong>
            </div>

            <button
              type="button"
              className="sync-button primary-button"
              style={{ padding: '8px 14px', fontSize: '0.85rem' }}
              onClick={handleSyncNow}
              disabled={syncing}
            >
              <Zap size={14} className={syncing ? 'animate-spin' : ''} />
              {syncing ? 'Syncing...' : 'Sync Now'}
            </button>
          </div>
        </header>

        {activePage === 'overview' && renderDashboard()}
        {activePage === 'transactions' && renderTransactionsPage()}
        {activePage === 'emails' && renderEmailActivityPage()}
        {activePage === 'settings' && renderSettingsPage()}
      </main>

      {/* MODAL: Paste & Test Bill Receipt */}
      {showPasteModal && (
        <div className="modal-overlay" onClick={() => setShowPasteModal(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Paste & Detect Bill Receipt</h3>
              <button
                type="button"
                className="modal-close-btn"
                onClick={() => setShowPasteModal(false)}
              >
                <X size={20} />
              </button>
            </div>

            <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '14px' }}>
              Paste any PhonePe payment confirmation email, subject line, or SMS receipt. The system will automatically extract the payment amount, date, transaction ID, UTR, and consumer number.
            </p>

            <form onSubmit={handleParsePaste}>
              <div className="setting-form-group">
                <label className="detail-label">Receipt / Confirmation Text</label>
                <textarea
                  className="setting-input"
                  rows={5}
                  placeholder="e.g. Payment of Rs. 950 to South Bihar Power Distribution Company Limited (SBPDCL) is successful. Txn ID: T2611... Consumer No: 2341902819."
                  value={pasteText}
                  onChange={(e) => setPasteText(e.target.value)}
                  style={{ resize: 'vertical', fontFamily: 'inherit' }}
                  required
                />
              </div>

              <div className="setting-form-group" style={{ marginTop: '12px' }}>
                <label className="detail-label">Payment Date (Optional)</label>
                <input
                  type="date"
                  className="setting-input"
                  value={pasteDate}
                  onChange={(e) => setPasteDate(e.target.value)}
                />
              </div>

              {pasteResultMsg && (
                <div
                  style={{
                    marginTop: '14px',
                    padding: '10px 14px',
                    borderRadius: '10px',
                    background: 'rgba(34, 197, 94, 0.15)',
                    border: '1px solid rgba(34, 197, 94, 0.3)',
                    color: '#86efac',
                    fontSize: '0.88rem',
                  }}
                >
                  {pasteResultMsg}
                </div>
              )}

              <div className="modal-actions">
                <button
                  type="button"
                  className="ghost-button"
                  onClick={() => setShowPasteModal(false)}
                >
                  Cancel
                </button>
                <button type="submit" className="primary-button">
                  <CheckCircle2 size={16} /> Parse & Save Bill
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: Transaction Details */}
      {selectedTxn && (
        <div className="modal-overlay" onClick={() => setSelectedTxn(null)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>SBPDCL Payment Details</h3>
              <button
                type="button"
                className="modal-close-btn"
                onClick={() => setSelectedTxn(null)}
              >
                <X size={20} />
              </button>
            </div>

            <div className="detail-grid">
              <div className="detail-item">
                <span className="detail-label">Amount Paid</span>
                <span className="detail-value" style={{ color: '#86efac', fontSize: '1.3rem' }}>
                  {formatCurrency(selectedTxn.amount)}
                </span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Payment Status</span>
                <span className="detail-value">
                  <span className={`status-badge ${String(selectedTxn.status).toLowerCase()}`}>
                    {selectedTxn.status}
                  </span>
                </span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Payment Date & Time</span>
                <span className="detail-value">
                  {formatDisplayDateTime(selectedTxn.transaction_date || selectedTxn.date)}
                </span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Payment Method</span>
                <span className="detail-value">
                  {selectedTxn.payment_method || selectedTxn.method || 'PhonePe'}
                </span>
              </div>
              <div className="detail-item full-width">
                <span className="detail-label">Biller Name</span>
                <span className="detail-value">
                  {selectedTxn.biller_name || 'South Bihar Power Distribution Company Limited (SBPDCL)'}
                </span>
              </div>
              <div className="detail-item">
                <span className="detail-label">PhonePe Transaction ID</span>
                <span className="detail-value">
                  <code>{selectedTxn.transaction_id || selectedTxn.id}</code>
                </span>
              </div>
              <div className="detail-item">
                <span className="detail-label">UPI Reference (UTR)</span>
                <span className="detail-value">
                  <code>{selectedTxn.upi_ref_no || '—'}</code>
                </span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Consumer Number (CA No.)</span>
                <span className="detail-value">
                  {selectedTxn.consumer_number || selectedTxn.customer || '—'}
                </span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Source</span>
                <span className="detail-value">{selectedTxn.source || 'Gmail'}</span>
              </div>
              {selectedTxn.subject && (
                <div className="detail-item full-width">
                  <span className="detail-label">Email Subject</span>
                  <div className="raw-snippet">{selectedTxn.subject}</div>
                </div>
              )}
            </div>

            <div className="modal-actions">
              {selectedTxn.email_id && (
                <a
                  href={`https://mail.google.com/mail/u/0/#inbox/${selectedTxn.email_id}`}
                  target="_blank"
                  rel="noreferrer"
                  className="ghost-button subtle-link"
                >
                  <ExternalLink size={14} /> View in Gmail
                </a>
              )}
              <button
                type="button"
                className="primary-button"
                onClick={() => setSelectedTxn(null)}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* MODAL: Email Activity Inspection & Review */}
      {selectedEmail && (
        <div className="modal-overlay" onClick={() => setSelectedEmail(null)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Email Activity Details</h3>
              <button
                type="button"
                className="modal-close-btn"
                onClick={() => setSelectedEmail(null)}
              >
                <X size={20} />
              </button>
            </div>

            <div className="detail-grid">
              <div className="detail-item full-width">
                <span className="detail-label">Subject</span>
                <span className="detail-value">{selectedEmail.subject || 'No subject'}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Sender</span>
                <span className="detail-value">{selectedEmail.sender || 'Unknown'}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Received Date</span>
                <span className="detail-value">
                  {formatDisplayDateTime(selectedEmail.received_date || selectedEmail.date)}
                </span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Extracted Amount</span>
                <span className="detail-value" style={{ color: '#86efac', fontWeight: 700 }}>
                  {formatCurrency(selectedEmail.extracted_amount || selectedEmail.amount)}
                </span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Detected Biller</span>
                <span className="detail-value">{selectedEmail.detected_biller || 'Unknown'}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Verification Status</span>
                <span className="detail-value">
                  {selectedEmail.verification_status === 'verified' && (
                    <span className="badge-verified">Verified SBPDCL</span>
                  )}
                  {selectedEmail.verification_status === 'review' && (
                    <span className="badge-review">Review Needed</span>
                  )}
                  {selectedEmail.verification_status === 'rejected' && (
                    <span className="badge-rejected">Rejected</span>
                  )}
                </span>
              </div>
              <div className="detail-item">
                <span className="detail-label">PhonePe Txn ID</span>
                <span className="detail-value">
                  <code>{selectedEmail.transaction_id || '—'}</code>
                </span>
              </div>
              {selectedEmail.rejection_reason && (
                <div className="detail-item full-width">
                  <span className="detail-label">Processing / Rejection Reason</span>
                  <div
                    style={{
                      background: 'rgba(239, 68, 68, 0.1)',
                      border: '1px solid rgba(239, 68, 68, 0.3)',
                      color: '#fca5a5',
                      padding: '10px 14px',
                      borderRadius: '10px',
                      fontSize: '0.85rem',
                    }}
                  >
                    {selectedEmail.rejection_reason}
                  </div>
                </div>
              )}
              {selectedEmail.snippet && (
                <div className="detail-item full-width">
                  <span className="detail-label">Email Snippet Preview</span>
                  <div className="raw-snippet">{selectedEmail.snippet}</div>
                </div>
              )}
            </div>

            <div className="modal-actions">
              <a
                href={`https://mail.google.com/mail/u/0/#inbox/${selectedEmail.email_id || selectedEmail.id}`}
                target="_blank"
                rel="noreferrer"
                className="ghost-button subtle-link"
              >
                <ExternalLink size={14} /> Open in Gmail
              </a>

              {selectedEmail.verification_status === 'review' && (
                <>
                  <button
                    type="button"
                    className="ghost-button"
                    style={{ color: '#f87171' }}
                    onClick={() => handleRejectEmail(selectedEmail.email_id || selectedEmail.id)}
                  >
                    Reject Email
                  </button>
                  <button
                    type="button"
                    className="primary-button"
                    onClick={() => handleVerifyEmail(selectedEmail.email_id || selectedEmail.id)}
                  >
                    <CheckCircle2 size={16} /> Verify as SBPDCL
                  </button>
                </>
              )}

              <button
                type="button"
                className="primary-button"
                onClick={() => setSelectedEmail(null)}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function StatCard({ label, value, subtitle, accent }) {
  return (
    <article className={`stat-card ${accent}`}>
      <div className="stat-header">
        <span>{label}</span>
      </div>
      <div className="stat-value">{value}</div>
      {subtitle && (
        <div style={{ marginTop: '8px', fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
          {subtitle}
        </div>
      )}
    </article>
  )
}

export default App

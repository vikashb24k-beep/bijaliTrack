import { useEffect, useMemo, useState } from 'react'
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import {
  ArrowDownRight,
  ArrowUpRight,
  Bell,
  BarChart3,
  ChevronDown,
  ChevronRight,
  Download,
  Gauge,
  LayoutDashboard,
  MailCheck,
  Moon,
  Power,
  Search,
  Settings,
  SunMedium,
  TrendingUp,
  User,
  Wallet,
  Zap,
} from 'lucide-react'
import './App.css'

const navItems = [
  { id: 'overview', label: 'Overview', icon: LayoutDashboard },
  { id: 'transactions', label: 'Transactions', icon: Wallet },
  { id: 'monthly', label: 'Monthly Analytics', icon: BarChart3 },
  { id: 'yearly', label: 'Yearly Analytics', icon: TrendingUp },
  { id: 'consumption', label: 'Electricity Consumption', icon: Gauge },
  { id: 'emails', label: 'Email Automation', icon: MailCheck },
  { id: 'settings', label: 'Settings', icon: Settings },
]

const spendingData = [
  { month: 'Jan', amount: 2800 },
  { month: 'Feb', amount: 3400 },
  { month: 'Mar', amount: 3100 },
  { month: 'Apr', amount: 4200 },
  { month: 'May', amount: 3900 },
  { month: 'Jun', amount: 4700 },
  { month: 'Jul', amount: 5200 },
  { month: 'Aug', amount: 4950 },
  { month: 'Sep', amount: 4550 },
  { month: 'Oct', amount: 4300 },
  { month: 'Nov', amount: 5400 },
  { month: 'Dec', amount: 6100 },
]

const paymentMix = [
  { name: 'PhonePe', value: 44, color: '#6366F1' },
  { name: 'Google Pay', value: 31, color: '#3B82F6' },
  { name: 'Paytm', value: 18, color: '#22D3EE' },
  { name: 'Other', value: 7, color: '#F59E0B' },
]

const fallbackTransactions = [
  { date: '2026-11-06', method: 'PhonePe', id: 'TXN-54091', amount: 900, status: 'Success', source: 'Gmail', customer: '23XXXXXX9114' },
  { date: '2026-11-01', method: 'Google Pay', id: 'TXN-54010', amount: 1250, status: 'Success', source: 'Gmail', customer: '23XXXXXX9114' },
  { date: '2026-10-25', method: 'Paytm', id: 'TXN-53974', amount: 650, status: 'Pending', source: 'Manual', customer: '23XXXXXX9114' },
  { date: '2026-10-18', method: 'PhonePe', id: 'TXN-53912', amount: 1100, status: 'Failed', source: 'Gmail', customer: '23XXXXXX9114' },
  { date: '2026-10-11', method: 'PhonePe', id: 'TXN-53890', amount: 780, status: 'Refunded', source: 'Gmail', customer: '23XXXXXX9114' },
]

const fallbackInsights = [
  'Your recharge expenditure increased by 12% compared with last month.',
  'You made 4 successful recharges this month.',
  'Your average recharge amount is ₹875.00.',
  'The highest recharge spike came from PhonePe transactions.',
]

const formatCurrency = (value) =>
  new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: 2,
  }).format(value)

const formatCompactCurrency = (value) =>
  new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    notation: 'compact',
    maximumFractionDigits: 1,
  }).format(value)

function App() {
  const [activePage, setActivePage] = useState('overview')
  const [isDark, setIsDark] = useState(true)
  const [search, setSearch] = useState('')
  const [transactions, setTransactions] = useState(fallbackTransactions)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    document.documentElement.dataset.theme = isDark ? 'dark' : 'light'
  }, [isDark])

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/dashboard/summary')
        if (!response.ok) {
          throw new Error('Dashboard API unavailable')
        }

        const payload = await response.json()
        if (Array.isArray(payload.transactions) && payload.transactions.length > 0) {
          setTransactions(payload.transactions)
        }
      } catch (error) {
        setTransactions(fallbackTransactions)
      } finally {
        setLoading(false)
      }
    }

    fetchDashboard()
  }, [])

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
    overview: 'Overview',
    transactions: 'Transactions',
    monthly: 'Monthly Analytics',
    yearly: 'Yearly Analytics',
    consumption: 'Electricity Consumption',
    emails: 'Email Automation',
    settings: 'Settings',
  }

  const totalThisMonth = transactions.reduce((sum, item) => sum + Number(item.amount || 0), 0)
  const totalThisYear = totalThisMonth * 12
  const averageMonthly = totalThisMonth / Math.max(transactions.length, 1)
  const totalTransactions = transactions.length

  const filteredTransactions = transactions.filter((item) => {
    const query = search.toLowerCase()
    return (
      item.id.toLowerCase().includes(query) ||
      item.method.toLowerCase().includes(query) ||
      item.customer.toLowerCase().includes(query)
    )
  })

  const renderOverview = () => (
    <>
      <header className="hero-panel">
        <div>
          <div className="eyebrow">Good evening, welcome back!</div>
          <h1>Here is your electricity spending overview.</h1>
          <p>{currentDate}</p>
        </div>

        <div className="hero-actions">
          <button type="button" className="sync-button primary-button">
            <Zap size={16} /> Sync Now
          </button>
          <div className="sync-status">
            <span className="status-dot" />
            <div>
              <strong>Synced</strong>
              <small>Last successful sync 12 min ago</small>
            </div>
          </div>
        </div>
      </header>

      <section className="stats-grid">
        <StatCard
          label="Total Recharged This Month"
          value={formatCurrency(totalThisMonth)}
          delta="+12.4%"
          deltaType="up"
          accent="electric"
        />
        <StatCard
          label="Total Recharged This Year"
          value={formatCurrency(totalThisYear)}
          delta="+18.8%"
          deltaType="up"
          accent="green"
        />
        <StatCard
          label="Average Monthly Spending"
          value={formatCurrency(averageMonthly)}
          delta="+2.1%"
          deltaType="up"
          accent="purple"
        />
        <StatCard
          label="Total Recharge Transactions"
          value={String(totalTransactions)}
          delta="+4 this month"
          deltaType="up"
          accent="cyan"
        />
      </section>

      <section className="chart-grid">
        <div className="panel spending-panel">
          <div className="panel-header">
            <div>
              <p className="panel-label">Overview</p>
              <h2>Electricity Spending</h2>
            </div>
            <div className="segmented-control">
              <button type="button" className="active">6M</button>
              <button type="button">12M</button>
            </div>
          </div>

          <div className="chart-wrap">
            <ResponsiveContainer width="100%" height={280}>
              <AreaChart data={spendingData}>
                <defs>
                  <linearGradient id="spendGradient" x1="0" x2="0" y1="0" y2="1">
                    <stop offset="0%" stopColor="#3B82F6" stopOpacity={0.6} />
                    <stop offset="100%" stopColor="#3B82F6" stopOpacity={0.04} />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="rgba(148,163,184,0.14)" vertical={false} />
                <XAxis dataKey="month" tickLine={false} axisLine={false} tick={{ fill: '#94A3B8', fontSize: 12 }} />
                <YAxis tickLine={false} axisLine={false} tick={{ fill: '#94A3B8', fontSize: 12 }} tickFormatter={(value) => `₹${value / 1000}k`} />
                <Tooltip
                  formatter={(value) => [formatCurrency(Number(value)), 'Spent']}
                  contentStyle={{
                    backgroundColor: '#111827',
                    border: '1px solid rgba(148,163,184,0.2)',
                    borderRadius: '12px',
                    color: '#F8FAFC',
                  }}
                />
                <Area type="monotone" dataKey="amount" stroke="#60A5FA" strokeWidth={3} fill="url(#spendGradient)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="panel donut-panel">
          <div className="panel-header compact-header">
            <div>
              <p className="panel-label">Breakdown</p>
              <h2>Spending Mix</h2>
            </div>
          </div>

          <div className="donut-wrap">
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie data={paymentMix} innerRadius={52} outerRadius={82} paddingAngle={4} dataKey="value">
                  {paymentMix.map((entry) => (
                    <Cell key={entry.name} fill={entry.color} />
                  ))}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="legend-list">
            {paymentMix.map((item) => (
              <div key={item.name} className="legend-item">
                <span className="dot" style={{ background: item.color }} />
                <span>{item.name}</span>
                <strong>{item.value}%</strong>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="bottom-grid">
        <div className="panel transaction-panel">
          <div className="panel-header">
            <div>
              <p className="panel-label">Recent</p>
              <h2>Recent Transactions</h2>
            </div>
            <button type="button" className="text-button">
              View all <ChevronRight size={16} />
            </button>
          </div>

          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Payment method</th>
                  <th>Transaction ID</th>
                  <th>Amount</th>
                  <th>Status</th>
                  <th>Source</th>
                </tr>
              </thead>
              <tbody>
                {transactions.slice(0, 5).map((item) => (
                  <tr key={item.id}>
                    <td>{item.date}</td>
                    <td>
                      <span className="method-pill">{item.method}</span>
                    </td>
                    <td>{item.id}</td>
                    <td>{formatCurrency(Number(item.amount || 0))}</td>
                    <td>
                      <span className={`status-badge ${String(item.status || '').toLowerCase()}`}>{item.status}</span>
                    </td>
                    <td>{item.source}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="panel insight-panel">
          <div className="panel-header compact-header">
            <div>
              <p className="panel-label">Insights</p>
              <h2>Quick Insights</h2>
            </div>
          </div>

          <div className="insight-list">
            {(fallbackInsights || []).map((item, index) => (
              <div key={item} className="insight-item">
                <span className="insight-index">0{index + 1}</span>
                <p>{item}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </>
  )

  const renderTransactions = () => (
    <div className="page-panel">
      <div className="page-header">
        <div>
          <p className="panel-label">Transactions</p>
          <h2>Recharge history and payment records</h2>
        </div>
        <div className="page-actions">
          <button type="button" className="ghost-button">
            <Download size={16} /> Export CSV
          </button>
        </div>
      </div>

      <div className="filter-row">
        <div className="search-mini">
          <Search size={16} />
          <input
            type="text"
            placeholder="Search by transaction ID or wallet"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
        </div>
        <button type="button" className="ghost-button">
          <ChevronDown size={16} /> Date filter
        </button>
        <button type="button" className="ghost-button">
          <ChevronDown size={16} /> Payment method
        </button>
      </div>

      <div className="table-wrap elevated-table">
        <table>
          <thead>
            <tr>
              <th>Date</th>
              <th>Payment method</th>
              <th>Transaction ID</th>
              <th>Amount</th>
              <th>Status</th>
              <th>Source</th>
            </tr>
          </thead>
          <tbody>
            {filteredTransactions.length > 0 ? (
              filteredTransactions.map((item) => (
                <tr key={item.id}>
                  <td>{item.date}</td>
                  <td><span className="method-pill">{item.method}</span></td>
                  <td>{item.id}</td>
                  <td>{formatCurrency(item.amount)}</td>
                  <td><span className={`status-badge ${item.status.toLowerCase()}`}>{item.status}</span></td>
                  <td>{item.source}</td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan="6" className="empty-state-cell">No matching transactions for your current filter.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )

  const renderMonthly = () => (
    <div className="page-panel">
      <div className="page-header">
        <div>
          <p className="panel-label">Monthly</p>
          <h2>Recharge performance by month</h2>
        </div>
      </div>

      <div className="panel chart-only-panel">
        <ResponsiveContainer width="100%" height={340}>
          <BarChart data={spendingData}>
            <CartesianGrid stroke="rgba(148,163,184,0.12)" vertical={false} />
            <XAxis dataKey="month" tickLine={false} axisLine={false} tick={{ fill: '#94A3B8', fontSize: 12 }} />
            <YAxis tickLine={false} axisLine={false} tick={{ fill: '#94A3B8', fontSize: 12 }} tickFormatter={(value) => `₹${value / 1000}k`} />
            <Tooltip formatter={(value) => [formatCurrency(Number(value)), 'Revenue']} contentStyle={{ backgroundColor: '#111827', borderColor: '#1e293b', borderRadius: 12 }} />
            <Bar dataKey="amount" radius={[10, 10, 0, 0]} fill="#6366F1" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )

  const renderYearly = () => (
    <div className="page-panel">
      <div className="page-header">
        <div>
          <p className="panel-label">Yearly</p>
          <h2>Annual spending summary</h2>
        </div>
      </div>

      <div className="stats-grid compact">
        <StatCard label="Annual Recharge" value={formatCurrency(totalThisYear)} delta="+20.6%" deltaType="up" accent="electric" />
        <StatCard label="Annual Avg. Recharge" value={formatCurrency(totalThisYear / 12)} delta="+9.3%" deltaType="up" accent="purple" />
        <StatCard label="Highest Month" value="₹6,100" delta="December" deltaType="up" accent="green" />
      </div>
    </div>
  )

  const pageContent = {
    overview: renderOverview(),
    transactions: renderTransactions(),
    monthly: renderMonthly(),
    yearly: renderYearly(),
    consumption: (
      <div className="page-panel">
        <div className="page-header">
          <div>
            <p className="panel-label">Consumption</p>
            <h2>Smart meter usage and remaining balance</h2>
          </div>
        </div>
        <div className="stats-grid compact">
          <StatCard label="Units Consumed" value="342 kWh" delta="+14% vs last month" deltaType="up" accent="electric" />
          <StatCard label="Meter Balance" value="₹2,460.50" delta="Healthy" deltaType="up" accent="green" />
          <StatCard label="Average Daily Usage" value="11.4 kWh" delta="Stable" deltaType="up" accent="cyan" />
        </div>
      </div>
    ),
    emails: (
      <div className="page-panel">
        <div className="page-header">
          <div>
            <p className="panel-label">Automation</p>
            <h2>Gmail email synchronization status</h2>
          </div>
        </div>
        <div className="email-card">
          <div className="email-status-row">
            <div>
              <span className="status-pill success">Connected</span>
              <h3>Gmail OAuth is active</h3>
            </div>
            <button type="button" className="primary-button">Reconnect Gmail</button>
          </div>
          <p>BijliTrack scans email for SBPDCL, Bihar Bijli, payment confirmations, and recharge receipts without modifying messages or sending email.</p>
        </div>
      </div>
    ),
    settings: (
      <div className="page-panel">
        <div className="page-header">
          <div>
            <p className="panel-label">Settings</p>
            <h2>Personalization and account preferences</h2>
          </div>
        </div>
        <div className="settings-panel">
          <div className="setting-card">
            <span>Theme</span>
            <button type="button" className="ghost-button" onClick={() => setIsDark((value) => !value)}>
              {isDark ? <SunMedium size={16} /> : <Moon size={16} />} {isDark ? 'Light mode' : 'Dark mode'}
            </button>
          </div>
          <div className="setting-card">
            <span>Sync preferences</span>
            <button type="button" className="ghost-button">Manage Gmail sync</button>
          </div>
        </div>
      </div>
    ),
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-row">
          <div className="brand-mark">
            <Power size={18} />
          </div>
          <div>
            <strong>BijliTrack</strong>
            <small>Smart meter finance</small>
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
            <div className="avatar">
              <User size={16} />
            </div>
            <div>
              <strong>Harsh</strong>
              <small>Premium</small>
            </div>
          </div>

          <button type="button" className="theme-toggle" onClick={() => setIsDark((value) => !value)}>
            {isDark ? <SunMedium size={16} /> : <Moon size={16} />}
          </button>
        </div>
      </aside>

      <main className="main-panel">
        <header className="topbar">
          <div className="topbar-left">
            <div className="breadcrumb">
              <span>Dashboard</span>
              <ChevronRight size={16} />
              <strong>{titleMap[activePage]}</strong>
            </div>
          </div>

          <div className="topbar-right">
            <div className="month-pill">
              <span>Current month</span>
              <strong>November</strong>
            </div>

            <div className="search-box">
              <Search size={16} />
              <input type="text" placeholder="Search transactions" value={search} onChange={(event) => setSearch(event.target.value)} />
            </div>

            <button type="button" className="icon-button" aria-label="Notifications">
              <Bell size={16} />
            </button>

            <div className="profile-mini">
              <div className="mini-avatar">H</div>
            </div>
          </div>
        </header>

        {pageContent}
      </main>
    </div>
  )
}

function StatCard({ label, value, delta, deltaType, accent }) {
  return (
    <article className={`stat-card ${accent}`}>
      <div className="stat-header">
        <span>{label}</span>
        <span className={`trend ${deltaType}`}>
          {deltaType === 'up' ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
          {delta}
        </span>
      </div>
      <div className="stat-value">{value}</div>
    </article>
  )
}

export default App

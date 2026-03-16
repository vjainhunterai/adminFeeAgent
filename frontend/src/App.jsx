import React from 'react'
import { Routes, Route, Link, useLocation } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import NewContracts from './pages/NewContracts'
import ContractAnalysis from './pages/ContractAnalysis'
import StatusMonitor from './pages/StatusMonitor'

function App() {
  const location = useLocation()

  const navItems = [
    { path: '/', label: 'Dashboard' },
    { path: '/new-contracts', label: 'Process New' },
    { path: '/analysis', label: 'Analyze Existing' },
    { path: '/status', label: 'Status Monitor' },
  ]

  return (
    <div className="app">
      <header className="header">
        <div className="header-inner">
          <h1 className="logo">hunterAI <span>AdminFee</span></h1>
          <nav className="nav">
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={`nav-link ${location.pathname === item.path ? 'active' : ''}`}
              >
                {item.label}
              </Link>
            ))}
          </nav>
        </div>
      </header>
      <main className="main">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/new-contracts" element={<NewContracts />} />
          <Route path="/analysis" element={<ContractAnalysis />} />
          <Route path="/status" element={<StatusMonitor />} />
        </Routes>
      </main>
    </div>
  )
}

export default App

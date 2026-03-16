import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { healthCheck } from '../api'

function Dashboard() {
  const [apiStatus, setApiStatus] = useState('checking')

  useEffect(() => {
    healthCheck()
      .then(() => setApiStatus('connected'))
      .catch(() => setApiStatus('disconnected'))
  }, [])

  return (
    <div className="page">
      <div className="page-header">
        <h2>Welcome to AdminFee Automation</h2>
        <p>Select a workflow to get started</p>
      </div>

      <div className="status-badge-row">
        <span className={`status-badge ${apiStatus}`}>
          API: {apiStatus}
        </span>
      </div>

      <div className="card-grid">
        <Link to="/new-contracts" className="card card-link">
          <div className="card-icon">+</div>
          <h3>Process NEW Contracts</h3>
          <p>
            Enter contracts manually or upload an Excel file.
            Triggers the Airflow pipeline and monitors until completion.
          </p>
        </Link>

        <Link to="/analysis" className="card card-link">
          <div className="card-icon">?</div>
          <h3>Analyze EXISTING Contracts</h3>
          <p>
            Ask natural-language questions about processed contracts.
            AI generates SQL, queries the database, and explains results.
          </p>
        </Link>

        <Link to="/status" className="card card-link">
          <div className="card-icon">~</div>
          <h3>Status Monitor</h3>
          <p>
            Check real-time processing status and ask AI-powered
            questions about contract progress.
          </p>
        </Link>
      </div>
    </div>
  )
}

export default Dashboard

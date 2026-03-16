import React, { useState } from 'react'
import { startProcessing, getContractSummary } from '../api'

function NewContracts() {
  const [inputType, setInputType] = useState('manual')
  const [contracts, setContracts] = useState('')
  const [deliveryName, setDeliveryName] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [summaryResult, setSummaryResult] = useState(null)
  const [summaryLoading, setSummaryLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    setResult(null)
    try {
      const data = await startProcessing({
        input_type: inputType,
        contracts,
        delivery_name: deliveryName,
      })
      setResult(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleSummary = async () => {
    if (!result?.contracts) return
    setSummaryLoading(true)
    try {
      const data = await getContractSummary(result.contracts)
      setSummaryResult(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setSummaryLoading(false)
    }
  }

  return (
    <div className="page">
      <div className="page-header">
        <h2>Process NEW Contracts</h2>
        <p>Enter contract details to start the AdminFee processing pipeline</p>
      </div>

      <form className="card form-card" onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Input Method</label>
          <div className="radio-group">
            <label className={`radio-label ${inputType === 'manual' ? 'selected' : ''}`}>
              <input
                type="radio"
                value="manual"
                checked={inputType === 'manual'}
                onChange={(e) => setInputType(e.target.value)}
              />
              Manual Entry
            </label>
            <label className={`radio-label ${inputType === 'file' ? 'selected' : ''}`}>
              <input
                type="radio"
                value="file"
                checked={inputType === 'file'}
                onChange={(e) => setInputType(e.target.value)}
              />
              Excel File
            </label>
          </div>
        </div>

        {inputType === 'manual' ? (
          <div className="form-group">
            <label>Contract Names (comma-separated)</label>
            <textarea
              value={contracts}
              onChange={(e) => setContracts(e.target.value)}
              placeholder="PP-OR-123, PP-NS-345"
              rows={3}
              required
            />
          </div>
        ) : (
          <div className="form-group">
            <div className="info-box">
              Place your <strong>contracts.xlsx</strong> file at:
              <code>/home/ubuntu/adminfee_data_pipeline/Data/agent_input/contracts.xlsx</code>
              <br />Column name should be: <strong>contract_name</strong>
            </div>
          </div>
        )}

        <div className="form-group">
          <label>Delivery Name</label>
          <input
            type="text"
            value={deliveryName}
            onChange={(e) => setDeliveryName(e.target.value)}
            placeholder="Delivery_9"
            required
          />
        </div>

        <button type="submit" className="btn btn-primary" disabled={loading}>
          {loading ? 'Processing...' : 'Start Processing'}
        </button>
      </form>

      {error && <div className="card error-card">{error}</div>}

      {result && (
        <div className="card result-card">
          <h3>Processing Started</h3>
          <div className="result-details">
            <div className="detail-row">
              <span className="detail-label">Contracts:</span>
              <span>{result.contracts?.join(', ')}</span>
            </div>
            <div className="detail-row">
              <span className="detail-label">Delivery:</span>
              <span>{result.delivery_name}</span>
            </div>
            <div className="detail-row">
              <span className="detail-label">Pipeline Status:</span>
              <span className={`badge ${result.pipeline?.status === 'TRIGGERED' ? 'badge-success' : 'badge-error'}`}>
                {result.pipeline?.status}
              </span>
            </div>
          </div>

          <button className="btn btn-secondary" onClick={handleSummary} disabled={summaryLoading}>
            {summaryLoading ? 'Generating Summary...' : 'Generate Summary Report'}
          </button>
        </div>
      )}

      {summaryResult && (
        <div className="card">
          <h3>Contract Summary Report</h3>
          <div className="summary-report">{summaryResult.report}</div>
          <table className="data-table">
            <thead>
              <tr>
                <th>Contract</th>
                <th>PO Spend</th>
                <th>INV Spend</th>
                <th>Report Spend</th>
                <th>Difference</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {summaryResult.summary?.map((row, i) => (
                <tr key={i}>
                  <td>{row.contract}</td>
                  <td>{row.po_spend?.toLocaleString() ?? 'N/A'}</td>
                  <td>{row.inv_spend?.toLocaleString() ?? 'N/A'}</td>
                  <td>{row.report_spend?.toLocaleString() ?? 'N/A'}</td>
                  <td>{row.difference?.toLocaleString() ?? 'N/A'}</td>
                  <td><span className="badge">{row.status}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

export default NewContracts

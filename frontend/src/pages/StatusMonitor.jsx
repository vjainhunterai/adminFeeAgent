import React, { useState, useEffect, useRef } from 'react'
import { getStatus, askStatusQuestion } from '../api'
import ChatMessage from '../components/ChatMessage'

function StatusMonitor() {
  const [status, setStatus] = useState(null)
  const [loading, setLoading] = useState(true)
  const [autoRefresh, setAutoRefresh] = useState(false)
  const [deliveryName, setDeliveryName] = useState('')
  const [question, setQuestion] = useState('')
  const [messages, setMessages] = useState([])
  const [asking, setAsking] = useState(false)
  const intervalRef = useRef(null)

  const fetchStatus = async () => {
    try {
      const data = await getStatus()
      setStatus(data)
    } catch {
      setStatus(null)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchStatus()
  }, [])

  useEffect(() => {
    if (autoRefresh) {
      intervalRef.current = setInterval(fetchStatus, 60000)
    }
    return () => clearInterval(intervalRef.current)
  }, [autoRefresh])

  const handleAsk = async (e) => {
    e.preventDefault()
    if (!question.trim() || !deliveryName.trim()) return
    const q = question.trim()
    setQuestion('')
    setAsking(true)
    setMessages((prev) => [...prev, { role: 'user', text: q }])
    try {
      const data = await askStatusQuestion({
        question: q,
        delivery_name: deliveryName,
      })
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', text: data.answer, sql: data.sql },
      ])
    } catch (err) {
      setMessages((prev) => [...prev, { role: 'error', text: err.message }])
    } finally {
      setAsking(false)
    }
  }

  return (
    <div className="page">
      <div className="page-header">
        <h2>Status Monitor</h2>
        <p>Real-time processing status with AI-powered Q&A</p>
      </div>

      <div className="card">
        <div className="status-grid">
          <div className="status-item">
            <span className="status-number">{status?.total ?? '-'}</span>
            <span className="status-label">Total</span>
          </div>
          <div className="status-item completed">
            <span className="status-number">{status?.completed ?? '-'}</span>
            <span className="status-label">Completed</span>
          </div>
          <div className="status-item in-progress">
            <span className="status-number">{status?.in_progress ?? '-'}</span>
            <span className="status-label">In Progress</span>
          </div>
        </div>

        {status?.is_completed && (
          <div className="info-box success">All contracts completed!</div>
        )}

        <div className="status-actions">
          <button className="btn btn-secondary" onClick={fetchStatus} disabled={loading}>
            {loading ? 'Refreshing...' : 'Refresh Now'}
          </button>
          <label className="toggle-label">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
            />
            Auto-refresh (60s)
          </label>
        </div>
      </div>

      <div className="card">
        <h3>Ask About Status</h3>
        <div className="form-group">
          <label>Delivery Name</label>
          <input
            type="text"
            value={deliveryName}
            onChange={(e) => setDeliveryName(e.target.value)}
            placeholder="Delivery_9"
          />
        </div>

        <div className="chat-messages compact">
          {messages.map((msg, i) => (
            <ChatMessage key={i} message={msg} />
          ))}
          {asking && (
            <div className="chat-msg system"><div className="msg-bubble">Thinking...</div></div>
          )}
        </div>

        <form className="chat-input-row" onSubmit={handleAsk}>
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="e.g. How many contracts are completed?"
            disabled={asking}
          />
          <button type="submit" className="btn btn-primary" disabled={asking || !question.trim() || !deliveryName.trim()}>
            Ask
          </button>
        </form>
      </div>
    </div>
  )
}

export default StatusMonitor

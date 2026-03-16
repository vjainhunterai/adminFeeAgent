import React, { useState } from 'react'
import { fetchDeliveryContracts, askAnalysisQuestion } from '../api'
import ChatMessage from '../components/ChatMessage'

function ContractAnalysis() {
  const [deliveryInput, setDeliveryInput] = useState('')
  const [delivery, setDelivery] = useState('')
  const [contracts, setContracts] = useState([])
  const [connected, setConnected] = useState(false)
  const [loading, setLoading] = useState(false)
  const [question, setQuestion] = useState('')
  const [messages, setMessages] = useState([])
  const [asking, setAsking] = useState(false)
  const [error, setError] = useState('')

  const handleConnect = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      const data = await fetchDeliveryContracts(deliveryInput)
      setDelivery(data.delivery)
      setContracts(data.contracts)
      setConnected(true)
      setMessages([{
        role: 'system',
        text: `Connected to delivery: ${data.delivery}\nContracts found: ${data.contracts.join(', ') || 'None'}`
      }])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleAsk = async (e) => {
    e.preventDefault()
    if (!question.trim()) return
    const q = question.trim()
    setQuestion('')
    setAsking(true)
    setMessages((prev) => [...prev, { role: 'user', text: q }])

    try {
      const data = await askAnalysisQuestion(q, contracts)
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', text: data.answer, sql: data.sql },
      ])
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: 'error', text: err.message },
      ])
    } finally {
      setAsking(false)
    }
  }

  return (
    <div className="page">
      <div className="page-header">
        <h2>Contract Analysis</h2>
        <p>Ask natural-language questions about existing contracts</p>
      </div>

      {!connected ? (
        <form className="card form-card" onSubmit={handleConnect}>
          <div className="form-group">
            <label>Delivery Name</label>
            <input
              type="text"
              value={deliveryInput}
              onChange={(e) => setDeliveryInput(e.target.value)}
              placeholder="Delivery 9"
              required
            />
          </div>
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? 'Connecting...' : 'Connect'}
          </button>
          {error && <div className="error-text">{error}</div>}
        </form>
      ) : (
        <div className="chat-container">
          <div className="chat-header">
            <span>Delivery: <strong>{delivery}</strong></span>
            <span>Contracts: <strong>{contracts.length}</strong></span>
            <button className="btn btn-sm" onClick={() => { setConnected(false); setMessages([]) }}>
              Change Delivery
            </button>
          </div>

          <div className="chat-messages">
            {messages.map((msg, i) => (
              <ChatMessage key={i} message={msg} />
            ))}
            {asking && (
              <div className="chat-msg system">
                <div className="msg-bubble">Analyzing...</div>
              </div>
            )}
          </div>

          <form className="chat-input-row" onSubmit={handleAsk}>
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Ask a question about your contracts..."
              disabled={asking}
            />
            <button type="submit" className="btn btn-primary" disabled={asking || !question.trim()}>
              Send
            </button>
          </form>
        </div>
      )}
    </div>
  )
}

export default ContractAnalysis

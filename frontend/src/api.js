const BASE = '/api'

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'Request failed')
  }
  return res.json()
}

// Health
export const healthCheck = () => request('/health')

// Processing (Phase 1)
export const startProcessing = (data) =>
  request('/processing/start', { method: 'POST', body: JSON.stringify(data) })

export const getStatus = () => request('/processing/status')

export const askStatusQuestion = (data) =>
  request('/processing/status/ask', { method: 'POST', body: JSON.stringify(data) })

export const getContractSummary = (contracts) =>
  request('/processing/summary', { method: 'POST', body: JSON.stringify({ contracts }) })

// Analysis (Phase 2)
export const fetchDeliveryContracts = (delivery_name) =>
  request('/analysis/delivery', { method: 'POST', body: JSON.stringify({ delivery_name }) })

export const askAnalysisQuestion = (question, contracts) =>
  request('/analysis/ask', { method: 'POST', body: JSON.stringify({ question, contracts }) })

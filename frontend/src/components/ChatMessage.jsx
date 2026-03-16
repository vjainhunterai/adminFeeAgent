import React, { useState } from 'react'

function ChatMessage({ message }) {
  const [showSql, setShowSql] = useState(false)
  const { role, text, sql } = message

  return (
    <div className={`chat-msg ${role}`}>
      <div className="msg-label">
        {role === 'user' ? 'You' : role === 'error' ? 'Error' : role === 'system' ? 'System' : 'AI Agent'}
      </div>
      <div className="msg-bubble">
        <div className="msg-text">{text}</div>
        {sql && (
          <div className="msg-sql">
            <button className="sql-toggle" onClick={() => setShowSql(!showSql)}>
              {showSql ? 'Hide SQL' : 'Show SQL'}
            </button>
            {showSql && <pre className="sql-block">{sql}</pre>}
          </div>
        )}
      </div>
    </div>
  )
}

export default ChatMessage

import React from 'react'

export default function MetricsPanel({ metrics = {} }) {
  const entries = Object.entries(metrics)
  return (
    <div style={{ background: '#0b0f14', padding: 12, borderRadius: 8, color: '#fff' }}>
      <h3 style={{ marginTop: 0 }}>Metrics</h3>
      {entries.length === 0 ? (
        <div>No metrics</div>
      ) : (
        <ul>
          {entries.map(([k, v]) => (
            <li key={k}>
              <strong>{k}</strong>: {String(v)}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}



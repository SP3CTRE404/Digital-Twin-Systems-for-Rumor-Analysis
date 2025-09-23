import React from 'react'

export default function Gauge({ value = 0.5, label = 'Score' }) {
  const clamped = Math.max(0, Math.min(1, value))
  const size = 180
  const stroke = 16
  const r = (size - stroke) / 2
  const cx = size / 2
  const cy = size / 2

  const startAngle = Math.PI
  const endAngle = Math.PI * (1 - clamped)

  const startX = cx + r * Math.cos(startAngle)
  const startY = cy + r * Math.sin(startAngle)
  const endX = cx + r * Math.cos(endAngle)
  const endY = cy + r * Math.sin(endAngle)

  const largeArc = 0

  const arcPath = `M ${startX} ${startY} A ${r} ${r} 0 ${largeArc} 1 ${endX} ${endY}`

  return (
    <div style={{ background: '#0b0f14', padding: 12, borderRadius: 8, color: '#fff' }}>
      <svg width={size} height={size / 2} viewBox={`0 0 ${size} ${size / 2}`}>
        <path
          d={`M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${cx + r} ${cy}`}
          fill="none"
          stroke="#223043"
          strokeWidth={stroke}
          strokeLinecap="round"
        />
        <path
          d={arcPath}
          fill="none"
          stroke="#3b82f6"
          strokeWidth={stroke}
          strokeLinecap="round"
        />
        <circle cx={endX} cy={endY} r={stroke / 2} fill="#3b82f6" />
      </svg>
      <div style={{ textAlign: 'center', marginTop: 8 }}>
        {label}: {(clamped * 100).toFixed(1)}%
      </div>
    </div>
  )
}



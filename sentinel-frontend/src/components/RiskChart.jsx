import React from 'react'
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js'
import { Doughnut } from 'react-chartjs-2'

ChartJS.register(ArcElement, Tooltip, Legend)

export default function RiskChart({ result }) {
  const harm = Number(result?.harm_score ?? result?.harm?.harmfulness_score ?? 0)
  const veracity = Number(result?.veracity_score ?? 0)
  const threat = Number(result?.threat_score ?? (harm * (1 - veracity)))

  const data = {
    labels: ['Harm', 'Veracity', 'Threat'],
    datasets: [
      {
        data: [harm, veracity, threat],
        backgroundColor: ['#ef4444', '#3b82f6', '#f59e0b'],
      },
    ],
  }

  const options = {
    maintainAspectRatio: false,
    plugins: { legend: { position: 'bottom' } }
  }

  return (
    <div className="bg-white p-4 rounded shadow" style={{ width: 360, height: 260 }}>
      <h2 className="font-bold mb-3">Risk Scores</h2>
      <div style={{ width: '100%', height: 180 }}>
        <Doughnut data={data} options={options} />
      </div>
      <div className="mt-2 text-sm text-gray-600">Harm: {harm.toFixed(3)} | Veracity: {veracity.toFixed(3)} | Threat: {threat.toFixed(3)}</div>
    </div>
  )
}




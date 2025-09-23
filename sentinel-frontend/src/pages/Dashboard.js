import React from 'react'
import { useLocation } from 'react-router-dom'
import RiskChart from '../components/RiskChart'
import RumorGraph from '../components/RumorGraph'

export default function Dashboard() {
  const { state } = useLocation()
  const result = state?.result

  if (!result) return <div className="p-10">No result. Go back and run a simulation.</div>

  return (
    <div className="p-10">
      <h1 className="text-2xl font-bold mb-4">Simulation Results</h1>
      <p><strong>Rumor:</strong> {result.rumor_text}</p>
      <p><strong>Stance:</strong> {result.stance}</p>
      <p><strong>Sentiment:</strong> {result.sentiment}</p>

      <div className="grid grid-cols-2 gap-6 mt-6">
        <RiskChart result={result} />
        <RumorGraph graph={result.graph} />
      </div>
    </div>
  )
}








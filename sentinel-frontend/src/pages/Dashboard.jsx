import React, { useMemo, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import RiskChart from '../components/RiskChart.jsx'
import RumorGraph from '../components/RumorGraph.jsx'
import AnalysisResults from '../components/AnalysisResults.jsx'

export default function Dashboard() {
  const { state } = useLocation()
  const navigate = useNavigate()
  const { analysis, simulation: result } = state || {}

  if (!analysis || !result) {
    return <div className="p-10">No analysis results. <button onClick={() => navigate('/')} className="text-blue-500 hover:underline">Go back</button> and analyze a rumor.</div>
  }

  const harm = result?.harm?.harmfulness_score ?? result?.harm_score ?? analysis.harm_score
  const graph = result?.graph || { nodes: [{ id: 0, stance: 'comment' }], edges: [] }
  const timeline = result?.timeline || []
  const [stepIdx, setStepIdx] = useState(timeline.length ? timeline.length - 1 : 0)
  const currentTime = useMemo(() => (timeline[stepIdx]?.time ?? null), [timeline, stepIdx])

  const filteredGraph = useMemo(() => {
    const g = graph || { nodes: [], edges: [] }
    if (currentTime == null) return g
    const nodes = (g.nodes || []).filter(n => typeof n.posted_time === 'number' ? n.posted_time <= currentTime : true)
    const allowed = new Set(nodes.map(n => n.id))
    const edges = (g.edges || []).filter(e => allowed.has(e.source) && allowed.has(e.target))
    return { nodes, edges }
  }, [graph, currentTime])
  const comps = result?.harm?.components || {}
  const sentimentDist = comps?.sentiment_distribution || {}
  const stanceDist = comps?.stance_distribution || {}
  const dominantSentiment = Object.keys(sentimentDist).sort((a, b) => sentimentDist[b] - sentimentDist[a])[0]
  const dominantStance = Object.keys(stanceDist).sort((a, b) => stanceDist[b] - stanceDist[a])[0]

  return (
    <div className="p-10">
      <h1 className="text-2xl font-bold mb-4">Rumor Analysis & Simulation</h1>

      <AnalysisResults analysis={analysis} />

      <div className="grid grid-cols-2 gap-6 mt-6">
        <RiskChart result={{ ...result, harm_score: harm }} />
        <RumorGraph graph={filteredGraph} harm={Number(harm || 0)} />
      </div>

      {timeline.length > 0 && (
        <div className="mt-6 bg-white p-4 rounded shadow">
          <h2 className="font-bold mb-2">Cascade Timeline</h2>
          <div className="text-sm text-gray-700 mb-2">Steps: {timeline.length}</div>
          <input
            type="range"
            min={0}
            max={Math.max(0, timeline.length - 1)}
            value={stepIdx}
            onChange={(e) => setStepIdx(parseInt(e.target.value, 10))}
            style={{ width: '100%' }}
          />
          <div className="text-xs text-gray-600 mt-1">t = {currentTime ?? 0}</div>
          <div className="mt-2 text-xs font-mono overflow-auto" style={{ maxHeight: 140 }}>
            {timeline.map((snap, i) => (
              <div key={i}>t={snap.time}: size={snap.cascade_size}</div>
            ))}
          </div>
        </div>
      )}

      <div className="grid grid-cols-2 gap-6 mt-6">
        <div className="bg-white p-4 rounded shadow">
          <h2 className="font-bold mb-2">Sentiment</h2>
          {dominantSentiment && (
            <div className="mb-2 text-sm text-gray-700">Dominant: <strong>{dominantSentiment}</strong></div>
          )}
          <pre className="text-xs overflow-auto" style={{ maxHeight: 160 }}>
            {JSON.stringify(sentimentDist, null, 2)}
          </pre>
        </div>
        <div className="bg-white p-4 rounded shadow">
          <h2 className="font-bold mb-2">Stance</h2>
          {dominantStance && (
            <div className="mb-2 text-sm text-gray-700">Dominant: <strong>{dominantStance}</strong></div>
          )}
          <pre className="text-xs overflow-auto" style={{ maxHeight: 160 }}>
            {JSON.stringify(stanceDist, null, 2)}
          </pre>
        </div>
      </div>

      {result?.harm?.components && (
        <div className="mt-6 bg-white p-4 rounded shadow">
          <h2 className="font-bold mb-2">Components</h2>
          <pre className="text-xs overflow-auto" style={{ maxHeight: 240 }}>
            {JSON.stringify(result.harm.components, null, 2)}
          </pre>
        </div>
      )}
    </div>
  )
}



import React, { useEffect, useState } from 'react'
import { useLocation } from 'react-router-dom'
import axios from 'axios'
import ForceGraph2D from 'react-force-graph-2d'
import Gauge from '../components/Gauge'

export default function Simulation() {
  const location = useLocation()
  const rumorText = location.state?.text || 'No rumor given'
  const [data, setData] = useState(null)

  useEffect(() => {
    async function fetchData() {
      try {
        const res = await axios.post('http://127.0.0.1:5000/simulate', { text: rumorText })
        setData(res.data)
      } catch (err) {
        console.error('Error calling API:', err)
      }
    }
    fetchData()
  }, [rumorText])

  if (!data) return <p>Loading simulation...</p>

  return (
    <div>
      <h2 className="text-2xl font-bold mb-4">Simulation Results</h2>
      <p className="mb-4"><b>Rumor:</b> {data.rumor_text}</p>

      <div className="grid grid-cols-3 gap-4 mb-6">
        <Gauge value={data.harm_score} label="Harm" />
        <Gauge value={data.veracity_score} label="Veracity" />
        <Gauge value={data.threat_score} label="Threat" />
      </div>

      <div className="bg-white shadow-lg rounded-2xl p-4">
        <h3 className="text-xl font-bold mb-2">Digital Twin Propagation</h3>
        <ForceGraph2D
          graphData={{
            nodes: (data.graph?.nodes || []).map((n) => ({
              id: n.id,
              name: n.stance,
              color: n.stance === 'support' ? 'green' : n.stance === 'deny' ? 'red' : n.stance === 'question' ? 'orange' : 'blue'
            })),
            links: (data.graph?.edges || []).map((e) => ({ source: e.source, target: e.target }))
          }}
          nodeAutoColorBy="stance"
          nodeLabel="name"
          width={600}
          height={400}
        />
      </div>

      <div className="mt-4">
        <h3 className="font-bold">Simulation Stats</h3>
        <ul className="list-disc pl-6">
          <li>Cascade size: {data.stats?.cascade_size ?? (data.graph?.nodes?.length ?? 'n/a')}</li>
          <li>Max depth: {data.stats?.max_depth ?? 'n/a'}</li>
          <li>Time to peak: {data.stats?.time_to_peak ?? 'n/a'}</li>
        </ul>
      </div>
    </div>
  )
}

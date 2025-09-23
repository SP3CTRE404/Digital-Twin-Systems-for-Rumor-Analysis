import React, { useEffect, useRef } from 'react'
import ForceGraph2D from 'react-force-graph-2d'

export default function NetworkGraph({ graph }) {
  const fgRef = useRef()

  const data = graph || {
    nodes: Array.from({ length: 12 }, (_, i) => ({ id: i })),
    links: Array.from({ length: 12 }, (_, i) => ({ source: i, target: (i + 1) % 12 }))
  }

  useEffect(() => {
    // center at init
    if (fgRef.current) {
      fgRef.current.zoomToFit(400)
    }
  }, [])

  return (
    <div style={{ height: 480, background: '#0b0f14', borderRadius: 8 }}>
      <ForceGraph2D
        ref={fgRef}
        graphData={data}
        nodeLabel={(n) => `Node ${n.id}`}
        linkColor={() => 'rgba(255,255,255,0.2)'}
        nodeAutoColorBy="id"
      />
    </div>
  )
}



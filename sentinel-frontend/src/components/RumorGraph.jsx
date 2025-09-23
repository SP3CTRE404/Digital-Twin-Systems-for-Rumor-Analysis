import React, { useEffect, useRef } from 'react'
import * as d3 from 'd3'

export default function RumorGraph({ graph, harm }) {
  const svgRef = useRef(null)

  useEffect(() => {
    const svg = d3.select(svgRef.current)
    svg.selectAll('*').remove()

    const nodes = graph?.nodes || []
    const links = graph?.edges || []

    const width = 400
    const height = 400

    const simulation = d3
      .forceSimulation(nodes)
      .force('link', d3.forceLink(links).id((d) => d.id).distance(100))
      .force('charge', d3.forceManyBody().strength(-200))
      .force('center', d3.forceCenter(width / 2, height / 2))

    const link = svg
      .append('g')
      .selectAll('line')
      .data(links)
      .enter()
      .append('line')
      .attr('stroke', '#999')

    const colorFor = (d) => {
      const s = (d.stance || d.bias || '').toLowerCase()
      if (s === 'support') return '#16a34a'      // green
      if (s === 'deny') return '#ef4444'         // red
      if (s === 'question' || s === 'query') return '#f59e0b' // yellow
      // fallback by sentiment
      const sent = (d.sentiment || '').toLowerCase()
      if (sent === 'positive') return '#16a34a'
      if (sent === 'negative') return '#ef4444'
      if (sent === 'neutral') return '#9ca3af'
      return '#9ca3af'
    }

    const node = svg
      .append('g')
      .selectAll('circle')
      .data(nodes)
      .enter()
      .append('circle')
      .attr('r', 8)
      .attr('fill', (d) => colorFor(d))
      .attr('stroke', '#111')
      .attr('stroke-width', 0.5)
      .append('title')
      .text((d) => `${d.id}: ${d.stance || 'node'}`)

    simulation.on('tick', () => {
      link
        .attr('x1', (d) => d.source.x)
        .attr('y1', (d) => d.source.y)
        .attr('x2', (d) => d.target.x)
        .attr('y2', (d) => d.target.y)

      node.attr('cx', (d) => d.x).attr('cy', (d) => d.y)
    })
  }, [graph])

  return <svg ref={svgRef} width={500} height={360}></svg>
}




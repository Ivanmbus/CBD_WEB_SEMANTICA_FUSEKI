import { useState, useEffect, useRef } from 'react'
import ForceGraph2D from 'react-force-graph-2d'

const NODE_COLORS = {
  'Planeta':      '#a855f7',
  'Satelite':     '#06d6f0',
  'Sol':          '#f59e0b',
  'PlanetaEnano': '#f97316',
  'Asteroide':    '#64748b',
}

function Spinner() {
  return (
    <div className="spinner-wrap">
      <div className="spinner" />
    </div>
  )
}

export default function GrafoPanel() {
  const [grafo,   setGrafo]   = useState({ nodes: [], links: [] })
  const [loading, setLoading] = useState(true)
  const [error,   setError]   = useState(null)
  const containerRef          = useRef(null)
  const [dims,    setDims]    = useState({ w: 800, h: 500 })

  useEffect(() => {
    fetch('/api/grafo')
      .then(r => { if (!r.ok) throw new Error(r.statusText); return r.json() })
      .then(data => { setGrafo(data); setLoading(false) })
      .catch(e  => { setError(e.message); setLoading(false) })
  }, [])

  useEffect(() => {
    if (!containerRef.current) return
    const ro = new ResizeObserver(entries => {
      const { width, height } = entries[0].contentRect
      setDims({ w: width, h: Math.max(height, 500) })
    })
    ro.observe(containerRef.current)
    return () => ro.disconnect()
  }, [])

  return (
    <div className="grafo-wrap" ref={containerRef}>
      {loading && <Spinner />}
      {error   && <p className="error-msg">Error: {error}</p>}
      {!loading && !error && (
        <>
          <div className="grafo-legend">
            {Object.entries(NODE_COLORS).map(([tipo, color]) => (
              <span key={tipo} className="grafo-legend__item">
                <span className="grafo-legend__dot" style={{ background: color }} />
                {tipo}
              </span>
            ))}
          </div>
          <ForceGraph2D
            graphData={grafo}
            width={dims.w}
            height={dims.h}
            backgroundColor="transparent"
            nodeLabel="id"
            nodeColor={n => NODE_COLORS[n.type] ?? '#94a3b8'}
            nodeRelSize={5}
            linkColor={() => 'rgba(255,255,255,0.15)'}
            linkWidth={1}
            linkDirectionalArrowLength={4}
            linkDirectionalArrowRelPos={1}
            linkLabel="label"
            nodeCanvasObject={(node, ctx, globalScale) => {
              const fontSize = Math.max(10 / globalScale, 3)
              const r = node.type === 'Sol' ? 10 : node.type === 'Planeta' ? 7 : 4
              ctx.beginPath()
              ctx.arc(node.x, node.y, r, 0, 2 * Math.PI)
              ctx.fillStyle   = NODE_COLORS[node.type] ?? '#94a3b8'
              ctx.shadowColor = NODE_COLORS[node.type] ?? '#94a3b8'
              ctx.shadowBlur  = 8
              ctx.fill()
              ctx.shadowBlur  = 0
              if (globalScale >= 0.6) {
                ctx.font         = `${fontSize}px Syne, sans-serif`
                ctx.fillStyle    = 'rgba(255,255,255,0.85)'
                ctx.textAlign    = 'center'
                ctx.textBaseline = 'middle'
                ctx.fillText(node.id, node.x, node.y + r + fontSize)
              }
            }}
          />
        </>
      )}
    </div>
  )
}
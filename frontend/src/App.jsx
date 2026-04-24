import { useState, useEffect } from 'react'
import GrafoPanel from './components/GrafoPanel'
import './App.css'




function round(v, d = 3) {
  const n = parseFloat(v)
  return isNaN(n) ? '—' : n.toFixed(d)
}

const TIPO_COLOR = {
  'rocoso':           '#f97316',
  'gigante gaseoso':  '#3b82f6',
  'gigante helado':   '#06b6d4',
}

// ── Componentes ──────────────────────────────────────────────────

function Spinner() {
  return (
    <div className="spinner-wrap">
      <div className="spinner" />
    </div>
  )
}

function PlanetCard({ planeta, onClick }) {
  // El backend devuelve objetos planos { nombre, tipo, semieje, periodo }
  const nombre  = planeta.nombre  ?? '—'
  const tipo    = planeta.tipo    ?? '—'
  const semieje = round(planeta.semieje, 2)
  const periodo = round(planeta.periodo, 1)
  const color   = TIPO_COLOR[tipo] ?? '#a855f7'

  return (
    <div className="planet-card" onClick={() => onClick(nombre)} style={{ '--accent-card': color }}>
      <div className="planet-card__glow" />
      <div className="planet-card__body">
        <span className="planet-card__tipo" style={{ color }}>
          {tipo}
        </span>
        <h2 className="planet-card__nombre">{nombre}</h2>
        <div className="planet-card__stats">
          <div className="stat">
            <span className="stat__label">Semieje mayor</span>
            <span className="stat__value">{semieje} <em>AU</em></span>
          </div>
          <div className="stat">
            <span className="stat__label">Período orbital</span>
            <span className="stat__value">{periodo} <em>días</em></span>
          </div>
        </div>
      </div>
    </div>
  )
}

function OrbitalRow({ label, value, unit }) {
  return (
    <div className="orbital-row">
      <span className="orbital-row__label">{label}</span>
      <span className="orbital-row__value">{value} <em>{unit}</em></span>
    </div>
  )
}

function DetailPanel({ nombre, onClose }) {
  const [data,      setData]      = useState(null)   // { name, info, images }
  const [satelites, setSatelites] = useState([])
  const [loading,   setLoading]   = useState(true)
  const [tab,       setTab]       = useState('orbita')

  useEffect(() => {
    const loadingTimer = setTimeout(() => setLoading(true), 0)
    let cancelled = false
    Promise.all([
      fetch(`/api/planets/completo/${encodeURIComponent(nombre)}`).then(r => {
        if (!r.ok) throw new Error(r.statusText)
        return r.json()
      }),
      fetch(`/api/planets/satelite/${encodeURIComponent(nombre)}`).then(r => {
        if (!r.ok) throw new Error(r.statusText)
        return r.json()
      }),
    ]).then(([planetaData, satRes]) => {
      setData(planetaData)
      setSatelites(satRes.satellites ?? [])
      setLoading(false)
    }).catch(() => setLoading(false))

    return () => {
      cancelled = true
      clearTimeout(loadingTimer)
    }
  }, [nombre])

  const info   = data?.info   ?? null
  const images = data?.images ?? []

  return (
    <div className="detail-overlay" onClick={onClose}>
      <div className="detail-panel" onClick={e => e.stopPropagation()}>
        <button className="detail-panel__close" onClick={onClose}>✕</button>

        <h2 className="detail-panel__title">{nombre}</h2>

        {loading ? <Spinner /> : !info ? (
          <p className="empty-msg">No se encontraron datos.</p>
        ) : (
          <>
            <div className="detail-tabs">
              <button className={`detail-tab ${tab === 'orbita'    ? 'active' : ''}`} onClick={() => setTab('orbita')}>Órbita</button>
              <button className={`detail-tab ${tab === 'satelites' ? 'active' : ''}`} onClick={() => setTab('satelites')}>
                Satélites {satelites.length > 0 && <span className="badge">{satelites.length}</span>}
              </button>
            </div>

            {tab === 'orbita' && (
              <div className="detail-section">
                {/* Imágenes devueltas por el backend */}
                {images.length > 0 && (
                  <div className="detail-images">
                    {images.map((src, i) => (
                      <img key={i} src={src} alt={`${nombre} ${i + 1}`} className="detail-img" />
                    ))}
                  </div>
                )}
                <div className="detail-tipo" style={{ color: TIPO_COLOR[info.tipo] ?? '#a855f7' }}>
                  {info.tipo}
                </div>
                <div className="orbital-grid">
                  <OrbitalRow label="Semieje mayor"   value={round(info.semieje,        4)} unit="AU"   />
                  <OrbitalRow label="Período orbital"  value={round(info.periodo,        2)} unit="días" />
                  <OrbitalRow label="Perihelio"        value={round(info.perihelio,      4)} unit="AU"   />
                  <OrbitalRow label="Afelio"           value={round(info.afelio,         4)} unit="AU"   />
                  <OrbitalRow label="Excentricidad"    value={round(info.excentricidad,  6)} unit=""     />
                  <OrbitalRow label="Inclinación"      value={round(info.inclinacionDeg, 4)} unit="°"    />
                  <OrbitalRow label="Arg. periapsis"   value={round(info.periapsis,      4)} unit="°"    />
                  <OrbitalRow label="Anomalía media"   value={round(info.anomaliaMediaDeg, 4)} unit="°"  />
                </div>
              </div>
            )}

            {tab === 'satelites' && (
              <div className="detail-section">
                {satelites.length === 0 ? (
                  <p className="empty-msg">Sin satélites registrados.</p>
                ) : (
                  <table className="sat-table">
                    <thead>
                      <tr>
                        <th>Nombre</th>
                        <th>Semieje (km)</th>
                        <th>Período (días)</th>
                        <th>Excentricidad</th>
                        <th>Inclinación</th>
                      </tr>
                    </thead>
                    <tbody>
                        {satelites.map((s, i) => (
                          <tr key={i}>
                            <td>{s.nombre}</td>
                            <td>{round(s.semiejeMayor, 1)}</td>
                            <td>{round(s.periodo,      3)}</td>
                            <td>{round(s.excentricidad,5)}</td>
                            <td>{round(s.inclinacion,  3)}°</td>
                          </tr>
                        ))}
                    </tbody>
                  </table>
                )}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
function QueryTable({ columns, rows }) {
  return (
    <div className="query-table-wrap">
      <table className="query-table">
        <thead>
          <tr>
            {columns.map((col) => (
              <th key={col}>{col}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i}>
              {columns.map((col) => (
                <td key={col}>{formatCell(row[col])}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function QueryCards({ columns, rows }) {
  const normalizedImageNames = [
    'imagen',
    'image',
    'img',
    'urlimagen',
    'imagenurl',
    'imagendescubridorurl',
  ]

  return (
    <div className="query-cards">
      {rows.map((row, i) => {
        const imageColumns = columns.filter((col) =>
          normalizedImageNames.includes(col.toLowerCase())
        )

        const textColumns = columns.filter(
          (col) => !normalizedImageNames.includes(col.toLowerCase())
        )

        const images = imageColumns
          .map((col) => row[col])
          .filter((value) => typeof value === 'string' && value.startsWith('http'))

        return (
          <article key={i} className="query-card">
            {images.length > 0 && (
              <div className="query-card__images">
                {images.map((src, idx) => (
                  <img
                    key={idx}
                    src={src}
                    alt={`resultado-${i}-img-${idx}`}
                    className="query-card__img"
                    loading="lazy"
                  />
                ))}
              </div>
            )}

            {textColumns.map((col) => (
              <div key={col} className="query-card__row">
                <span className="query-card__label">{col}</span>
                <span className="query-card__value">{formatCell(row[col])}</span>
              </div>
            ))}
          </article>
        )
      })}
    </div>
  )
}

function SimpleResultGraph({ graph }) {
  return (
    <div className="simple-graph">
      <div className="simple-graph__nodes">
        {graph.nodes.map((node) => (
          <div key={node.id} className="simple-graph__node">
            {node.label}
          </div>
        ))}
      </div>

      <div className="simple-graph__edges">
        {graph.edges.map((edge, i) => (
          <div key={i} className="simple-graph__edge">
            <strong>{edge.source}</strong>
            <span>{edge.label ? ` — ${edge.label} → ` : ' → '}</span>
            <strong>{edge.target}</strong>
          </div>
        ))}
      </div>
    </div>
  )
}

function formatCell(value) {
  if (value === null || value === undefined || value === '') return '—'
  if (typeof value === 'object') return JSON.stringify(value)
  return String(value)
}

function buildGraphData(rows, columns) {
  const sourceKey =
    columns.find((c) => ['source', 'from', 's', 'subject'].includes(c)) || null
  const targetKey =
    columns.find((c) => ['target', 'to', 'o', 'object'].includes(c)) || null
  const labelKey =
    columns.find((c) => ['label', 'predicate', 'p', 'rel'].includes(c)) || null

  if (!sourceKey || !targetKey) {
    return { nodes: [], edges: [] }
  }

  const nodeMap = new Map()
  const edges = []

  rows.forEach((row) => {
    const source = formatCell(row[sourceKey])
    const target = formatCell(row[targetKey])
    const label = labelKey ? formatCell(row[labelKey]) : ''

    if (source && source !== '—' && !nodeMap.has(source)) {
      nodeMap.set(source, { id: source, label: source })
    }
    if (target && target !== '—' && !nodeMap.has(target)) {
      nodeMap.set(target, { id: target, label: target })
    }

    if (source !== '—' && target !== '—') {
      edges.push({ source, target, label })
    }
  })

  return {
    nodes: Array.from(nodeMap.values()),
    edges,
  }
}
// ── App ──────────────────────────────────────────────────────────
function QueryWorkbench() {
  const [query, setQuery] = useState(`PREFIX sol: <http://ejemplo.org/sistema-solar#>

SELECT ?nombre ?tipo
WHERE {
  ?p a sol:Planeta ;
     sol:nombre ?nombre ;
     sol:tipoPlaneta ?tipo .
}
ORDER BY ?nombre`)

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [rows, setRows] = useState([])
  const [columns, setColumns] = useState([])
  const [view, setView] = useState('tabla')
  const [hasRun, setHasRun] = useState(false)

  const consultasEjemplo = [
    {
      titulo: 'Todos los planetas',
      descripcion: 'Lista nombre y tipo de todos los planetas.',
      query: `PREFIX sol: <http://ejemplo.org/sistema-solar#>

SELECT ?nombre ?tipo
WHERE {
  ?p a sol:Planeta ;
     sol:nombre ?nombre ;
     sol:tipoPlaneta ?tipo .
}
ORDER BY ?nombre`
    },
    {
      titulo: 'Planetas y satélites',
      descripcion: 'Muestra los satélites de cada planeta.',
      query: `PREFIX sol: <http://ejemplo.org/sistema-solar#>

SELECT ?planeta ?satelite
WHERE {
  ?p a sol:Planeta ;
     sol:nombre ?planeta ;
     sol:tieneSatelite ?s .
  ?s sol:nombre ?satelite .
}
ORDER BY ?planeta ?satelite`
    },
    {
      titulo: 'Órbitas planetarias',
      descripcion: 'Semieje mayor y período orbital.',
      query: `PREFIX sol: <http://ejemplo.org/sistema-solar#>

SELECT ?nombre ?semieje ?periodo
WHERE {
  ?p a sol:Planeta ;
     sol:nombre ?nombre ;
     sol:tieneOrbita ?o .
  ?o sol:semiejeMayorAu ?semieje ;
     sol:periodoOrbitalDias ?periodo .
}
ORDER BY ?semieje`
    },
    {
      titulo: 'Imágenes de planetas',
      descripcion: 'Devuelve nombre e imagen.',
      query: `PREFIX sol: <http://ejemplo.org/sistema-solar#>

SELECT ?nombre ?imagenUrl
WHERE {
  ?p a sol:Planeta ;
     sol:nombre ?nombre ;
     sol:imagenUrl ?imagenUrl .
}
ORDER BY ?nombre`
    },
  ]

  function applyExample(exampleQuery) {
    setQuery(exampleQuery)
  }

  async function runQuery() {
    setHasRun(true)
    setLoading(true)
    setError(null)

    try {
      const res = await fetch('http://localhost:8000/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query }),
      })

      const data = await res.json()

      if (!res.ok) {
        throw new Error(data.detail || 'No se pudo ejecutar la consulta')
      }

      setColumns(data.columns ?? [])
      setRows(data.rows ?? [])
    } catch (e) {
      setError(e.message || 'No se pudo ejecutar la consulta')
      setColumns([])
      setRows([])
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="query-page">
      <div className="query-shell">
        <div className="query-main-column">
          <div className="query-editor-card">
            <div className="query-editor-top">
              <div>
                <h2 className="query-title">Consulta SPARQL</h2>
                <p className="query-sub">
                  Escribe una consulta y visualiza los resultados.
                </p>
              </div>

              <button className="query-run-btn" onClick={runQuery} disabled={loading}>
                {loading ? 'Ejecutando…' : 'Ejecutar'}
              </button>
            </div>

            <textarea
              className="query-editor"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              spellCheck={false}
            />
          </div>

          <div className="query-results-card">
            <div className="detail-tabs">
              <button
                className={`detail-tab ${view === 'tabla' ? 'active' : ''}`}
                onClick={() => setView('tabla')}
              >
                Tabla
              </button>
              <button
                className={`detail-tab ${view === 'visual' ? 'active' : ''}`}
                onClick={() => setView('visual')}
              >
                Visual
              </button>
            </div>

            {loading ? (
              <Spinner />
            ) : error ? (
              <p className="error-msg">{error}</p>
            ) : rows.length === 0 ? (
              <p className="empty-msg">
                {hasRun
                  ? 'No se han encontrado resultados para esta consulta.'
                  : 'Ejecuta una consulta para ver resultados.'}
              </p>
            ) : view === 'tabla' ? (
              <div className="query-table-wrap">
                <table className="query-table">
                  <thead>
                    <tr>
                      {columns.map((col) => (
                        <th key={col}>{col}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {rows.map((row, i) => (
                      <tr key={i}>
                        {columns.map((col) => (
                          <td key={col}>{row[col] ?? '—'}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <QueryCards columns={columns} rows={rows} />
            )}
          </div>
        </div>

        <aside className="query-side-column">
          <div className="query-examples-panel">
            <h3 className="query-examples__title">Consultas recomendadas</h3>

            <div className="query-examples__list">
              {consultasEjemplo.map((item, i) => (
                <button
                  key={i}
                  type="button"
                  className="query-example-card"
                  onClick={() => applyExample(item.query)}
                >
                  <span className="query-example-card__title">{item.titulo}</span>
                  <span className="query-example-card__desc">{item.descripcion}</span>
                </button>
              ))}
            </div>
          </div>
        </aside>
      </div>
    </section>
  )
}

export default function App() {
  const [planetas,       setPlanetas]       = useState([])
  const [loading,        setLoading]        = useState(true)
  const [error,          setError]          = useState(null)
  const [selectedPlanet, setSelectedPlanet] = useState(null)
  const [filtroTipo,     setFiltroTipo]     = useState('todos')
  const [vista, setVista] = useState('planetas') // 'planetas' | 'grafo' | 'consulta'

  useEffect(() => {
    // Usa el endpoint /planets/lista que devuelve { planets: [{nombre, tipo, semieje, periodo}] }
    fetch('/api/planets/lista')
      .then(r => { if (!r.ok) throw new Error(r.statusText); return r.json() })
      .then(data => { setPlanetas(data.planets ?? []); setLoading(false) })
      .catch(e  => { setError(e.message); setLoading(false) })
  }, [])

  const tipos = ['todos', ...new Set(planetas.map(p => p.tipo ?? '—').filter(t => t !== '—'))]

  const planetasFiltrados = filtroTipo === 'todos'
    ? planetas
    : planetas.filter(p => p.tipo === filtroTipo)

  // Generadas una sola vez para evitar Math.random en cada render
  const [stars] = useState(() =>
    Array.from({ length: 80 }, (_, i) => ({
      id:       i,
      left:     `${Math.random() * 100}%`,
      top:      `${Math.random() * 100}%`,
      delay:    `${Math.random() * 4}s`,
      duration: `${2 + Math.random() * 3}s`,
      size:     `${1 + Math.random() * 2}px`,
    }))
  )

  return (
    <div className="app">
      {/* Fondo estrellado */}
      <div className="starfield" aria-hidden="true">
        {stars.map(s => (
          <div key={s.id} className="star" style={{
            left:              s.left,
            top:               s.top,
            animationDelay:    s.delay,
            animationDuration: s.duration,
            width:             s.size,
            height:            s.size,
          }} />
        ))}
      </div>

      {/* Header */}
      <header className="app-header">
        <div className="app-header__inner">
          <div className="app-header__logo">
            <span className="logo-dot" />
            <span className="logo-dot logo-dot--2" />
          </div>
          <h1 className="app-header__title">Astronomy RDF DataBase</h1>
          <p className="app-header__sub">Sistema Solar · Apache Jena Fuseki · SPARQL</p>
          <nav className="app-nav">
            <button className={`nav-btn ${vista === 'planetas' ? 'active' : ''}`} onClick={() => setVista('planetas')}>
              Planetas
            </button>
            <button className={`nav-btn ${vista === 'grafo' ? 'active' : ''}`} onClick={() => setVista('grafo')}>
              Grafo RDF
            </button>
            <button className={`nav-btn ${vista === 'consulta' ? 'active' : ''}`} onClick={() => setVista('consulta')}>
              Consulta
            </button>
          </nav>
        </div>
      </header>

      {/* Filtros: solo en vista planetas */}
      {vista === 'planetas' && (
        <div className="filters">
          {tipos.map(tipo => (
            <button
              key={tipo}
              className={`filter-btn ${filtroTipo === tipo ? 'active' : ''}`}
              style={
                filtroTipo === tipo && tipo !== 'todos'
                  ? { borderColor: TIPO_COLOR[tipo], color: TIPO_COLOR[tipo] }
                  : {}
              }
              onClick={() => setFiltroTipo(tipo)}
            >
              {tipo}
            </button>
          ))}
        </div>
      )}

      {/* Contenido principal */}
      <main className="app-main">
        {vista === 'consulta' ? (
          <QueryWorkbench />
        ) : vista === 'grafo' ? (
          <GrafoPanel />
        ) : (
          <>
            {loading && <Spinner />}
            {error && <p className="error-msg">Error: {error}</p>}
            {!loading && !error && (
              <div className="planet-grid">
                {planetasFiltrados.map((p, i) => (
                  <PlanetCard key={i} planeta={p} onClick={setSelectedPlanet} />
                ))}
              </div>
            )}
          </>
        )}
      </main>

      {/* Panel de detalle */}
      {selectedPlanet && (
        <DetailPanel
          nombre={selectedPlanet}
          onClose={() => setSelectedPlanet(null)}
        />
      )}
    </div>
  )
}

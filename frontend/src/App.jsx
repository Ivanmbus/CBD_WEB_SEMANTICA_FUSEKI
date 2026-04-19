import { useState, useEffect } from 'react'
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

// ── App ──────────────────────────────────────────────────────────
export default function App() {
  const [planetas,       setPlanetas]       = useState([])
  const [loading,        setLoading]        = useState(true)
  const [error,          setError]          = useState(null)
  const [selectedPlanet, setSelectedPlanet] = useState(null)
  const [filtroTipo,     setFiltroTipo]     = useState('todos')

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
        </div>
      </header>

      {/* Filtros */}
      <div className="filters">
        {tipos.map(tipo => (
          <button
            key={tipo}
            className={`filter-btn ${filtroTipo === tipo ? 'active' : ''}`}
            style={filtroTipo === tipo && tipo !== 'todos'
              ? { borderColor: TIPO_COLOR[tipo], color: TIPO_COLOR[tipo] }
              : {}
            }
            onClick={() => setFiltroTipo(tipo)}
          >
            {tipo}
          </button>
        ))}
      </div>

      {/* Contenido principal */}
      <main className="app-main">
        {loading && <Spinner />}
        {error   && <p className="error-msg">Error: {error}</p>}
        {!loading && !error && (
          <div className="planet-grid">
            {planetasFiltrados.map((p, i) => (
              <PlanetCard
                key={i}
                planeta={p}
                onClick={setSelectedPlanet}
              />
            ))}
          </div>
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

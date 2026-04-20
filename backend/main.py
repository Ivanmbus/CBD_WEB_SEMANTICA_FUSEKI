from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from SPARQLWrapper import SPARQLWrapper, JSON
from pydantic import BaseModel

app = FastAPI()

#Allows react port to call backend when needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

FUSEKI_URL = "http://fuseki:3030/miDataset/query"

class QueryRequest(BaseModel):
    query: str

def config_request(query: str):
    sparql = SPARQLWrapper(FUSEKI_URL)
    sparql.setQuery(query)
    sparql.setCredentials("admin", "admin123")
    sparql.setReturnFormat(JSON)
    return sparql

@app.post("/query")
def run_query(request: QueryRequest):
    sparql = config_request(request.query)
    
    try:
        results = sparql.query().convert()
        return results
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/planets")
def get_planets():
    query = """PREFIX sol: <http://ejemplo.org/sistema-solar#>
            SELECT ?planeta 
            WHERE {
            ?p a sol:Planeta ;
                sol:nombre ?planeta .
            }"""
    sparql = config_request(query)
    try:
        results = sparql.query().convert()
        planets = [result['planeta']['value'] for result in results["results"]["bindings"]]
        return {"planets": planets}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@app.get("/planets/satelite/{name}")
def get_planet_satellites(name: str):

    query = f"""
        PREFIX sol: <http://ejemplo.org/sistema-solar#>
        SELECT ?satelite ?semiejeMayor ?periodo ?excentricidad ?inclinacion
        WHERE {{
        ?p a sol:Planeta ;
            sol:nombre "{name}" ;
            sol:tieneSatelite ?s .
        ?s sol:nombre ?satelite ;
            sol:tieneOrbita ?o .
        ?o sol:semiejeMayorKm ?semiejeMayor ;
            sol:periodoOrbitalDias ?periodo ;
            sol:excentricidad ?excentricidad ;
            sol:inclinacionDeg ?inclinacion .
        }}
        ORDER BY ?semiejeMayor
    """
    sparql = config_request(query)
    try:
        results = sparql.query().convert()
        satellites = [
            {
                "nombre": r["satelite"]["value"],
                "semiejeMayor": r["semiejeMayor"]["value"],
                "periodo": r["periodo"]["value"],
                "excentricidad": r["excentricidad"]["value"],
                "inclinacion": r["inclinacion"]["value"],
            }
            for r in results["results"]["bindings"]
        ]
        return {"planeta": name, "satellites": satellites}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/planets/lista")
def get_planets_lista():
    query = """
        PREFIX sol: <http://ejemplo.org/sistema-solar#>
        SELECT ?nombre ?tipo ?semieje ?periodo
        WHERE {
        ?p a sol:Planeta ;
            sol:nombre ?nombre ;
            sol:tipoPlaneta ?tipo ;
            sol:tieneOrbita ?o .
        ?o sol:semiejeMayorAu ?semieje ;
            sol:periodoOrbitalDias ?periodo .
        }
        ORDER BY ?semieje
    """
    sparql = config_request(query)
    try:
        results = sparql.query().convert()
        planets = [
            {
                "nombre":  r["nombre"]["value"],
                "tipo":    r["tipo"]["value"],
                "semieje": r["semieje"]["value"],
                "periodo": r["periodo"]["value"],
            }
            for r in results["results"]["bindings"]
        ]
        return {"planets": planets}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/planets/{name}")
def get_planet_info(name: str):
    query = f"""
        PREFIX sol: <http://ejemplo.org/sistema-solar#>

        SELECT ?nombre ?tipo ?semieje ?periodo
        WHERE {{
            ?p a sol:Planeta ;
               sol:nombre ?nombre ;
               sol:tipoPlaneta ?tipo ;
               sol:tieneOrbita ?o .
            ?o sol:semiejeMayorAu ?semieje ;
               sol:periodoOrbitalDias ?periodo .

            FILTER(?nombre = "{name}")
        }}
    """
    sparql = config_request(query)
    try:
        results = sparql.query().convert()
        bindings = results["results"]["bindings"]

        if not bindings:
            raise HTTPException(status_code=404, detail=f"Planeta '{name}' no encontrado")

        # Cada columna del SELECT se lee directamente por su nombre
        row = bindings[0]
        info = {
            "nombre":  row["nombre"]["value"],
            "tipo":    row["tipo"]["value"],
            "semieje": row["semieje"]["value"],
            "periodo": row["periodo"]["value"],
        }
        return {"name": name, "info": info}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/planets/completo/{name}")
def get_planet_info(name: str):
    query = f"""
        PREFIX sol: <http://ejemplo.org/sistema-solar#>

        SELECT ?nombre ?tipo ?imagenes ?semieje ?periodo ?afelio ?perihelio ?excentricidad ?inclinacionDeg ?periapsis ?anomalia
        WHERE {{
                    ?p a sol:Planeta ;
                sol:nombre ?nombre ;
                sol:tipoPlaneta ?tipo ;
                sol:imagenUrl ?imagenes;
                sol:tieneOrbita ?o .
                    ?o sol:semiejeMayorAu ?semieje ;
                    sol:periodoOrbitalDias ?periodo ;
                    sol:afelioAu ?afelio ;
                    sol:perihelioAu ?perihelio ;
                    sol:excentricidad ?excentricidad ;
                    sol:inclinacionDeg ?inclinacionDeg ;
                    sol:argumentoPeriapsisDeg ?periapsis ;
                    sol:anomaliaMediaDeg ?anomalia .
                
                    FILTER(?nombre = "{name}")
        }}
    """
    sparql = config_request(query)
    try:
        results = sparql.query().convert()
        bindings = results["results"]["bindings"]

        if not bindings:
            raise HTTPException(status_code=404, detail=f"Planeta '{name}' no encontrado")

        # Cada columna del SELECT se lee directamente por su nombre
        row = bindings[0]
        info = {
            "nombre":  row["nombre"]["value"],
            "tipo":    row["tipo"]["value"],
            "semieje": row["semieje"]["value"],
            "periodo": row["periodo"]["value"],
            "afelio": row["afelio"]["value"],
            "perihelio": row["perihelio"]["value"],
            "excentricidad": row["excentricidad"]["value"],
            "inclinacionDeg": row["inclinacionDeg"]["value"],
            "periapsis": row["periapsis"]["value"],
            "anomaliaMediaDeg": row["anomalia"]["value"]
        }
        images = [row["imagenes"]["value"] for row in bindings]
        return {"name": name, "info": info, "images":images}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/grafo")
def get_grafo():
    query = """
        PREFIX sol: <http://ejemplo.org/sistema-solar#>
        SELECT ?origen ?tipo_origen ?destino ?tipo_destino ?relacion
        WHERE {
          {
            ?p a sol:Planeta ;
               sol:nombre ?origen ;
               sol:tieneSatelite ?s .
            ?s sol:nombre ?destino .
            BIND("Planeta"       AS ?tipo_origen)
            BIND("Satelite"      AS ?tipo_destino)
            BIND("tieneSatelite" AS ?relacion)
          } UNION {
            ?p a sol:Planeta ;
               sol:nombre ?origen ;
               sol:orbitaAlrededorDe ?estrella .
            ?estrella sol:nombre ?destino .
            BIND("Planeta"          AS ?tipo_origen)
            BIND("Sol"              AS ?tipo_destino)
            BIND("orbitaAlrededorDe" AS ?relacion)
          }
        }
    """
    sparql = config_request(query)
    try:
        results = sparql.query().convert()
        nodos_map = {}
        enlaces   = []
        for r in results["results"]["bindings"]:
            origen       = r["origen"]["value"]
            destino      = r["destino"]["value"]
            tipo_origen  = r["tipo_origen"]["value"]
            tipo_destino = r["tipo_destino"]["value"]
            relacion     = r["relacion"]["value"]
            nodos_map[origen]  = tipo_origen
            nodos_map[destino] = tipo_destino
            enlaces.append({ "source": origen, "target": destino, "label": relacion })
        nodos = [{ "id": n, "type": t } for n, t in nodos_map.items()]
        return { "nodes": nodos, "links": enlaces }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


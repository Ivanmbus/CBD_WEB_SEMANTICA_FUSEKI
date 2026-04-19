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

FUSEKI_URL = "http://localhost:3030/miDataset/query"

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
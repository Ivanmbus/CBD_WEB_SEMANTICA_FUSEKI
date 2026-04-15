#!/bin/sh

echo "Esperando Fuseki (ping)..."

until curl -s http://fuseki:3030/$/ping > /dev/null; do
  echo "Fuseki no listo aún..."
  sleep 2
done

echo "Fuseki listo ✔"

echo "Creando dataset..."

echo "Creando dataset..."

curl -X POST \
  --data-urlencode "dbName=ds" \
  --data-urlencode "dbType=tdb2" \
  http://fuseki:3030/\$/datasets

FUSEKI_URL="http://fuseki:3030/ds"

echo "Esperando dataset..."

until curl -s "$FUSEKI_URL" > /dev/null; do
  sleep 2
done

echo "Cargando schema..."

curl -X POST \
  -H "Content-Type: text/turtle" \
  --data-binary @/staging/schema.ttl \
  "$FUSEKI_URL/data?graph=http://ejemplo.org/schema"

echo "Cargando data..."

curl -X POST \
  -H "Content-Type: text/turtle" \
  --data-binary @/staging/data.ttl \
  "$FUSEKI_URL/data"

echo "OK"
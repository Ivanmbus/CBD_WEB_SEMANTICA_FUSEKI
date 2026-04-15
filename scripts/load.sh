#!/bin/sh

FUSEKI_URL="http://fuseki:3030/ds"

echo "Esperando a Fuseki..."

until curl -s "$FUSEKI_URL" > /dev/null; do
  sleep 2
done

echo "Fuseki listo"

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

echo "Carga completada"
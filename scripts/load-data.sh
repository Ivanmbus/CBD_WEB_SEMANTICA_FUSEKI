#!/bin/sh
apk add --no-cache curl > /dev/null 2>&1

sleep 5

echo "Esperando a que Fuseki arranque..."
until curl -sf http://fuseki:3030/$/ping > /dev/null; do
  sleep 2
done

echo "Limpiando datos anteriores..."
curl -u admin:admin123 -X DELETE "http://fuseki:3030/miDataset/data?default"

echo "Cargando schema..."
curl -u admin:admin123 -X POST http://fuseki:3030/miDataset/data \
     -H 'Content-Type: text/turtle' \
     --data-binary @/data/schema_horizons.ttl

echo "Cargando datos..."
curl -u admin:admin123 -X POST http://fuseki:3030/miDataset/data \
     -H 'Content-Type: text/turtle' \
     --data-binary @/data/data_horizons.ttl

echo "Listo."
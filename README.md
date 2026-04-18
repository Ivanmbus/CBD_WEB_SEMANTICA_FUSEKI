# CBD_WEB_SEMANTICA_FUSEKI

Cambios realizados Iván 18/04:

## Schema.ttl: 
[ELIMINADO] sol:diametroKm → redundante con radioMedioKm (diametro = radio * 2), Calcúlalo en consultas SPARQL con: BIND(?radioMedioKm * 2 AS ?diametro)
[CORREGIDO] Renombrado de temperaturaMediaC a temperaturaMediaK La API devuelve la temperatura en Kelvin, no en Celsius
[AÑADIDO] Propiedades de descubrimiento, necesarias para consultas históricas
[ELIMINADO] sol:argumentoPerihelioDeg → duplicado de argumentoPeriapsisDeg
El argumento del perihelio ES el argumento del periapsis referido al Sol
import csv
import requests
from pathlib import Path
from datetime import date, timedelta
from io import StringIO

BASE_URL = "https://ssd.jpl.nasa.gov/api/horizons.api"

NASA_URL_IMAGE_SEARCH = "https://images-api.nasa.gov/search"

PLANETS = {
    "mercurio": {"id": "199", "nombre": "Mercurio", "en": "Mercury", "tipo": "rocoso"},
    "venus":    {"id": "299", "nombre": "Venus",    "en": "Venus",   "tipo": "rocoso"},
    "tierra":   {"id": "399", "nombre": "Tierra",   "en": "Earth",   "tipo": "rocoso"},
    "marte":    {"id": "499", "nombre": "Marte",    "en": "Mars",    "tipo": "rocoso"},
    "jupiter":  {"id": "599", "nombre": "Júpiter",  "en": "Jupiter", "tipo": "gigante gaseoso"},
    "saturno":  {"id": "699", "nombre": "Saturno",  "en": "Saturn",  "tipo": "gigante gaseoso"},
    "urano":    {"id": "799", "nombre": "Urano",    "en": "Uranus",  "tipo": "gigante helado"},
    "neptuno":  {"id": "899", "nombre": "Neptuno",  "en": "Neptune", "tipo": "gigante helado"},
}

DWARF_PLANETS = {
    "ceres":    {"id": "1",      "nombre": "Ceres",    "en": "Ceres"},
    "pluton":   {"id": "999",    "nombre": "Plutón",   "en": "Pluto"},
    "haumea":   {"id": "136108", "nombre": "Haumea",   "en": "Haumea"},
    "makemake": {"id": "136472", "nombre": "Makemake", "en": "Makemake"},
    "eris":     {"id": "136199", "nombre": "Eris",     "en": "Eris"},
}

ASTEROIDS = {
    "pallas":  {"id": "2",      "nombre": "Pallas",  "en": "Pallas"},
    "juno":    {"id": "3",      "nombre": "Juno",    "en": "Juno"},
    "vesta":   {"id": "4",      "nombre": "Vesta",   "en": "Vesta"},
    "hygiea":  {"id": "10",     "nombre": "Hygiea",  "en": "Hygiea"},
    "psyche":  {"id": "16",     "nombre": "Psyche",  "en": "Psyche"},
    "eros":    {"id": "433",    "nombre": "Eros",    "en": "Eros"},
    "apophis": {"id": "99942",  "nombre": "Apophis", "en": "Apophis"},
    "bennu":   {"id": "101955", "nombre": "Bennu",   "en": "Bennu"},
    "ryugu":   {"id": "162173", "nombre": "Ryugu",   "en": "Ryugu"},
}

SATELLITES = {
    # Tierra
    "luna":      {"id": "301", "nombre": "Luna",      "en": "Moon",      "parent_slug": "tierra",  "center": "@399"},
    # Marte
    "fobos":     {"id": "401", "nombre": "Fobos",     "en": "Phobos",    "parent_slug": "marte",   "center": "@499"},
    "deimos":    {"id": "402", "nombre": "Deimos",    "en": "Deimos",    "parent_slug": "marte",   "center": "@499"},
    # Júpiter
    "io":        {"id": "501", "nombre": "Ío",        "en": "Io",        "parent_slug": "jupiter", "center": "@599"},
    "europa":    {"id": "502", "nombre": "Europa",    "en": "Europa",    "parent_slug": "jupiter", "center": "@599"},
    "ganimedes": {"id": "503", "nombre": "Ganímedes", "en": "Ganymede",  "parent_slug": "jupiter", "center": "@599"},
    "calisto":   {"id": "504", "nombre": "Calisto",   "en": "Callisto",  "parent_slug": "jupiter", "center": "@599"},
    # Saturno
    "mimas":     {"id": "601", "nombre": "Mimas",     "en": "Mimas",     "parent_slug": "saturno", "center": "@699"},
    "encelado":  {"id": "602", "nombre": "Encélado",  "en": "Enceladus", "parent_slug": "saturno", "center": "@699"},
    "tetis":     {"id": "603", "nombre": "Tetis",     "en": "Tethys",    "parent_slug": "saturno", "center": "@699"},
    "dione":     {"id": "604", "nombre": "Dione",     "en": "Dione",     "parent_slug": "saturno", "center": "@699"},
    "rea":       {"id": "605", "nombre": "Rea",       "en": "Rhea",      "parent_slug": "saturno", "center": "@699"},
    "titan":     {"id": "606", "nombre": "Titán",     "en": "Titan",     "parent_slug": "saturno", "center": "@699"},
    "japeto":    {"id": "608", "nombre": "Jápeto",    "en": "Iapetus",   "parent_slug": "saturno", "center": "@699"},
    # Urano
    "ariel":     {"id": "701", "nombre": "Ariel",     "en": "Ariel",     "parent_slug": "urano",   "center": "@799"},
    "umbriel":   {"id": "702", "nombre": "Umbriel",   "en": "Umbriel",   "parent_slug": "urano",   "center": "@799"},
    "titania":   {"id": "703", "nombre": "Titania",   "en": "Titania",   "parent_slug": "urano",   "center": "@799"},
    "oberon":    {"id": "704", "nombre": "Oberón",    "en": "Oberon",    "parent_slug": "urano",   "center": "@799"},
    "miranda":   {"id": "705", "nombre": "Miranda",   "en": "Miranda",   "parent_slug": "urano",   "center": "@799"},
    # Neptuno
    "triton":    {"id": "801", "nombre": "Tritón",    "en": "Triton",    "parent_slug": "neptuno", "center": "@899"},
    "nereida":   {"id": "802", "nombre": "Nereida",   "en": "Nereid",    "parent_slug": "neptuno", "center": "@899"},
}


# ── HELPERS ──────────────────────────────────────────────────────────────────

def to_float(value):
    value = value.strip()
    if not value or value.lower() == "n.a.":
        return None
    return float(value)


def decimal_literal(value):
    if value is None:
        return None
    return f'"{value}"^^xsd:decimal'

def url_literal(value):
    if not value:
        return None
    url_list = [f'"{value}"^^xsd:anyURI' for value in value if value]

    return url_list


# ── CONSULTA A HORIZONS ──────────────────────────────────────────────────────

def horizons_elements(command: str, center: str, out_units: str) -> dict:
    start = date.today().isoformat()
    stop = (date.today() + timedelta(days=1)).isoformat()

    params = {
        "format": "json",
        "COMMAND": f"'{command}'",
        "OBJ_DATA": "YES",
        "MAKE_EPHEM": "YES",
        "EPHEM_TYPE": "ELEMENTS",
        "CENTER": f"'{center}'",
        "START_TIME": f"'{start}'",
        "STOP_TIME": f"'{stop}'",
        "STEP_SIZE": "'1 d'",
        "OUT_UNITS": out_units,
        "CSV_FORMAT": "YES",
    }

    response = requests.get(BASE_URL, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()

    if "error" in data:
        raise RuntimeError(data["error"])

    result = data.get("result", "")

    if "$$SOE" not in result or "$$EOE" not in result:
        raise RuntimeError(
            f"Horizons no devolvió tabla válida para COMMAND={command}, CENTER={center}"
        )

    table = result.split("$$SOE")[1].split("$$EOE")[0].strip()
    first_line = table.splitlines()[0]

    reader = csv.reader(StringIO(first_line), skipinitialspace=True)
    row = next(reader)

    # Columnas CSV de Horizons ELEMENTS:
    # JDTDB, Calendar Date, EC, QR, IN, OM, W, Tp, N, MA, TA, A, AD, PR
    return {
        "excentricidad":              to_float(row[2]),
        "periapsis":                  to_float(row[3]),
        "inclinacionDeg":             to_float(row[4]),
        "longitudNodoAscendenteDeg":  to_float(row[5]),
        # [CORREGIDO] Mapeado a argumentoPeriapsisDeg (propiedad del esquema)
        # El original usaba argumentoPerihelioDeg que fue eliminado del esquema
        "argumentoPeriapsisDeg":      to_float(row[6]),
        "anomaliaMediaDeg":           to_float(row[9]),
        "semiejeMayor":               to_float(row[11]),
        "apoapsis":                   to_float(row[12]),
        "periodoOrbitalDias":         to_float(row[13]),
    }


# Consulta a Nasa Image and Video Library para obtener la URL de una imagen representativa de cada cuerpo.
def nasa_image(cuerpo_celeste: str) -> list:
    params = {
        "q": cuerpo_celeste,
        "media_type": "image",
    }
    response = requests.get(NASA_URL_IMAGE_SEARCH, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()

    items = data.get("collection", {}).get("items", [])
    if not items:
        return ""

    # Devolvemos la URL de la primera imagen encontrada
    return [
    item.get("links", [{}])[0].get("href", "")
    for item in items[:3]
    ]


# ── ESCRITURA DE ÓRBITA EN TTL ───────────────────────────────────────────────

def add_orbit_ttl(lines, orbit_uri, orbit, unit: str):
    """
    unit = 'AU' para órbitas heliocéntricas (planetas, planetas enanos, asteroides).
    unit = 'KM' para órbitas planetocéntricas (satélites).

    [CORREGIDO] Eliminadas fechaEpoch y epochJulianDate — no están en el esquema.
    [CORREGIDO] argumentoPerihelioDeg reemplazado por argumentoPeriapsisDeg en AU.
    """

    lines.append(f"{orbit_uri}")
    lines.append("    a sol:Orbita ;")

    if unit == "AU":
        props = [
            ("semiejeMayorAu",            "semiejeMayor",             "decimal"),
            ("perihelioAu",               "periapsis",                "decimal"),
            ("afelioAu",                  "apoapsis",                 "decimal"),
            ("excentricidad",             "excentricidad",            "decimal"),
            ("inclinacionDeg",            "inclinacionDeg",           "decimal"),
            ("longitudNodoAscendenteDeg", "longitudNodoAscendenteDeg","decimal"),
            # [CORREGIDO] argumentoPerihelioDeg → argumentoPeriapsisDeg
            ("argumentoPeriapsisDeg",     "argumentoPeriapsisDeg",    "decimal"),
            ("anomaliaMediaDeg",          "anomaliaMediaDeg",         "decimal"),
            ("periodoOrbitalDias",        "periodoOrbitalDias",       "decimal"),
        ]
    else:
        props = [
            ("semiejeMayorKm",            "semiejeMayor",             "decimal"),
            ("periapsisKm",               "periapsis",                "decimal"),
            ("apoapsisKm",                "apoapsis",                 "decimal"),
            ("excentricidad",             "excentricidad",            "decimal"),
            ("inclinacionDeg",            "inclinacionDeg",           "decimal"),
            ("longitudNodoAscendenteDeg", "longitudNodoAscendenteDeg","decimal"),
            ("argumentoPeriapsisDeg",     "argumentoPeriapsisDeg",    "decimal"),
            ("anomaliaMediaDeg",          "anomaliaMediaDeg",         "decimal"),
            ("periodoOrbitalDias",        "periodoOrbitalDias",       "decimal"),
        ]

    prop_lines = []
    for ttl_prop, data_key, dtype in props:
        value = orbit.get(data_key)
        lit = decimal_literal(value)
        if lit is not None:
            prop_lines.append(f"    sol:{ttl_prop} {lit}")

    for i, line in enumerate(prop_lines):
        lines.append(line + (" ." if i == len(prop_lines) - 1 else " ;"))

    lines.append("")


# ── GENERADORES DE BLOQUES ───────────────────────────────────────────────────

def add_heliocentric_bodies(lines, title, bodies, rdf_class):
    """
    Genera cuerpos que orbitan el Sol: planetas enanos y asteroides.
    [CORREGIDO] horizonsId ya no incluye el ";" — se escribe el id limpio.
    """
    lines.extend([f"# ── {title} ", ""])

    for slug, info in bodies.items():
        print(f"  Consultando: {info['nombre']}...")
        orbit_uri = f"sol:orbita_{slug}"

        try:
            orbit = horizons_elements(command=info["id"], center="@10", out_units="AU-D")
        except Exception as e:
            print(f"  ERROR con {info['nombre']}: {e}")
            continue

        # Obtenemos las imágenes fuera del bloque de líneas para manejarlas con seguridad
        imagenes = url_literal(nasa_image(info["en"]))

        body_lines = [
            f"sol:{slug}",
            f"    a sol:{rdf_class} ;",
            f'    sol:nombre "{info["nombre"]}" ;',
            f'    sol:nombreIngles "{info["en"]}" ;',
            f'    sol:horizonsId "{info["id"]}" ;',
            "    sol:orbitaAlrededorDe sol:sol ;",
        ]

        # Añadimos solo las imágenes que existan, sin asumir que hay 3
        if imagenes:
            for imagen in imagenes:
                if imagen:
                    body_lines.append(f"    sol:imagenUrl {imagen} ;")

        body_lines.append(f"    sol:tieneOrbita {orbit_uri} .")
        body_lines.append("")

        lines.extend(body_lines)
        add_orbit_ttl(lines, orbit_uri, orbit, unit="AU")


# ── CONSTRUCCIÓN DEL TTL ─────────────────────────────────────────────────────

def build_ttl() -> str:
    lines = [
        "@prefix sol: <http://ejemplo.org/sistema-solar#> .",
        "@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .",
        "",
        "# Generado automáticamente desde NASA/JPL Horizons",
        "",
        "# ── ESTRELLA ────────────────────────────────────────────────",
        "",
        "sol:sol",
        "    a sol:Estrella ;",
        '    sol:nombre "Sol" ;',
        '    sol:nombreIngles "Sun" ;',
        '    sol:horizonsId "10" .',
        "",
    ]

    # ── PLANETAS ─────────────────────────────────────────────────────────────
    lines.extend(["# ── PLANETAS ────────────────────────────────────────────────", ""])

    for slug, info in PLANETS.items():
        print(f"  Consultando planeta: {info['nombre']}...")
        
        orbit_uri = f"sol:orbita_{slug}"

        try:
            orbit = horizons_elements(command=info["id"], center="@10", out_units="AU-D")
        except Exception as e:
            print(f"  ERROR con {info['nombre']}: {e}")
            continue

        # [CORREGIDO] Recopilamos los satélites de este planeta para añadir sol:tieneSatelite
        # El original no enlazaba los satélites desde el lado del planeta
        satelites_del_planeta = [
            f"sol:{s_slug}"
            for s_slug, s_info in SATELLITES.items()
            if s_info["parent_slug"] == slug
        ]

        imagen_planeta =  url_literal(nasa_image(info["en"]))

        body_lines = [
            f"sol:{slug}",
            "    a sol:Planeta ;",
            f'    sol:nombre "{info["nombre"]}" ;',
            f'    sol:nombreIngles "{info["en"]}" ;',
            f'    sol:horizonsId "{info["id"]}" ;',
            f'    sol:tipoPlaneta "{info["tipo"]}" ;',
            "    sol:orbitaAlrededorDe sol:sol ;",
        ]

        for imagen in imagen_planeta:
            if imagen:
                body_lines.append(f"    sol:imagenUrl {imagen} ;")

        # Añadir tieneSatelite si el planeta tiene lunas definidas
        for sat_uri in satelites_del_planeta:
            body_lines.append(f"    sol:tieneSatelite {sat_uri} ;")

        # Cerrar el bloque cambiando el último ";" por "."
        body_lines[-1] = body_lines[-1].rstrip(" ;") + " ;"
        body_lines.append(f"    sol:tieneOrbita {orbit_uri} .")

        lines.extend(body_lines)
        lines.append("")
        add_orbit_ttl(lines, orbit_uri, orbit, unit="AU")

    # ── PLANETAS ENANOS ───────────────────────────────────────────────────────
    add_heliocentric_bodies(
        lines=lines,
        title="PLANETAS ENANOS",
        bodies=DWARF_PLANETS,
        rdf_class="PlanetaEnano",
    )

    # ── ASTEROIDES ────────────────────────────────────────────────────────────
    add_heliocentric_bodies(
        lines=lines,
        title="ASTEROIDES",
        bodies=ASTEROIDS,
        rdf_class="Asteroide",
    )

    # ── SATÉLITES ─────────────────────────────────────────────────────────────
    # [CORREGIDO] Se eliminan las tripletas sol:tieneSatelite duplicadas desde aquí
    # porque ahora ya se generan en el bloque del planeta correspondiente
    lines.extend(["# ── SATÉLITES NATURALES ─────────────────────────────────────", ""])

    for slug, info in SATELLITES.items():
        print(f"  Consultando satélite: {info['nombre']}...")
        
        parent_uri = f"sol:{info['parent_slug']}"
        orbit_uri  = f"sol:orbita_{slug}"

        try:
            orbit = horizons_elements(
                command=info["id"],
                center=info["center"],
                out_units="KM-D",
            )
        except Exception as e:
            print(f"  ERROR con {info['nombre']}: {e}")
            continue

        imagen_satelite =  url_literal(nasa_image(info["en"]))

        body_lines = [
            f"sol:{slug}",
            "    a sol:Satelite ;",
            f'    sol:nombre "{info["nombre"]}" ;',
            f'    sol:nombreIngles "{info["en"]}" ;',
            f'    sol:horizonsId "{info["id"]}" ;',
            f"    sol:sateliteDe {parent_uri} ;",
            f"    sol:orbitaAlrededorDe {parent_uri} ;",
        ]

        for imagen in imagen_satelite:
            if imagen:
                body_lines.append(f"    sol:imagenUrl {imagen} ;")

        body_lines.append(f"    sol:tieneOrbita {orbit_uri} .")
        body_lines.append("")

        lines.extend(body_lines)
        add_orbit_ttl(lines, orbit_uri, orbit, unit="KM")

    return "\n".join(lines)


# ── MAIN ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Generando data_horizons.ttl desde NASA/JPL Horizons...\n")
    ttl = build_ttl()
    Path("data_horizons.ttl").write_text(ttl, encoding="utf-8")
    print("\nArchivo generado: data_horizons.ttl")
    imagen_Makemake =  nasa_image("Makemake")
    print(f"URL de imagen representativa de Makemake: {imagen_Makemake}")
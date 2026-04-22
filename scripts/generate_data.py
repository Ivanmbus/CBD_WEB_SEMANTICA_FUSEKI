import csv
import requests
from pathlib import Path
from datetime import date, timedelta
from io import StringIO
import time
import requests
from functools import lru_cache
import re as _re
from decimal import Decimal, InvalidOperation

_DATE_RE = _re.compile(r'^\d{4}-\d{2}-\d{2}$')


BASE_URL = "https://ssd.jpl.nasa.gov/api/horizons.api"

NASA_URL_IMAGE_SEARCH = "https://images-api.nasa.gov/search"

WIKIDATA_API = "https://www.wikidata.org/w/api.php"

WIKIDATA_SPARQL_URL = "https://query.wikidata.org/sparql"

CONSULTA_FECHA = "2026-04-19"

CONSULTA_FECHA_FIN = "2026-04-20"

# None = todos los satélites
# Ejemplos:
# {"jupiter"}
# {"saturno", "urano"}
# {"pluton"}
GENERAR_SATELITES = True
SATELLITES_PLANETAS_ACTIVOS = None
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
    "ceres":    {"id": "1;",      "nombre": "Ceres",    "en": "Ceres"},
    "pluton":   {"id": "999",    "nombre": "Plutón",   "en": "Pluto"},
    "haumea":   {"id": "136108;", "nombre": "Haumea",   "en": "Haumea"},
    "makemake": {"id": "136472;", "nombre": "Makemake", "en": "Makemake"},
    "eris":     {"id": "136199;", "nombre": "Eris",     "en": "Eris"},
}

ASTEROIDS = {
    "pallas":  {"id": "2;",      "nombre": "Pallas",  "en": "Pallas"},
    "juno":    {"id": "3;",      "nombre": "Juno",    "en": "Juno"},
    "vesta":   {"id": "4;",      "nombre": "Vesta",   "en": "Vesta"},
    "hygiea":  {"id": "10;",     "nombre": "Hygiea",  "en": "Hygiea"},
    "psyche":  {"id": "16;",     "nombre": "Psyche",  "en": "Psyche"},
    "eros":    {"id": "433;",    "nombre": "Eros",    "en": "Eros"},
    "apophis": {"id": "99942;",  "nombre": "Apophis", "en": "Apophis"},
    "bennu":   {"id": "101955;", "nombre": "Bennu",   "en": "Bennu"},
    "ryugu":   {"id": "162173;", "nombre": "Ryugu",   "en": "Ryugu"},
}

SATELLITES = {
    # Tierra
    "luna":      {"id": "301", "nombre": "Luna",      "en": "Moon",      "parent_slug": "tierra",  "center": "@399"},

    # Marte
    "fobos":     {"id": "401", "nombre": "Fobos",     "en": "Phobos",    "parent_slug": "marte",   "center": "@499"},
    "deimos":    {"id": "402", "nombre": "Deimos",    "en": "Deimos",    "parent_slug": "marte",   "center": "@499"},

    # Júpiter
    "io":         {"id": "501",   "nombre": "Ío",           "en": "Io",           "parent_slug": "jupiter", "center": "@599"},
    "europa":     {"id": "502",   "nombre": "Europa",       "en": "Europa",       "parent_slug": "jupiter", "center": "@599"},
    "ganimedes":  {"id": "503",   "nombre": "Ganímedes",    "en": "Ganymede",     "parent_slug": "jupiter", "center": "@599"},
    "calisto":    {"id": "504",   "nombre": "Calisto",      "en": "Callisto",     "parent_slug": "jupiter", "center": "@599"},
    "amaltea":    {"id": "505",   "nombre": "Amaltea",      "en": "Amalthea",     "parent_slug": "jupiter", "center": "@599"},
    "himalia":    {"id": "506",   "nombre": "Himalia",      "en": "Himalia",      "parent_slug": "jupiter", "center": "@599"},
    "elara":      {"id": "507",   "nombre": "Elara",        "en": "Elara",        "parent_slug": "jupiter", "center": "@599"},
    "pasifae":    {"id": "508",   "nombre": "Pasífae",      "en": "Pasiphae",     "parent_slug": "jupiter", "center": "@599"},
    "sinope":     {"id": "509",   "nombre": "Sinope",       "en": "Sinope",       "parent_slug": "jupiter", "center": "@599"},
    "lisitea":    {"id": "510",   "nombre": "Lisitea",      "en": "Lysithea",     "parent_slug": "jupiter", "center": "@599"},
    "carme":      {"id": "511",   "nombre": "Carme",        "en": "Carme",        "parent_slug": "jupiter", "center": "@599"},
    "ananke":     {"id": "512",   "nombre": "Ananké",       "en": "Ananke",       "parent_slug": "jupiter", "center": "@599"},
    "leda":       {"id": "513",   "nombre": "Leda",         "en": "Leda",         "parent_slug": "jupiter", "center": "@599"},
    "tebe":       {"id": "514",   "nombre": "Tebe",         "en": "Thebe",        "parent_slug": "jupiter", "center": "@599"},
    "adrastea":   {"id": "515",   "nombre": "Adrastea",     "en": "Adrastea",     "parent_slug": "jupiter", "center": "@599"},
    "metis":      {"id": "516",   "nombre": "Metis",        "en": "Metis",        "parent_slug": "jupiter", "center": "@599"},
    "callirrhoe": {"id": "517",   "nombre": "Callirrhoe",   "en": "Callirrhoe",   "parent_slug": "jupiter", "center": "@599", "designacion": "S/1999 J 1"},
    "themisto":   {"id": "518",   "nombre": "Themisto",     "en": "Themisto",     "parent_slug": "jupiter", "center": "@599", "designacion": "S/1975 J 1"},
    "megaclite":  {"id": "519",   "nombre": "Megaclite",    "en": "Megaclite",    "parent_slug": "jupiter", "center": "@599", "designacion": "S/2000 J 8"},
    "taygete":    {"id": "520",   "nombre": "Taigete",      "en": "Taygete",      "parent_slug": "jupiter", "center": "@599", "designacion": "S/2000 J 9"},
    "chaldene":   {"id": "521",   "nombre": "Chaldene",     "en": "Chaldene",     "parent_slug": "jupiter", "center": "@599", "designacion": "S/2000 J 10"},
    "harpalyke":  {"id": "522",   "nombre": "Harpalyke",    "en": "Harpalyke",    "parent_slug": "jupiter", "center": "@599", "designacion": "S/2000 J 5"},
    "kalyke":     {"id": "523",   "nombre": "Kalyke",       "en": "Kalyke",       "parent_slug": "jupiter", "center": "@599", "designacion": "S/2000 J 2"},
    "iocaste":    {"id": "524",   "nombre": "Iocaste",      "en": "Iocaste",      "parent_slug": "jupiter", "center": "@599", "designacion": "S/2000 J 3"},
    "erinome":    {"id": "525",   "nombre": "Erínome",      "en": "Erinome",      "parent_slug": "jupiter", "center": "@599", "designacion": "S/2000 J 4"},
    "isonoe":     {"id": "526",   "nombre": "Isónoe",       "en": "Isonoe",       "parent_slug": "jupiter", "center": "@599", "designacion": "S/2000 J 6"},
    "praxidike":  {"id": "527",   "nombre": "Praxídike",    "en": "Praxidike",    "parent_slug": "jupiter", "center": "@599", "designacion": "S/2000 J 7"},
    "autonoe":    {"id": "528",   "nombre": "Autónoe",      "en": "Autonoe",      "parent_slug": "jupiter", "center": "@599", "designacion": "S/2001 J 1"},
    "thyone":     {"id": "529",   "nombre": "Tíone",        "en": "Thyone",       "parent_slug": "jupiter", "center": "@599", "designacion": "S/2001 J 2"},
    "hermippe":   {"id": "530",   "nombre": "Hermipe",      "en": "Hermippe",     "parent_slug": "jupiter", "center": "@599", "designacion": "S/2001 J 3"},
    "aitne":      {"id": "531",   "nombre": "Aitne",        "en": "Aitne",        "parent_slug": "jupiter", "center": "@599", "designacion": "S/2001 J 11"},
    "eurydome":   {"id": "532",   "nombre": "Eurydome",     "en": "Eurydome",     "parent_slug": "jupiter", "center": "@599", "designacion": "S/2001 J 4"},
    "euanthe":    {"id": "533",   "nombre": "Euanthe",      "en": "Euanthe",      "parent_slug": "jupiter", "center": "@599", "designacion": "S/2001 J 7"},
    "euporie":    {"id": "534",   "nombre": "Euporie",      "en": "Euporie",      "parent_slug": "jupiter", "center": "@599", "designacion": "S/2001 J 10"},
    "orthosie":   {"id": "535",   "nombre": "Orthosie",     "en": "Orthosie",     "parent_slug": "jupiter", "center": "@599", "designacion": "S/2001 J 9"},
    "sponde":     {"id": "536",   "nombre": "Sponde",       "en": "Sponde",       "parent_slug": "jupiter", "center": "@599", "designacion": "S/2001 J 5"},
    "kale":       {"id": "537",   "nombre": "Kale",         "en": "Kale",         "parent_slug": "jupiter", "center": "@599", "designacion": "S/2001 J 8"},
    "pasithee":   {"id": "538",   "nombre": "Pasítee",      "en": "Pasithee",     "parent_slug": "jupiter", "center": "@599", "designacion": "S/2001 J 6"},
    "hegemone":   {"id": "539",   "nombre": "Hegemone",     "en": "Hegemone",     "parent_slug": "jupiter", "center": "@599", "designacion": "S/2003 J 8"},
    "mneme":      {"id": "540",   "nombre": "Mneme",        "en": "Mneme",        "parent_slug": "jupiter", "center": "@599", "designacion": "S/2003 J 21"},
    "aoede":      {"id": "541",   "nombre": "Aoede",        "en": "Aoede",        "parent_slug": "jupiter", "center": "@599", "designacion": "S/2003 J 7"},
    "thelxinoe":  {"id": "542",   "nombre": "Thelxínoe",    "en": "Thelxinoe",    "parent_slug": "jupiter", "center": "@599", "designacion": "S/2003 J 22"},
    "arche":      {"id": "543",   "nombre": "Arche",        "en": "Arche",        "parent_slug": "jupiter", "center": "@599", "designacion": "S/2002 J 1"},
    "kallichore": {"id": "544",   "nombre": "Kallichore",   "en": "Kallichore",   "parent_slug": "jupiter", "center": "@599", "designacion": "S/2003 J 11"},
    "helike":     {"id": "545",   "nombre": "Helike",       "en": "Helike",       "parent_slug": "jupiter", "center": "@599", "designacion": "S/2003 J 6"},
    "carpo":      {"id": "546",   "nombre": "Carpo",        "en": "Carpo",        "parent_slug": "jupiter", "center": "@599", "designacion": "S/2003 J 20"},
    "eukelade":   {"id": "547",   "nombre": "Eukelade",     "en": "Eukelade",     "parent_slug": "jupiter", "center": "@599", "designacion": "S/2003 J 1"},
    "cyllene":    {"id": "548",   "nombre": "Cyllene",      "en": "Cyllene",      "parent_slug": "jupiter", "center": "@599", "designacion": "S/2003 J 13"},
    "kore":       {"id": "549",   "nombre": "Kore",         "en": "Kore",         "parent_slug": "jupiter", "center": "@599", "designacion": "S/2003 J 14"},
    "herse":      {"id": "550",   "nombre": "Herse",        "en": "Herse",        "parent_slug": "jupiter", "center": "@599", "designacion": "S/2003 J 17"},
    "jupiter_li":   {"id": "551", "nombre": "S/2010 J 1",   "en": "S/2010 J 1",   "parent_slug": "jupiter", "center": "@599", "designacion": "S/2010 J 1"},
    "jupiter_lii":  {"id": "552", "nombre": "S/2010 J 2",   "en": "S/2010 J 2",   "parent_slug": "jupiter", "center": "@599", "designacion": "S/2010 J 2"},
    "dia":          {"id": "553", "nombre": "Dia",          "en": "Dia",          "parent_slug": "jupiter", "center": "@599", "designacion": "S/2000 J 11"},
    "jupiter_liv":  {"id": "554", "nombre": "S/2016 J 1",   "en": "S/2016 J 1",   "parent_slug": "jupiter", "center": "@599", "designacion": "S/2016 J 1"},
    "jupiter_lv":   {"id": "555", "nombre": "S/2003 J 18",  "en": "S/2003 J 18",  "parent_slug": "jupiter", "center": "@599", "designacion": "S/2003 J 18"},
    "jupiter_lvi":  {"id": "556", "nombre": "S/2011 J 2",   "en": "S/2011 J 2",   "parent_slug": "jupiter", "center": "@599", "designacion": "S/2011 J 2"},
    "eirene":       {"id": "557", "nombre": "Eirene",       "en": "Eirene",       "parent_slug": "jupiter", "center": "@599", "designacion": "S/2003 J 5"},
    "philophrosyne":{"id": "558", "nombre": "Philophrosyne","en": "Philophrosyne","parent_slug": "jupiter", "center": "@599", "designacion": "S/2003 J 15"},
    "jupiter_lix":  {"id": "559", "nombre": "S/2017 J 1",   "en": "S/2017 J 1",   "parent_slug": "jupiter", "center": "@599", "designacion": "S/2017 J 1"},
    "eupheme":      {"id": "560", "nombre": "Eupheme",      "en": "Eupheme",      "parent_slug": "jupiter", "center": "@599", "designacion": "S/2003 J 3"},
    "jupiter_lxi":  {"id": "561", "nombre": "S/2003 J 19",  "en": "S/2003 J 19",  "parent_slug": "jupiter", "center": "@599", "designacion": "S/2003 J 19"},
    "valetudo":     {"id": "562", "nombre": "Valetudo",     "en": "Valetudo",     "parent_slug": "jupiter", "center": "@599", "designacion": "S/2016 J 2"},
    "jupiter_lxiii":{"id": "563", "nombre": "S/2017 J 2",   "en": "S/2017 J 2",   "parent_slug": "jupiter", "center": "@599", "designacion": "S/2017 J 2"},
    "jupiter_lxiv": {"id": "564", "nombre": "S/2017 J 3",   "en": "S/2017 J 3",   "parent_slug": "jupiter", "center": "@599", "designacion": "S/2017 J 3"},
    "pandia":       {"id": "565", "nombre": "Pandia",       "en": "Pandia",       "parent_slug": "jupiter", "center": "@599", "designacion": "S/2017 J 4"},
    "jupiter_lxvi": {"id": "566", "nombre": "S/2017 J 5",   "en": "S/2017 J 5",   "parent_slug": "jupiter", "center": "@599", "designacion": "S/2017 J 5"},
    "jupiter_lxvii":{"id": "567", "nombre": "S/2017 J 6",   "en": "S/2017 J 6",   "parent_slug": "jupiter", "center": "@599", "designacion": "S/2017 J 6"},
    "jupiter_lxviii":{"id": "568","nombre": "S/2017 J 7",   "en": "S/2017 J 7",   "parent_slug": "jupiter", "center": "@599", "designacion": "S/2017 J 7"},
    "jupiter_lxix":{"id": "569",  "nombre": "S/2017 J 8",   "en": "S/2017 J 8",   "parent_slug": "jupiter", "center": "@599", "designacion": "S/2017 J 8"},
    "jupiter_lxx": {"id": "570",  "nombre": "S/2017 J 9",   "en": "S/2017 J 9",   "parent_slug": "jupiter", "center": "@599", "designacion": "S/2017 J 9"},
    "ersa":        {"id": "571",  "nombre": "Ersa",         "en": "Ersa",         "parent_slug": "jupiter", "center": "@599", "designacion": "S/2018 J 1"},
    "jupiter_lxxii":{"id": "572", "nombre": "S/2011 J 1",   "en": "S/2011 J 1",   "parent_slug": "jupiter", "center": "@599", "designacion": "S/2011 J 1"},
    "jupiter_s2003_j2":  {"id": "55501", "nombre": "S/2003 J 2",  "en": "S/2003 J 2",  "parent_slug": "jupiter", "center": "@599", "designacion": "S/2003 J 2"},
    "jupiter_s2003_j4":  {"id": "55502", "nombre": "S/2003 J 4",  "en": "S/2003 J 4",  "parent_slug": "jupiter", "center": "@599", "designacion": "S/2003 J 4"},
    "jupiter_s2003_j9":  {"id": "55503", "nombre": "S/2003 J 9",  "en": "S/2003 J 9",  "parent_slug": "jupiter", "center": "@599", "designacion": "S/2003 J 9"},
    "jupiter_s2003_j10": {"id": "55504", "nombre": "S/2003 J 10", "en": "S/2003 J 10", "parent_slug": "jupiter", "center": "@599", "designacion": "S/2003 J 10"},
    "jupiter_s2003_j12": {"id": "55505", "nombre": "S/2003 J 12", "en": "S/2003 J 12", "parent_slug": "jupiter", "center": "@599", "designacion": "S/2003 J 12"},
    "jupiter_s2003_j16": {"id": "55506", "nombre": "S/2003 J 16", "en": "S/2003 J 16", "parent_slug": "jupiter", "center": "@599", "designacion": "S/2003 J 16"},
    "jupiter_s2003_j23": {"id": "55507", "nombre": "S/2003 J 23", "en": "S/2003 J 23", "parent_slug": "jupiter", "center": "@599", "designacion": "S/2003 J 23"},
    "jupiter_s2003_j24": {"id": "55508", "nombre": "S/2003 J 24", "en": "S/2003 J 24", "parent_slug": "jupiter", "center": "@599", "designacion": "S/2003 J 24"},
    "jupiter_s2011_j3":  {"id": "55509", "nombre": "S/2011 J 3",  "en": "S/2011 J 3",  "parent_slug": "jupiter", "center": "@599", "designacion": "S/2011 J 3"},
    "jupiter_s2018_j2":  {"id": "55510", "nombre": "S/2018 J 2",  "en": "S/2018 J 2",  "parent_slug": "jupiter", "center": "@599", "designacion": "S/2018 J 2"},
    "jupiter_s2018_j3":  {"id": "55511", "nombre": "S/2018 J 3",  "en": "S/2018 J 3",  "parent_slug": "jupiter", "center": "@599", "designacion": "S/2018 J 3"},
    "jupiter_s2021_j1":  {"id": "55512", "nombre": "S/2021 J 1",  "en": "S/2021 J 1",  "parent_slug": "jupiter", "center": "@599", "designacion": "S/2021 J 1"},
    "jupiter_s2021_j2":  {"id": "55513", "nombre": "S/2021 J 2",  "en": "S/2021 J 2",  "parent_slug": "jupiter", "center": "@599", "designacion": "S/2021 J 2"},
    "jupiter_s2021_j3":  {"id": "55514", "nombre": "S/2021 J 3",  "en": "S/2021 J 3",  "parent_slug": "jupiter", "center": "@599", "designacion": "S/2021 J 3"},
    "jupiter_s2021_j4":  {"id": "55515", "nombre": "S/2021 J 4",  "en": "S/2021 J 4",  "parent_slug": "jupiter", "center": "@599", "designacion": "S/2021 J 4"},
    "jupiter_s2021_j5":  {"id": "55516", "nombre": "S/2021 J 5",  "en": "S/2021 J 5",  "parent_slug": "jupiter", "center": "@599", "designacion": "S/2021 J 5"},
    "jupiter_s2021_j6":  {"id": "55517", "nombre": "S/2021 J 6",  "en": "S/2021 J 6",  "parent_slug": "jupiter", "center": "@599", "designacion": "S/2021 J 6"},
    "jupiter_s2016_j3":  {"id": "55518", "nombre": "S/2016 J 3",  "en": "S/2016 J 3",  "parent_slug": "jupiter", "center": "@599", "designacion": "S/2016 J 3"},
    "jupiter_s2016_j4":  {"id": "55519", "nombre": "S/2016 J 4",  "en": "S/2016 J 4",  "parent_slug": "jupiter", "center": "@599", "designacion": "S/2016 J 4"},
    "jupiter_s2018_j4":  {"id": "55520", "nombre": "S/2018 J 4",  "en": "S/2018 J 4",  "parent_slug": "jupiter", "center": "@599", "designacion": "S/2018 J 4"},
    "jupiter_s2022_j1":  {"id": "55521", "nombre": "S/2022 J 1",  "en": "S/2022 J 1",  "parent_slug": "jupiter", "center": "@599", "designacion": "S/2022 J 1"},
    "jupiter_s2022_j2":  {"id": "55522", "nombre": "S/2022 J 2",  "en": "S/2022 J 2",  "parent_slug": "jupiter", "center": "@599", "designacion": "S/2022 J 2"},
    "jupiter_s2022_j3":  {"id": "55523", "nombre": "S/2022 J 3",  "en": "S/2022 J 3",  "parent_slug": "jupiter", "center": "@599", "designacion": "S/2022 J 3"},
    "jupiter_s2017_j10": {"id": "55525", "nombre": "S/2017 J 10", "en": "S/2017 J 10", "parent_slug": "jupiter", "center": "@599", "designacion": "S/2017 J 10"},
    "jupiter_s2017_j11": {"id": "55526", "nombre": "S/2017 J 11", "en": "S/2017 J 11", "parent_slug": "jupiter", "center": "@599", "designacion": "S/2017 J 11"},
    "jupiter_s2011_j4":  {"id": "55527", "nombre": "S/2011 J 4",  "en": "S/2011 J 4",  "parent_slug": "jupiter", "center": "@599", "designacion": "S/2011 J 4"},
    "jupiter_s2018_j5":  {"id": "55528", "nombre": "S/2018 J 5",  "en": "S/2018 J 5",  "parent_slug": "jupiter", "center": "@599", "designacion": "S/2018 J 5"},
    "jupiter_s2024_j1":  {"id": "55529", "nombre": "S/2024 J 1",  "en": "S/2024 J 1",  "parent_slug": "jupiter", "center": "@599", "designacion": "S/2024 J 1"},
    "jupiter_s2011_j5":  {"id": "55530", "nombre": "S/2011 J 5",  "en": "S/2011 J 5",  "parent_slug": "jupiter", "center": "@599", "designacion": "S/2011 J 5"},
    "jupiter_s2010_j3":  {"id": "55531", "nombre": "S/2010 J 3",  "en": "S/2010 J 3",  "parent_slug": "jupiter", "center": "@599", "designacion": "S/2010 J 3"},
    "jupiter_s2010_j4":  {"id": "55532", "nombre": "S/2010 J 4",  "en": "S/2010 J 4",  "parent_slug": "jupiter", "center": "@599", "designacion": "S/2010 J 4"},
    "jupiter_s2010_j5":  {"id": "55533", "nombre": "S/2010 J 5",  "en": "S/2010 J 5",  "parent_slug": "jupiter", "center": "@599", "designacion": "S/2010 J 5"},
    "jupiter_s2010_j6":  {"id": "55534", "nombre": "S/2010 J 6",  "en": "S/2010 J 6",  "parent_slug": "jupiter", "center": "@599", "designacion": "S/2010 J 6"},
    "jupiter_s2011_j6":  {"id": "55535", "nombre": "S/2011 J 6",  "en": "S/2011 J 6",  "parent_slug": "jupiter", "center": "@599", "designacion": "S/2011 J 6"},
    "jupiter_s2017_j12": {"id": "55536", "nombre": "S/2017 J 12", "en": "S/2017 J 12", "parent_slug": "jupiter", "center": "@599", "designacion": "S/2017 J 12"},
    "jupiter_s2017_j13": {"id": "55537", "nombre": "S/2017 J 13", "en": "S/2017 J 13", "parent_slug": "jupiter", "center": "@599", "designacion": "S/2017 J 13"},
    "jupiter_s2017_j14": {"id": "55538", "nombre": "S/2017 J 14", "en": "S/2017 J 14", "parent_slug": "jupiter", "center": "@599", "designacion": "S/2017 J 14"},
    "jupiter_s2017_j15": {"id": "55539", "nombre": "S/2017 J 15", "en": "S/2017 J 15", "parent_slug": "jupiter", "center": "@599", "designacion": "S/2017 J 15"},
    "jupiter_s2017_j16": {"id": "55540", "nombre": "S/2017 J 16", "en": "S/2017 J 16", "parent_slug": "jupiter", "center": "@599", "designacion": "S/2017 J 16"},
    "jupiter_s2017_j17": {"id": "55541", "nombre": "S/2017 J 17", "en": "S/2017 J 17", "parent_slug": "jupiter", "center": "@599", "designacion": "S/2017 J 17"},
    "jupiter_s2017_j18": {"id": "55542", "nombre": "S/2017 J 18", "en": "S/2017 J 18", "parent_slug": "jupiter", "center": "@599", "designacion": "S/2017 J 18"},
    "jupiter_s2021_j7":  {"id": "55543", "nombre": "S/2021 J 7",  "en": "S/2021 J 7",  "parent_slug": "jupiter", "center": "@599", "designacion": "S/2021 J 7"},
    "jupiter_s2021_j8":  {"id": "55544", "nombre": "S/2021 J 8",  "en": "S/2021 J 8",  "parent_slug": "jupiter", "center": "@599", "designacion": "S/2021 J 8"},

    # Saturno
    "mimas":       {"id": "601",   "nombre": "Mimas",        "en": "Mimas",        "parent_slug": "saturno", "center": "@699"},
    "encelado":    {"id": "602",   "nombre": "Encélado",     "en": "Enceladus",    "parent_slug": "saturno", "center": "@699"},
    "tetis":       {"id": "603",   "nombre": "Tetis",        "en": "Tethys",       "parent_slug": "saturno", "center": "@699"},
    "dione":       {"id": "604",   "nombre": "Dione",        "en": "Dione",        "parent_slug": "saturno", "center": "@699"},
    "rea":         {"id": "605",   "nombre": "Rea",          "en": "Rhea",         "parent_slug": "saturno", "center": "@699"},
    "titan":       {"id": "606",   "nombre": "Titán",        "en": "Titan",        "parent_slug": "saturno", "center": "@699"},
    "hiperion":    {"id": "607",   "nombre": "Hiperión",     "en": "Hyperion",     "parent_slug": "saturno", "center": "@699"},
    "japeto":      {"id": "608",   "nombre": "Jápeto",       "en": "Iapetus",      "parent_slug": "saturno", "center": "@699"},
    "febe":        {"id": "609",   "nombre": "Febe",         "en": "Phoebe",       "parent_slug": "saturno", "center": "@699"},
    "jano":        {"id": "610",   "nombre": "Jano",         "en": "Janus",        "parent_slug": "saturno", "center": "@699"},
    "epimeteo":    {"id": "611",   "nombre": "Epimeteo",     "en": "Epimetheus",   "parent_slug": "saturno", "center": "@699"},
    "helena":      {"id": "612",   "nombre": "Helena",       "en": "Helene",       "parent_slug": "saturno", "center": "@699"},
    "telesto":     {"id": "613",   "nombre": "Telesto",      "en": "Telesto",      "parent_slug": "saturno", "center": "@699"},
    "calipso":     {"id": "614",   "nombre": "Calipso",      "en": "Calypso",      "parent_slug": "saturno", "center": "@699"},
    "atlas":       {"id": "615",   "nombre": "Atlas",        "en": "Atlas",        "parent_slug": "saturno", "center": "@699"},
    "prometeo":    {"id": "616",   "nombre": "Prometeo",     "en": "Prometheus",   "parent_slug": "saturno", "center": "@699"},
    "pandora":     {"id": "617",   "nombre": "Pandora",      "en": "Pandora",      "parent_slug": "saturno", "center": "@699"},
    "pan":         {"id": "618",   "nombre": "Pan",          "en": "Pan",          "parent_slug": "saturno", "center": "@699"},
    "ymir":        {"id": "619",   "nombre": "Ymir",         "en": "Ymir",         "parent_slug": "saturno", "center": "@699", "designacion": "S/2000 S 1"},
    "paaliaq":     {"id": "620",   "nombre": "Paaliaq",      "en": "Paaliaq",      "parent_slug": "saturno", "center": "@699", "designacion": "S/2000 S 2"},
    "tarvos":      {"id": "621",   "nombre": "Tarvos",       "en": "Tarvos",       "parent_slug": "saturno", "center": "@699", "designacion": "S/2000 S 4"},
    "ijiraq":      {"id": "622",   "nombre": "Ijiraq",       "en": "Ijiraq",       "parent_slug": "saturno", "center": "@699", "designacion": "S/2000 S 6"},
    "suttungr":    {"id": "623",   "nombre": "Suttungr",     "en": "Suttungr",     "parent_slug": "saturno", "center": "@699", "designacion": "S/2000 S 12"},
    "kiviuq":      {"id": "624",   "nombre": "Kiviuq",       "en": "Kiviuq",       "parent_slug": "saturno", "center": "@699", "designacion": "S/2000 S 5"},
    "mundilfari":  {"id": "625",   "nombre": "Mundilfari",   "en": "Mundilfari",   "parent_slug": "saturno", "center": "@699", "designacion": "S/2000 S 9"},
    "albiorix":    {"id": "626",   "nombre": "Albiorix",     "en": "Albiorix",     "parent_slug": "saturno", "center": "@699", "designacion": "S/2000 S 11"},
    "skathi":      {"id": "627",   "nombre": "Skathi",       "en": "Skathi",       "parent_slug": "saturno", "center": "@699", "designacion": "S/2000 S 8"},
    "erriapus":    {"id": "628",   "nombre": "Erriapus",     "en": "Erriapus",     "parent_slug": "saturno", "center": "@699", "designacion": "S/2000 S 10"},
    "siarnaq":     {"id": "629",   "nombre": "Siarnaq",      "en": "Siarnaq",      "parent_slug": "saturno", "center": "@699", "designacion": "S/2000 S 3"},
    "thrymr":      {"id": "630",   "nombre": "Thrymr",       "en": "Thrymr",       "parent_slug": "saturno", "center": "@699", "designacion": "S/2000 S 7"},
    "narvi":       {"id": "631",   "nombre": "Narvi",        "en": "Narvi",        "parent_slug": "saturno", "center": "@699", "designacion": "S/2003 S 1"},
    "methone":     {"id": "632",   "nombre": "Methone",      "en": "Methone",      "parent_slug": "saturno", "center": "@699", "designacion": "S/2004 S 1"},
    "pallene":     {"id": "633",   "nombre": "Pallene",      "en": "Pallene",      "parent_slug": "saturno", "center": "@699", "designacion": "S/2004 S 2"},
    "polydeuces":  {"id": "634",   "nombre": "Polydeuces",   "en": "Polydeuces",   "parent_slug": "saturno", "center": "@699", "designacion": "S/2004 S 5"},
    "daphnis":     {"id": "635",   "nombre": "Daphnis",      "en": "Daphnis",      "parent_slug": "saturno", "center": "@699", "designacion": "S/2005 S 1"},
    "aegir":       {"id": "636",   "nombre": "Aegir",        "en": "Aegir",        "parent_slug": "saturno", "center": "@699", "designacion": "S/2004 S 10"},
    "bebhionn":    {"id": "637",   "nombre": "Bebhionn",     "en": "Bebhionn",     "parent_slug": "saturno", "center": "@699", "designacion": "S/2004 S 11"},
    "bergelmir":   {"id": "638",   "nombre": "Bergelmir",    "en": "Bergelmir",    "parent_slug": "saturno", "center": "@699", "designacion": "S/2004 S 15"},
    "bestla":      {"id": "639",   "nombre": "Bestla",       "en": "Bestla",       "parent_slug": "saturno", "center": "@699", "designacion": "S/2004 S 18"},
    "farbauti":    {"id": "640",   "nombre": "Farbauti",     "en": "Farbauti",     "parent_slug": "saturno", "center": "@699", "designacion": "S/2004 S 9"},
    "fenrir":      {"id": "641",   "nombre": "Fenrir",       "en": "Fenrir",       "parent_slug": "saturno", "center": "@699", "designacion": "S/2004 S 16"},
    "fornjot":     {"id": "642",   "nombre": "Fornjot",      "en": "Fornjot",      "parent_slug": "saturno", "center": "@699", "designacion": "S/2004 S 8"},
    "hati":        {"id": "643",   "nombre": "Hati",         "en": "Hati",         "parent_slug": "saturno", "center": "@699", "designacion": "S/2004 S 14"},
    "hyrrokkin":   {"id": "644",   "nombre": "Hyrrokkin",    "en": "Hyrrokkin",    "parent_slug": "saturno", "center": "@699", "designacion": "S/2004 S 19"},
    "kari":        {"id": "645",   "nombre": "Kari",         "en": "Kari",         "parent_slug": "saturno", "center": "@699", "designacion": "S/2006 S 2"},
    "loge":        {"id": "646",   "nombre": "Loge",         "en": "Loge",         "parent_slug": "saturno", "center": "@699", "designacion": "S/2006 S 5"},
    "skoll":       {"id": "647",   "nombre": "Skoll",        "en": "Skoll",        "parent_slug": "saturno", "center": "@699", "designacion": "S/2006 S 8"},
    "surtur":      {"id": "648",   "nombre": "Surtur",       "en": "Surtur",       "parent_slug": "saturno", "center": "@699", "designacion": "S/2006 S 7"},
    "anthe":       {"id": "649",   "nombre": "Anthe",        "en": "Anthe",        "parent_slug": "saturno", "center": "@699", "designacion": "S/2007 S 4"},
    "jarnsaxa":    {"id": "650",   "nombre": "Jarnsaxa",     "en": "Jarnsaxa",     "parent_slug": "saturno", "center": "@699", "designacion": "S/2006 S 6"},
    "greip":       {"id": "651",   "nombre": "Greip",        "en": "Greip",        "parent_slug": "saturno", "center": "@699", "designacion": "S/2006 S 4"},
    "tarqeq":      {"id": "652",   "nombre": "Tarqeq",       "en": "Tarqeq",       "parent_slug": "saturno", "center": "@699", "designacion": "S/2007 S 1"},
    "aegaeon":     {"id": "653",   "nombre": "Aegaeon",      "en": "Aegaeon",      "parent_slug": "saturno", "center": "@699", "designacion": "S/2008 S 1"},
    "gridr":       {"id": "654",   "nombre": "Gridr",        "en": "Gridr",        "parent_slug": "saturno", "center": "@699", "designacion": "S/2004 S 20"},
    "angrboda":    {"id": "655",   "nombre": "Angrboda",     "en": "Angrboda",     "parent_slug": "saturno", "center": "@699", "designacion": "S/2004 S 22"},
    "skrymir":     {"id": "656",   "nombre": "Skrymir",      "en": "Skrymir",      "parent_slug": "saturno", "center": "@699", "designacion": "S/2004 S 23"},
    "gerd":        {"id": "657",   "nombre": "Gerd",         "en": "Gerd",         "parent_slug": "saturno", "center": "@699", "designacion": "S/2004 S 25"},
    "saturno_s2004_s26": {"id": "658", "nombre": "S/2004 S 26", "en": "S/2004 S 26", "parent_slug": "saturno", "center": "@699", "designacion": "S/2004 S 26"},
    "eggther":     {"id": "659",   "nombre": "Eggther",      "en": "Eggther",      "parent_slug": "saturno", "center": "@699", "designacion": "S/2004 S 27"},
    "saturno_s2004_s29": {"id": "660", "nombre": "S/2004 S 29", "en": "S/2004 S 29", "parent_slug": "saturno", "center": "@699", "designacion": "S/2004 S 29"},
    "beli":        {"id": "661",   "nombre": "Beli",         "en": "Beli",         "parent_slug": "saturno", "center": "@699", "designacion": "S/2004 S 30"},
    "gunnlod":     {"id": "662",   "nombre": "Gunnlod",      "en": "Gunnlod",      "parent_slug": "saturno", "center": "@699", "designacion": "S/2004 S 32"},
    "thiazzi":     {"id": "663",   "nombre": "Thiazzi",      "en": "Thiazzi",      "parent_slug": "saturno", "center": "@699", "designacion": "S/2004 S 33"},
    "saturno_s2004_s34": {"id": "664", "nombre": "S/2004 S 34", "en": "S/2004 S 34", "parent_slug": "saturno", "center": "@699", "designacion": "S/2004 S 34"},
    "alvaldi":     {"id": "665",   "nombre": "Alvaldi",      "en": "Alvaldi",      "parent_slug": "saturno", "center": "@699", "designacion": "S/2004 S 35"},
    "geirrod":     {"id": "666",   "nombre": "Geirrod",      "en": "Geirrod",      "parent_slug": "saturno", "center": "@699", "designacion": "S/2004 S 38"},
    "saturno_s2004_s31": {"id": "65067", "nombre": "S/2004 S 31", "en": "S/2004 S 31", "parent_slug": "saturno", "center": "@699", "designacion": "S/2004 S 31"},
    "saturno_s2004_s24": {"id": "65070", "nombre": "S/2004 S 24", "en": "S/2004 S 24", "parent_slug": "saturno", "center": "@699", "designacion": "S/2004 S 24"},
    "saturno_s2004_s28": {"id": "65077", "nombre": "S/2004 S 28", "en": "S/2004 S 28", "parent_slug": "saturno", "center": "@699", "designacion": "S/2004 S 28"},
    "saturno_s2004_s21": {"id": "65079", "nombre": "S/2004 S 21", "en": "S/2004 S 21", "parent_slug": "saturno", "center": "@699", "designacion": "S/2004 S 21"},
    "saturno_s2004_s36": {"id": "65081", "nombre": "S/2004 S 36", "en": "S/2004 S 36", "parent_slug": "saturno", "center": "@699", "designacion": "S/2004 S 36"},
    "saturno_s2004_s37": {"id": "65082", "nombre": "S/2004 S 37", "en": "S/2004 S 37", "parent_slug": "saturno", "center": "@699", "designacion": "S/2004 S 37"},
    "saturno_s2004_s39": {"id": "65084", "nombre": "S/2004 S 39", "en": "S/2004 S 39", "parent_slug": "saturno", "center": "@699", "designacion": "S/2004 S 39"},
    "saturno_s2004_s7":  {"id": "65085", "nombre": "S/2004 S 7",  "en": "S/2004 S 7",  "parent_slug": "saturno", "center": "@699", "designacion": "S/2004 S 7"},
    "saturno_s2004_s12": {"id": "65086", "nombre": "S/2004 S 12", "en": "S/2004 S 12", "parent_slug": "saturno", "center": "@699", "designacion": "S/2004 S 12"},
    "saturno_s2004_s13": {"id": "65087", "nombre": "S/2004 S 13", "en": "S/2004 S 13", "parent_slug": "saturno", "center": "@699", "designacion": "S/2004 S 13"},
    "saturno_s2004_s17": {"id": "65088", "nombre": "S/2004 S 17", "en": "S/2004 S 17", "parent_slug": "saturno", "center": "@699", "designacion": "S/2004 S 17"},
    "saturno_s2006_s1":  {"id": "65089", "nombre": "S/2006 S 1",  "en": "S/2006 S 1",  "parent_slug": "saturno", "center": "@699", "designacion": "S/2006 S 1"},
    "saturno_s2006_s3":  {"id": "65090", "nombre": "S/2006 S 3",  "en": "S/2006 S 3",  "parent_slug": "saturno", "center": "@699", "designacion": "S/2006 S 3"},
    "saturno_s2007_s2":  {"id": "65091", "nombre": "S/2007 S 2",  "en": "S/2007 S 2",  "parent_slug": "saturno", "center": "@699", "designacion": "S/2007 S 2"},
    "saturno_s2007_s3":  {"id": "65092", "nombre": "S/2007 S 3",  "en": "S/2007 S 3",  "parent_slug": "saturno", "center": "@699", "designacion": "S/2007 S 3"},
    "saturno_s2019_s1":  {"id": "65093", "nombre": "S/2019 S 1",  "en": "S/2019 S 1",  "parent_slug": "saturno", "center": "@699", "designacion": "S/2019 S 1"},
    "saturno_s2019_s2":  {"id": "65094", "nombre": "S/2019 S 2",  "en": "S/2019 S 2",  "parent_slug": "saturno", "center": "@699", "designacion": "S/2019 S 2"},
    "saturno_s2019_s3":  {"id": "65095", "nombre": "S/2019 S 3",  "en": "S/2019 S 3",  "parent_slug": "saturno", "center": "@699", "designacion": "S/2019 S 3"},
    "saturno_s2020_s1":  {"id": "65096", "nombre": "S/2020 S 1",  "en": "S/2020 S 1",  "parent_slug": "saturno", "center": "@699", "designacion": "S/2020 S 1"},
    "saturno_s2020_s2":  {"id": "65097", "nombre": "S/2020 S 2",  "en": "S/2020 S 2",  "parent_slug": "saturno", "center": "@699", "designacion": "S/2020 S 2"},
    "saturno_s2004_s40": {"id": "65098", "nombre": "S/2004 S 40", "en": "S/2004 S 40", "parent_slug": "saturno", "center": "@699", "designacion": "S/2004 S 40"},
    "saturno_s2006_s9":  {"id": "65100", "nombre": "S/2006 S 9",  "en": "S/2006 S 9",  "parent_slug": "saturno", "center": "@699", "designacion": "S/2006 S 9"},
    "saturno_s2007_s5":  {"id": "65101", "nombre": "S/2007 S 5",  "en": "S/2007 S 5",  "parent_slug": "saturno", "center": "@699", "designacion": "S/2007 S 5"},
    "saturno_s2020_s3":  {"id": "65102", "nombre": "S/2020 S 3",  "en": "S/2020 S 3",  "parent_slug": "saturno", "center": "@699", "designacion": "S/2020 S 3"},
    "saturno_s2019_s4":  {"id": "65103", "nombre": "S/2019 S 4",  "en": "S/2019 S 4",  "parent_slug": "saturno", "center": "@699", "designacion": "S/2019 S 4"},
    "saturno_s2004_s41": {"id": "65104", "nombre": "S/2004 S 41", "en": "S/2004 S 41", "parent_slug": "saturno", "center": "@699", "designacion": "S/2004 S 41"},
    "saturno_s2020_s4":  {"id": "65105", "nombre": "S/2020 S 4",  "en": "S/2020 S 4",  "parent_slug": "saturno", "center": "@699", "designacion": "S/2020 S 4"},
    "saturno_s2020_s5":  {"id": "65106", "nombre": "S/2020 S 5",  "en": "S/2020 S 5",  "parent_slug": "saturno", "center": "@699", "designacion": "S/2020 S 5"},
    "saturno_s2007_s6":  {"id": "65107", "nombre": "S/2007 S 6",  "en": "S/2007 S 6",  "parent_slug": "saturno", "center": "@699", "designacion": "S/2007 S 6"},
    "saturno_s2004_s42": {"id": "65108", "nombre": "S/2004 S 42", "en": "S/2004 S 42", "parent_slug": "saturno", "center": "@699", "designacion": "S/2004 S 42"},
    "saturno_s2006_s10": {"id": "65109", "nombre": "S/2006 S 10", "en": "S/2006 S 10", "parent_slug": "saturno", "center": "@699", "designacion": "S/2006 S 10"},
    "saturno_s2019_s5":  {"id": "65110", "nombre": "S/2019 S 5",  "en": "S/2019 S 5",  "parent_slug": "saturno", "center": "@699", "designacion": "S/2019 S 5"},
    "saturno_s2004_s43": {"id": "65111", "nombre": "S/2004 S 43", "en": "S/2004 S 43", "parent_slug": "saturno", "center": "@699", "designacion": "S/2004 S 43"},
    "saturno_s2004_s44": {"id": "65112", "nombre": "S/2004 S 44", "en": "S/2004 S 44", "parent_slug": "saturno", "center": "@699", "designacion": "S/2004 S 44"},
    "saturno_s2004_s45": {"id": "65113", "nombre": "S/2004 S 45", "en": "S/2004 S 45", "parent_slug": "saturno", "center": "@699", "designacion": "S/2004 S 45"},
    "saturno_s2006_s11": {"id": "65114", "nombre": "S/2006 S 11", "en": "S/2006 S 11", "parent_slug": "saturno", "center": "@699", "designacion": "S/2006 S 11"},
    "saturno_s2006_s12": {"id": "65115", "nombre": "S/2006 S 12", "en": "S/2006 S 12", "parent_slug": "saturno", "center": "@699", "designacion": "S/2006 S 12"},
    "saturno_s2019_s6":  {"id": "65116", "nombre": "S/2019 S 6",  "en": "S/2019 S 6",  "parent_slug": "saturno", "center": "@699", "designacion": "S/2019 S 6"},
    "saturno_s2006_s13": {"id": "65117", "nombre": "S/2006 S 13", "en": "S/2006 S 13", "parent_slug": "saturno", "center": "@699", "designacion": "S/2006 S 13"},
    "saturno_s2019_s7":  {"id": "65118", "nombre": "S/2019 S 7",  "en": "S/2019 S 7",  "parent_slug": "saturno", "center": "@699", "designacion": "S/2019 S 7"},
    "saturno_s2019_s8":  {"id": "65119", "nombre": "S/2019 S 8",  "en": "S/2019 S 8",  "parent_slug": "saturno", "center": "@699", "designacion": "S/2019 S 8"},
    "saturno_s2019_s9":  {"id": "65120", "nombre": "S/2019 S 9",  "en": "S/2019 S 9",  "parent_slug": "saturno", "center": "@699", "designacion": "S/2019 S 9"},
    "saturno_s2004_s46": {"id": "65121", "nombre": "S/2004 S 46", "en": "S/2004 S 46", "parent_slug": "saturno", "center": "@699", "designacion": "S/2004 S 46"},
    "saturno_s2019_s10": {"id": "65122", "nombre": "S/2019 S 10", "en": "S/2019 S 10", "parent_slug": "saturno", "center": "@699", "designacion": "S/2019 S 10"},
    "saturno_s2004_s47": {"id": "65123", "nombre": "S/2004 S 47", "en": "S/2004 S 47", "parent_slug": "saturno", "center": "@699", "designacion": "S/2004 S 47"},
    "saturno_s2019_s11": {"id": "65124", "nombre": "S/2019 S 11", "en": "S/2019 S 11", "parent_slug": "saturno", "center": "@699", "designacion": "S/2019 S 11"},
    "saturno_s2006_s14": {"id": "65125", "nombre": "S/2006 S 14", "en": "S/2006 S 14", "parent_slug": "saturno", "center": "@699", "designacion": "S/2006 S 14"},
    "saturno_s2019_s12": {"id": "65126", "nombre": "S/2019 S 12", "en": "S/2019 S 12", "parent_slug": "saturno", "center": "@699", "designacion": "S/2019 S 12"},
    "saturno_s2020_s6":  {"id": "65127", "nombre": "S/2020 S 6",  "en": "S/2020 S 6",  "parent_slug": "saturno", "center": "@699", "designacion": "S/2020 S 6"},
    "saturno_s2019_s13": {"id": "65128", "nombre": "S/2019 S 13", "en": "S/2019 S 13", "parent_slug": "saturno", "center": "@699", "designacion": "S/2019 S 13"},
    "saturno_s2005_s4":  {"id": "65129", "nombre": "S/2005 S 4",  "en": "S/2005 S 4",  "parent_slug": "saturno", "center": "@699", "designacion": "S/2005 S 4"},
    "saturno_s2007_s7":  {"id": "65130", "nombre": "S/2007 S 7",  "en": "S/2007 S 7",  "parent_slug": "saturno", "center": "@699", "designacion": "S/2007 S 7"},
    "saturno_s2007_s8":  {"id": "65131", "nombre": "S/2007 S 8",  "en": "S/2007 S 8",  "parent_slug": "saturno", "center": "@699", "designacion": "S/2007 S 8"},
    "saturno_s2020_s7":  {"id": "65132", "nombre": "S/2020 S 7",  "en": "S/2020 S 7",  "parent_slug": "saturno", "center": "@699", "designacion": "S/2020 S 7"},
    "saturno_s2019_s14": {"id": "65133", "nombre": "S/2019 S 14", "en": "S/2019 S 14", "parent_slug": "saturno", "center": "@699", "designacion": "S/2019 S 14"},
    "saturno_s2019_s15": {"id": "65134", "nombre": "S/2019 S 15", "en": "S/2019 S 15", "parent_slug": "saturno", "center": "@699", "designacion": "S/2019 S 15"},
    "saturno_s2005_s5":  {"id": "65135", "nombre": "S/2005 S 5",  "en": "S/2005 S 5",  "parent_slug": "saturno", "center": "@699", "designacion": "S/2005 S 5"},
    "saturno_s2006_s15": {"id": "65136", "nombre": "S/2006 S 15", "en": "S/2006 S 15", "parent_slug": "saturno", "center": "@699", "designacion": "S/2006 S 15"},
    "saturno_s2006_s16": {"id": "65137", "nombre": "S/2006 S 16", "en": "S/2006 S 16", "parent_slug": "saturno", "center": "@699", "designacion": "S/2006 S 16"},
    "saturno_s2006_s17": {"id": "65138", "nombre": "S/2006 S 17", "en": "S/2006 S 17", "parent_slug": "saturno", "center": "@699", "designacion": "S/2006 S 17"},
    "saturno_s2004_s48": {"id": "65139", "nombre": "S/2004 S 48", "en": "S/2004 S 48", "parent_slug": "saturno", "center": "@699", "designacion": "S/2004 S 48"},
    "saturno_s2020_s8":  {"id": "65140", "nombre": "S/2020 S 8",  "en": "S/2020 S 8",  "parent_slug": "saturno", "center": "@699", "designacion": "S/2020 S 8"},
    "saturno_s2004_s49": {"id": "65141", "nombre": "S/2004 S 49", "en": "S/2004 S 49", "parent_slug": "saturno", "center": "@699", "designacion": "S/2004 S 49"},
    "saturno_s2004_s50": {"id": "65142", "nombre": "S/2004 S 50", "en": "S/2004 S 50", "parent_slug": "saturno", "center": "@699", "designacion": "S/2004 S 50"},
    "saturno_s2006_s18": {"id": "65143", "nombre": "S/2006 S 18", "en": "S/2006 S 18", "parent_slug": "saturno", "center": "@699", "designacion": "S/2006 S 18"},
    "saturno_s2019_s16": {"id": "65144", "nombre": "S/2019 S 16", "en": "S/2019 S 16", "parent_slug": "saturno", "center": "@699", "designacion": "S/2019 S 16"},
    "saturno_s2019_s17": {"id": "65145", "nombre": "S/2019 S 17", "en": "S/2019 S 17", "parent_slug": "saturno", "center": "@699", "designacion": "S/2019 S 17"},
    "saturno_s2019_s18": {"id": "65146", "nombre": "S/2019 S 18", "en": "S/2019 S 18", "parent_slug": "saturno", "center": "@699", "designacion": "S/2019 S 18"},
    "saturno_s2019_s19": {"id": "65147", "nombre": "S/2019 S 19", "en": "S/2019 S 19", "parent_slug": "saturno", "center": "@699", "designacion": "S/2019 S 19"},
    "saturno_s2019_s20": {"id": "65148", "nombre": "S/2019 S 20", "en": "S/2019 S 20", "parent_slug": "saturno", "center": "@699", "designacion": "S/2019 S 20"},
    "saturno_s2006_s19": {"id": "65149", "nombre": "S/2006 S 19", "en": "S/2006 S 19", "parent_slug": "saturno", "center": "@699", "designacion": "S/2006 S 19"},
    "saturno_s2004_s51": {"id": "65150", "nombre": "S/2004 S 51", "en": "S/2004 S 51", "parent_slug": "saturno", "center": "@699", "designacion": "S/2004 S 51"},
    "saturno_s2020_s9":  {"id": "65151", "nombre": "S/2020 S 9",  "en": "S/2020 S 9",  "parent_slug": "saturno", "center": "@699", "designacion": "S/2020 S 9"},
    "saturno_s2004_s52": {"id": "65152", "nombre": "S/2004 S 52", "en": "S/2004 S 52", "parent_slug": "saturno", "center": "@699", "designacion": "S/2004 S 52"},
    "saturno_s2007_s9":  {"id": "65153", "nombre": "S/2007 S 9",  "en": "S/2007 S 9",  "parent_slug": "saturno", "center": "@699", "designacion": "S/2007 S 9"},
    "saturno_s2004_s53": {"id": "65154", "nombre": "S/2004 S 53", "en": "S/2004 S 53", "parent_slug": "saturno", "center": "@699", "designacion": "S/2004 S 53"},
    "saturno_s2020_s10": {"id": "65155", "nombre": "S/2020 S 10", "en": "S/2020 S 10", "parent_slug": "saturno", "center": "@699", "designacion": "S/2020 S 10"},
    "saturno_s2019_s21": {"id": "65156", "nombre": "S/2019 S 21", "en": "S/2019 S 21", "parent_slug": "saturno", "center": "@699", "designacion": "S/2019 S 21"},
    "saturno_s2006_s20": {"id": "65157", "nombre": "S/2006 S 20", "en": "S/2006 S 20", "parent_slug": "saturno", "center": "@699", "designacion": "S/2006 S 20"},
    "saturno_s2004_s54": {"id": "65158", "nombre": "S/2004 S 54", "en": "S/2004 S 54", "parent_slug": "saturno", "center": "@699", "designacion": "S/2004 S 54"},
    "saturno_s2004_s55": {"id": "65159", "nombre": "S/2004 S 55", "en": "S/2004 S 55", "parent_slug": "saturno", "center": "@699", "designacion": "S/2004 S 55"},
    "saturno_s2004_s56": {"id": "65160", "nombre": "S/2004 S 56", "en": "S/2004 S 56", "parent_slug": "saturno", "center": "@699", "designacion": "S/2004 S 56"},
    "saturno_s2004_s57": {"id": "65161", "nombre": "S/2004 S 57", "en": "S/2004 S 57", "parent_slug": "saturno", "center": "@699", "designacion": "S/2004 S 57"},
    "saturno_s2004_s58": {"id": "65162", "nombre": "S/2004 S 58", "en": "S/2004 S 58", "parent_slug": "saturno", "center": "@699", "designacion": "S/2004 S 58"},
    "saturno_s2004_s59": {"id": "65163", "nombre": "S/2004 S 59", "en": "S/2004 S 59", "parent_slug": "saturno", "center": "@699", "designacion": "S/2004 S 59"},
    "saturno_s2004_s60": {"id": "65164", "nombre": "S/2004 S 60", "en": "S/2004 S 60", "parent_slug": "saturno", "center": "@699", "designacion": "S/2004 S 60"},
    "saturno_s2004_s61": {"id": "65165", "nombre": "S/2004 S 61", "en": "S/2004 S 61", "parent_slug": "saturno", "center": "@699", "designacion": "S/2004 S 61"},
    "saturno_s2005_s06": {"id": "65166", "nombre": "S/2005 S 06", "en": "S/2005 S 06", "parent_slug": "saturno", "center": "@699", "designacion": "S/2005 S 06"},
    "saturno_s2005_s07": {"id": "65167", "nombre": "S/2005 S 07", "en": "S/2005 S 07", "parent_slug": "saturno", "center": "@699", "designacion": "S/2005 S 07"},
    "saturno_s2006_s21": {"id": "65168", "nombre": "S/2006 S 21", "en": "S/2006 S 21", "parent_slug": "saturno", "center": "@699", "designacion": "S/2006 S 21"},
    "saturno_s2006_s22": {"id": "65169", "nombre": "S/2006 S 22", "en": "S/2006 S 22", "parent_slug": "saturno", "center": "@699", "designacion": "S/2006 S 22"},
    "saturno_s2006_s23": {"id": "65170", "nombre": "S/2006 S 23", "en": "S/2006 S 23", "parent_slug": "saturno", "center": "@699", "designacion": "S/2006 S 23"},
    "saturno_s2006_s24": {"id": "65171", "nombre": "S/2006 S 24", "en": "S/2006 S 24", "parent_slug": "saturno", "center": "@699", "designacion": "S/2006 S 24"},
    "saturno_s2006_s25": {"id": "65172", "nombre": "S/2006 S 25", "en": "S/2006 S 25", "parent_slug": "saturno", "center": "@699", "designacion": "S/2006 S 25"},
    "saturno_s2006_s26": {"id": "65173", "nombre": "S/2006 S 26", "en": "S/2006 S 26", "parent_slug": "saturno", "center": "@699", "designacion": "S/2006 S 26"},
    "saturno_s2006_s27": {"id": "65174", "nombre": "S/2006 S 27", "en": "S/2006 S 27", "parent_slug": "saturno", "center": "@699", "designacion": "S/2006 S 27"},
    "saturno_s2006_s28": {"id": "65175", "nombre": "S/2006 S 28", "en": "S/2006 S 28", "parent_slug": "saturno", "center": "@699", "designacion": "S/2006 S 28"},
    "saturno_s2006_s29": {"id": "65176", "nombre": "S/2006 S 29", "en": "S/2006 S 29", "parent_slug": "saturno", "center": "@699", "designacion": "S/2006 S 29"},
    "saturno_s2007_s10": {"id": "65177", "nombre": "S/2007 S 10", "en": "S/2007 S 10", "parent_slug": "saturno", "center": "@699", "designacion": "S/2007 S 10"},
    "saturno_s2007_s11": {"id": "65178", "nombre": "S/2007 S 11", "en": "S/2007 S 11", "parent_slug": "saturno", "center": "@699", "designacion": "S/2007 S 11"},
    "saturno_s2019_s22": {"id": "65179", "nombre": "S/2019 S 22", "en": "S/2019 S 22", "parent_slug": "saturno", "center": "@699", "designacion": "S/2019 S 22"},
    "saturno_s2019_s23": {"id": "65180", "nombre": "S/2019 S 23", "en": "S/2019 S 23", "parent_slug": "saturno", "center": "@699", "designacion": "S/2019 S 23"},
    "saturno_s2019_s24": {"id": "65181", "nombre": "S/2019 S 24", "en": "S/2019 S 24", "parent_slug": "saturno", "center": "@699", "designacion": "S/2019 S 24"},
    "saturno_s2019_s25": {"id": "65182", "nombre": "S/2019 S 25", "en": "S/2019 S 25", "parent_slug": "saturno", "center": "@699", "designacion": "S/2019 S 25"},
    "saturno_s2019_s26": {"id": "65183", "nombre": "S/2019 S 26", "en": "S/2019 S 26", "parent_slug": "saturno", "center": "@699", "designacion": "S/2019 S 26"},
    "saturno_s2019_s27": {"id": "65184", "nombre": "S/2019 S 27", "en": "S/2019 S 27", "parent_slug": "saturno", "center": "@699", "designacion": "S/2019 S 27"},
    "saturno_s2019_s28": {"id": "65185", "nombre": "S/2019 S 28", "en": "S/2019 S 28", "parent_slug": "saturno", "center": "@699", "designacion": "S/2019 S 28"},
    "saturno_s2019_s29": {"id": "65186", "nombre": "S/2019 S 29", "en": "S/2019 S 29", "parent_slug": "saturno", "center": "@699", "designacion": "S/2019 S 29"},
    "saturno_s2019_s30": {"id": "65187", "nombre": "S/2019 S 30", "en": "S/2019 S 30", "parent_slug": "saturno", "center": "@699", "designacion": "S/2019 S 30"},
    "saturno_s2019_s31": {"id": "65188", "nombre": "S/2019 S 31", "en": "S/2019 S 31", "parent_slug": "saturno", "center": "@699", "designacion": "S/2019 S 31"},
    "saturno_s2019_s32": {"id": "65189", "nombre": "S/2019 S 32", "en": "S/2019 S 32", "parent_slug": "saturno", "center": "@699", "designacion": "S/2019 S 32"},
    "saturno_s2019_s33": {"id": "65190", "nombre": "S/2019 S 33", "en": "S/2019 S 33", "parent_slug": "saturno", "center": "@699", "designacion": "S/2019 S 33"},
    "saturno_s2019_s34": {"id": "65191", "nombre": "S/2019 S 34", "en": "S/2019 S 34", "parent_slug": "saturno", "center": "@699", "designacion": "S/2019 S 34"},
    "saturno_s2019_s35": {"id": "65192", "nombre": "S/2019 S 35", "en": "S/2019 S 35", "parent_slug": "saturno", "center": "@699", "designacion": "S/2019 S 35"},
    "saturno_s2019_s36": {"id": "65193", "nombre": "S/2019 S 36", "en": "S/2019 S 36", "parent_slug": "saturno", "center": "@699", "designacion": "S/2019 S 36"},
    "saturno_s2019_s37": {"id": "65194", "nombre": "S/2019 S 37", "en": "S/2019 S 37", "parent_slug": "saturno", "center": "@699", "designacion": "S/2019 S 37"},
    "saturno_s2019_s38": {"id": "65195", "nombre": "S/2019 S 38", "en": "S/2019 S 38", "parent_slug": "saturno", "center": "@699", "designacion": "S/2019 S 38"},
    "saturno_s2019_s39": {"id": "65196", "nombre": "S/2019 S 39", "en": "S/2019 S 39", "parent_slug": "saturno", "center": "@699", "designacion": "S/2019 S 39"},
    "saturno_s2019_s40": {"id": "65197", "nombre": "S/2019 S 40", "en": "S/2019 S 40", "parent_slug": "saturno", "center": "@699", "designacion": "S/2019 S 40"},
    "saturno_s2019_s41": {"id": "65198", "nombre": "S/2019 S 41", "en": "S/2019 S 41", "parent_slug": "saturno", "center": "@699", "designacion": "S/2019 S 41"},
    "saturno_s2019_s42": {"id": "65199", "nombre": "S/2019 S 42", "en": "S/2019 S 42", "parent_slug": "saturno", "center": "@699", "designacion": "S/2019 S 42"},
    "saturno_s2019_s43": {"id": "65200", "nombre": "S/2019 S 43", "en": "S/2019 S 43", "parent_slug": "saturno", "center": "@699", "designacion": "S/2019 S 43"},
    "saturno_s2019_s44": {"id": "65201", "nombre": "S/2019 S 44", "en": "S/2019 S 44", "parent_slug": "saturno", "center": "@699", "designacion": "S/2019 S 44"},
    "saturno_s2020_s11": {"id": "65202", "nombre": "S/2020 S 11", "en": "S/2020 S 11", "parent_slug": "saturno", "center": "@699", "designacion": "S/2020 S 11"},
    "saturno_s2020_s12": {"id": "65203", "nombre": "S/2020 S 12", "en": "S/2020 S 12", "parent_slug": "saturno", "center": "@699", "designacion": "S/2020 S 12"},
    "saturno_s2020_s13": {"id": "65204", "nombre": "S/2020 S 13", "en": "S/2020 S 13", "parent_slug": "saturno", "center": "@699", "designacion": "S/2020 S 13"},
    "saturno_s2020_s14": {"id": "65205", "nombre": "S/2020 S 14", "en": "S/2020 S 14", "parent_slug": "saturno", "center": "@699", "designacion": "S/2020 S 14"},
    "saturno_s2020_s15": {"id": "65206", "nombre": "S/2020 S 15", "en": "S/2020 S 15", "parent_slug": "saturno", "center": "@699", "designacion": "S/2020 S 15"},
    "saturno_s2020_s16": {"id": "65207", "nombre": "S/2020 S 16", "en": "S/2020 S 16", "parent_slug": "saturno", "center": "@699", "designacion": "S/2020 S 16"},
    "saturno_s2020_s17": {"id": "65208", "nombre": "S/2020 S 17", "en": "S/2020 S 17", "parent_slug": "saturno", "center": "@699", "designacion": "S/2020 S 17"},
    "saturno_s2020_s18": {"id": "65209", "nombre": "S/2020 S 18", "en": "S/2020 S 18", "parent_slug": "saturno", "center": "@699", "designacion": "S/2020 S 18"},
    "saturno_s2020_s19": {"id": "65210", "nombre": "S/2020 S 19", "en": "S/2020 S 19", "parent_slug": "saturno", "center": "@699", "designacion": "S/2020 S 19"},
    "saturno_s2020_s20": {"id": "65211", "nombre": "S/2020 S 20", "en": "S/2020 S 20", "parent_slug": "saturno", "center": "@699", "designacion": "S/2020 S 20"},
    "saturno_s2020_s21": {"id": "65212", "nombre": "S/2020 S 21", "en": "S/2020 S 21", "parent_slug": "saturno", "center": "@699", "designacion": "S/2020 S 21"},
    "saturno_s2020_s22": {"id": "65213", "nombre": "S/2020 S 22", "en": "S/2020 S 22", "parent_slug": "saturno", "center": "@699", "designacion": "S/2020 S 22"},
    "saturno_s2020_s23": {"id": "65214", "nombre": "S/2020 S 23", "en": "S/2020 S 23", "parent_slug": "saturno", "center": "@699", "designacion": "S/2020 S 23"},
    "saturno_s2020_s24": {"id": "65215", "nombre": "S/2020 S 24", "en": "S/2020 S 24", "parent_slug": "saturno", "center": "@699", "designacion": "S/2020 S 24"},
    "saturno_s2020_s25": {"id": "65216", "nombre": "S/2020 S 25", "en": "S/2020 S 25", "parent_slug": "saturno", "center": "@699", "designacion": "S/2020 S 25"},
    "saturno_s2020_s26": {"id": "65217", "nombre": "S/2020 S 26", "en": "S/2020 S 26", "parent_slug": "saturno", "center": "@699", "designacion": "S/2020 S 26"},
    "saturno_s2020_s27": {"id": "65218", "nombre": "S/2020 S 27", "en": "S/2020 S 27", "parent_slug": "saturno", "center": "@699", "designacion": "S/2020 S 27"},
    "saturno_s2020_s28": {"id": "65219", "nombre": "S/2020 S 28", "en": "S/2020 S 28", "parent_slug": "saturno", "center": "@699", "designacion": "S/2020 S 28"},
    "saturno_s2020_s29": {"id": "65220", "nombre": "S/2020 S 29", "en": "S/2020 S 29", "parent_slug": "saturno", "center": "@699", "designacion": "S/2020 S 29"},
    "saturno_s2020_s30": {"id": "65221", "nombre": "S/2020 S 30", "en": "S/2020 S 30", "parent_slug": "saturno", "center": "@699", "designacion": "S/2020 S 30"},
    "saturno_s2020_s31": {"id": "65222", "nombre": "S/2020 S 31", "en": "S/2020 S 31", "parent_slug": "saturno", "center": "@699", "designacion": "S/2020 S 31"},
    "saturno_s2020_s32": {"id": "65223", "nombre": "S/2020 S 32", "en": "S/2020 S 32", "parent_slug": "saturno", "center": "@699", "designacion": "S/2020 S 32"},
    "saturno_s2020_s33": {"id": "65224", "nombre": "S/2020 S 33", "en": "S/2020 S 33", "parent_slug": "saturno", "center": "@699", "designacion": "S/2020 S 33"},
    "saturno_s2020_s34": {"id": "65225", "nombre": "S/2020 S 34", "en": "S/2020 S 34", "parent_slug": "saturno", "center": "@699", "designacion": "S/2020 S 34"},
    "saturno_s2020_s35": {"id": "65226", "nombre": "S/2020 S 35", "en": "S/2020 S 35", "parent_slug": "saturno", "center": "@699", "designacion": "S/2020 S 35"},
    "saturno_s2020_s36": {"id": "65227", "nombre": "S/2020 S 36", "en": "S/2020 S 36", "parent_slug": "saturno", "center": "@699", "designacion": "S/2020 S 36"},
    "saturno_s2020_s37": {"id": "65228", "nombre": "S/2020 S 37", "en": "S/2020 S 37", "parent_slug": "saturno", "center": "@699", "designacion": "S/2020 S 37"},
    "saturno_s2020_s38": {"id": "65229", "nombre": "S/2020 S 38", "en": "S/2020 S 38", "parent_slug": "saturno", "center": "@699", "designacion": "S/2020 S 38"},
    "saturno_s2020_s39": {"id": "65230", "nombre": "S/2020 S 39", "en": "S/2020 S 39", "parent_slug": "saturno", "center": "@699", "designacion": "S/2020 S 39"},
    "saturno_s2020_s40": {"id": "65231", "nombre": "S/2020 S 40", "en": "S/2020 S 40", "parent_slug": "saturno", "center": "@699", "designacion": "S/2020 S 40"},
    "saturno_s2020_s41": {"id": "65232", "nombre": "S/2020 S 41", "en": "S/2020 S 41", "parent_slug": "saturno", "center": "@699", "designacion": "S/2020 S 41"},
    "saturno_s2020_s42": {"id": "65233", "nombre": "S/2020 S 42", "en": "S/2020 S 42", "parent_slug": "saturno", "center": "@699", "designacion": "S/2020 S 42"},
    "saturno_s2020_s43": {"id": "65234", "nombre": "S/2020 S 43", "en": "S/2020 S 43", "parent_slug": "saturno", "center": "@699", "designacion": "S/2020 S 43"},
    "saturno_s2020_s44": {"id": "65235", "nombre": "S/2020 S 44", "en": "S/2020 S 44", "parent_slug": "saturno", "center": "@699", "designacion": "S/2020 S 44"},
    "saturno_s2023_s01": {"id": "65236", "nombre": "S/2023 S 01", "en": "S/2023 S 01", "parent_slug": "saturno", "center": "@699", "designacion": "S/2023 S 01"},
    "saturno_s2023_s02": {"id": "65237", "nombre": "S/2023 S 02", "en": "S/2023 S 02", "parent_slug": "saturno", "center": "@699", "designacion": "S/2023 S 02"},
    "saturno_s2023_s03": {"id": "65238", "nombre": "S/2023 S 03", "en": "S/2023 S 03", "parent_slug": "saturno", "center": "@699", "designacion": "S/2023 S 03"},
    "saturno_s2023_s04": {"id": "65239", "nombre": "S/2023 S 04", "en": "S/2023 S 04", "parent_slug": "saturno", "center": "@699", "designacion": "S/2023 S 04"},
    "saturno_s2023_s05": {"id": "65240", "nombre": "S/2023 S 05", "en": "S/2023 S 05", "parent_slug": "saturno", "center": "@699", "designacion": "S/2023 S 05"},
    "saturno_s2023_s06": {"id": "65241", "nombre": "S/2023 S 06", "en": "S/2023 S 06", "parent_slug": "saturno", "center": "@699", "designacion": "S/2023 S 06"},
    "saturno_s2023_s07": {"id": "65242", "nombre": "S/2023 S 07", "en": "S/2023 S 07", "parent_slug": "saturno", "center": "@699", "designacion": "S/2023 S 07"},
    "saturno_s2023_s08": {"id": "65243", "nombre": "S/2023 S 08", "en": "S/2023 S 08", "parent_slug": "saturno", "center": "@699", "designacion": "S/2023 S 08"},
    "saturno_s2023_s09": {"id": "65244", "nombre": "S/2023 S 09", "en": "S/2023 S 09", "parent_slug": "saturno", "center": "@699", "designacion": "S/2023 S 09"},
    "saturno_s2023_s10": {"id": "65245", "nombre": "S/2023 S 10", "en": "S/2023 S 10", "parent_slug": "saturno", "center": "@699", "designacion": "S/2023 S 10"},
    "saturno_s2023_s11": {"id": "65246", "nombre": "S/2023 S 11", "en": "S/2023 S 11", "parent_slug": "saturno", "center": "@699", "designacion": "S/2023 S 11"},
    "saturno_s2023_s12": {"id": "65247", "nombre": "S/2023 S 12", "en": "S/2023 S 12", "parent_slug": "saturno", "center": "@699", "designacion": "S/2023 S 12"},
    "saturno_s2023_s13": {"id": "65248", "nombre": "S/2023 S 13", "en": "S/2023 S 13", "parent_slug": "saturno", "center": "@699", "designacion": "S/2023 S 13"},
    "saturno_s2023_s14": {"id": "65249", "nombre": "S/2023 S 14", "en": "S/2023 S 14", "parent_slug": "saturno", "center": "@699", "designacion": "S/2023 S 14"},
    "saturno_s2023_s15": {"id": "65250", "nombre": "S/2023 S 15", "en": "S/2023 S 15", "parent_slug": "saturno", "center": "@699", "designacion": "S/2023 S 15"},
    "saturno_s2023_s16": {"id": "65251", "nombre": "S/2023 S 16", "en": "S/2023 S 16", "parent_slug": "saturno", "center": "@699", "designacion": "S/2023 S 16"},
    "saturno_s2023_s17": {"id": "65252", "nombre": "S/2023 S 17", "en": "S/2023 S 17", "parent_slug": "saturno", "center": "@699", "designacion": "S/2023 S 17"},
    "saturno_s2023_s18": {"id": "65253", "nombre": "S/2023 S 18", "en": "S/2023 S 18", "parent_slug": "saturno", "center": "@699", "designacion": "S/2023 S 18"},
    "saturno_s2023_s19": {"id": "65254", "nombre": "S/2023 S 19", "en": "S/2023 S 19", "parent_slug": "saturno", "center": "@699", "designacion": "S/2023 S 19"},
    "saturno_s2023_s20": {"id": "65255", "nombre": "S/2023 S 20", "en": "S/2023 S 20", "parent_slug": "saturno", "center": "@699", "designacion": "S/2023 S 20"},
    "saturno_s2023_s21": {"id": "65256", "nombre": "S/2023 S 21", "en": "S/2023 S 21", "parent_slug": "saturno", "center": "@699", "designacion": "S/2023 S 21"},
    "saturno_s2023_s22": {"id": "65257", "nombre": "S/2023 S 22", "en": "S/2023 S 22", "parent_slug": "saturno", "center": "@699", "designacion": "S/2023 S 22"},
    "saturno_s2023_s23": {"id": "65258", "nombre": "S/2023 S 23", "en": "S/2023 S 23", "parent_slug": "saturno", "center": "@699", "designacion": "S/2023 S 23"},
    "saturno_s2023_s24": {"id": "65259", "nombre": "S/2023 S 24", "en": "S/2023 S 24", "parent_slug": "saturno", "center": "@699", "designacion": "S/2023 S 24"},
    "saturno_s2023_s25": {"id": "65260", "nombre": "S/2023 S 25", "en": "S/2023 S 25", "parent_slug": "saturno", "center": "@699", "designacion": "S/2023 S 25"},
    "saturno_s2023_s26": {"id": "65261", "nombre": "S/2023 S 26", "en": "S/2023 S 26", "parent_slug": "saturno", "center": "@699", "designacion": "S/2023 S 26"},
    "saturno_s2023_s27": {"id": "65262", "nombre": "S/2023 S 27", "en": "S/2023 S 27", "parent_slug": "saturno", "center": "@699", "designacion": "S/2023 S 27"},
    "saturno_s2023_s28": {"id": "65263", "nombre": "S/2023 S 28", "en": "S/2023 S 28", "parent_slug": "saturno", "center": "@699", "designacion": "S/2023 S 28"},
    "saturno_s2023_s29": {"id": "65264", "nombre": "S/2023 S 29", "en": "S/2023 S 29", "parent_slug": "saturno", "center": "@699", "designacion": "S/2023 S 29"},
    "saturno_s2023_s30": {"id": "65265", "nombre": "S/2023 S 30", "en": "S/2023 S 30", "parent_slug": "saturno", "center": "@699", "designacion": "S/2023 S 30"},
    "saturno_s2023_s31": {"id": "65266", "nombre": "S/2023 S 31", "en": "S/2023 S 31", "parent_slug": "saturno", "center": "@699", "designacion": "S/2023 S 31"},
    "saturno_s2023_s32": {"id": "65267", "nombre": "S/2023 S 32", "en": "S/2023 S 32", "parent_slug": "saturno", "center": "@699", "designacion": "S/2023 S 32"},
    "saturno_s2023_s33": {"id": "65268", "nombre": "S/2023 S 33", "en": "S/2023 S 33", "parent_slug": "saturno", "center": "@699", "designacion": "S/2023 S 33"},
    "saturno_s2023_s34": {"id": "65269", "nombre": "S/2023 S 34", "en": "S/2023 S 34", "parent_slug": "saturno", "center": "@699", "designacion": "S/2023 S 34"},
    "saturno_s2023_s35": {"id": "65270", "nombre": "S/2023 S 35", "en": "S/2023 S 35", "parent_slug": "saturno", "center": "@699", "designacion": "S/2023 S 35"},
    "saturno_s2023_s36": {"id": "65271", "nombre": "S/2023 S 36", "en": "S/2023 S 36", "parent_slug": "saturno", "center": "@699", "designacion": "S/2023 S 36"},
    "saturno_s2023_s37": {"id": "65272", "nombre": "S/2023 S 37", "en": "S/2023 S 37", "parent_slug": "saturno", "center": "@699", "designacion": "S/2023 S 37"},
    "saturno_s2023_s38": {"id": "65273", "nombre": "S/2023 S 38", "en": "S/2023 S 38", "parent_slug": "saturno", "center": "@699", "designacion": "S/2023 S 38"},
    "saturno_s2023_s39": {"id": "65274", "nombre": "S/2023 S 39", "en": "S/2023 S 39", "parent_slug": "saturno", "center": "@699", "designacion": "S/2023 S 39"},
    "saturno_s2023_s40": {"id": "65275", "nombre": "S/2023 S 40", "en": "S/2023 S 40", "parent_slug": "saturno", "center": "@699", "designacion": "S/2023 S 40"},
    "saturno_s2023_s41": {"id": "65276", "nombre": "S/2023 S 41", "en": "S/2023 S 41", "parent_slug": "saturno", "center": "@699", "designacion": "S/2023 S 41"},
    "saturno_s2023_s42": {"id": "65277", "nombre": "S/2023 S 42", "en": "S/2023 S 42", "parent_slug": "saturno", "center": "@699", "designacion": "S/2023 S 42"},
    "saturno_s2023_s43": {"id": "65278", "nombre": "S/2023 S 43", "en": "S/2023 S 43", "parent_slug": "saturno", "center": "@699", "designacion": "S/2023 S 43"},
    "saturno_s2023_s44": {"id": "65279", "nombre": "S/2023 S 44", "en": "S/2023 S 44", "parent_slug": "saturno", "center": "@699", "designacion": "S/2023 S 44"},
    "saturno_s2023_s45": {"id": "65280", "nombre": "S/2023 S 45", "en": "S/2023 S 45", "parent_slug": "saturno", "center": "@699", "designacion": "S/2023 S 45"},
    "saturno_s2023_s46": {"id": "65281", "nombre": "S/2023 S 46", "en": "S/2023 S 46", "parent_slug": "saturno", "center": "@699", "designacion": "S/2023 S 46"},
    "saturno_s2023_s47": {"id": "65282", "nombre": "S/2023 S 47", "en": "S/2023 S 47", "parent_slug": "saturno", "center": "@699", "designacion": "S/2023 S 47"},
    "saturno_s2023_s48": {"id": "65283", "nombre": "S/2023 S 48", "en": "S/2023 S 48", "parent_slug": "saturno", "center": "@699", "designacion": "S/2023 S 48"},
    "saturno_s2023_s49": {"id": "65284", "nombre": "S/2023 S 49", "en": "S/2023 S 49", "parent_slug": "saturno", "center": "@699", "designacion": "S/2023 S 49"},
    "saturno_s2023_s50": {"id": "65285", "nombre": "S/2023 S 50", "en": "S/2023 S 50", "parent_slug": "saturno", "center": "@699", "designacion": "S/2023 S 50"},
    "saturno_s2020_s45": {"id": "65286", "nombre": "S/2020 S 45", "en": "S/2020 S 45", "parent_slug": "saturno", "center": "@699", "designacion": "S/2020 S 45"},
    "saturno_s2020_s46": {"id": "65287", "nombre": "S/2020 S 46", "en": "S/2020 S 46", "parent_slug": "saturno", "center": "@699", "designacion": "S/2020 S 46"},
    "saturno_s2020_s47": {"id": "65288", "nombre": "S/2020 S 47", "en": "S/2020 S 47", "parent_slug": "saturno", "center": "@699", "designacion": "S/2020 S 47"},
    "saturno_s2020_s48": {"id": "65289", "nombre": "S/2020 S 48", "en": "S/2020 S 48", "parent_slug": "saturno", "center": "@699", "designacion": "S/2020 S 48"},
    "saturno_s2023_s51": {"id": "65290", "nombre": "S/2023 S 51", "en": "S/2023 S 51", "parent_slug": "saturno", "center": "@699", "designacion": "S/2023 S 51"},
    "saturno_s2023_s52": {"id": "65291", "nombre": "S/2023 S 52", "en": "S/2023 S 52", "parent_slug": "saturno", "center": "@699", "designacion": "S/2023 S 52"},
    "saturno_s2023_s53": {"id": "65292", "nombre": "S/2023 S 53", "en": "S/2023 S 53", "parent_slug": "saturno", "center": "@699", "designacion": "S/2023 S 53"},
    "saturno_s2023_s54": {"id": "65293", "nombre": "S/2023 S 54", "en": "S/2023 S 54", "parent_slug": "saturno", "center": "@699", "designacion": "S/2023 S 54"},
    "saturno_s2023_s55": {"id": "65294", "nombre": "S/2023 S 55", "en": "S/2023 S 55", "parent_slug": "saturno", "center": "@699", "designacion": "S/2023 S 55"},
    "saturno_s2023_s56": {"id": "65295", "nombre": "S/2023 S 56", "en": "S/2023 S 56", "parent_slug": "saturno", "center": "@699", "designacion": "S/2023 S 56"},
    "saturno_s2023_s57": {"id": "65296", "nombre": "S/2023 S 57", "en": "S/2023 S 57", "parent_slug": "saturno", "center": "@699", "designacion": "S/2023 S 57"},
    "saturno_s2020_s49": {"id": "65297", "nombre": "S/2020 S 49", "en": "S/2020 S 49", "parent_slug": "saturno", "center": "@699", "designacion": "S/2020 S 49"},
    "saturno_s2023_s58": {"id": "65298", "nombre": "S/2023 S 58", "en": "S/2023 S 58", "parent_slug": "saturno", "center": "@699", "designacion": "S/2023 S 58"},
    "saturno_s2023_s59": {"id": "65299", "nombre": "S/2023 S 59", "en": "S/2023 S 59", "parent_slug": "saturno", "center": "@699", "designacion": "S/2023 S 59"},
    "saturno_s2023_s60": {"id": "65300", "nombre": "S/2023 S 60", "en": "S/2023 S 60", "parent_slug": "saturno", "center": "@699", "designacion": "S/2023 S 60"},
    "saturno_s2023_s61": {"id": "65301", "nombre": "S/2023 S 61", "en": "S/2023 S 61", "parent_slug": "saturno", "center": "@699", "designacion": "S/2023 S 61"},
    "saturno_s2023_s62": {"id": "65302", "nombre": "S/2023 S 62", "en": "S/2023 S 62", "parent_slug": "saturno", "center": "@699", "designacion": "S/2023 S 62"},
    "saturno_s2023_s63": {"id": "65303", "nombre": "S/2023 S 63", "en": "S/2023 S 63", "parent_slug": "saturno", "center": "@699", "designacion": "S/2023 S 63"},

    # Urano
    "ariel":       {"id": "701", "nombre": "Ariel",      "en": "Ariel",      "parent_slug": "urano", "center": "@799"},
    "umbriel":     {"id": "702", "nombre": "Umbriel",    "en": "Umbriel",    "parent_slug": "urano", "center": "@799"},
    "titania":     {"id": "703", "nombre": "Titania",    "en": "Titania",    "parent_slug": "urano", "center": "@799"},
    "oberon":      {"id": "704", "nombre": "Oberón",     "en": "Oberon",     "parent_slug": "urano", "center": "@799"},
    "miranda":     {"id": "705", "nombre": "Miranda",    "en": "Miranda",    "parent_slug": "urano", "center": "@799"},
    "cordelia":    {"id": "706", "nombre": "Cordelia",   "en": "Cordelia",   "parent_slug": "urano", "center": "@799"},
    "ofelia":      {"id": "707", "nombre": "Ofelia",     "en": "Ophelia",    "parent_slug": "urano", "center": "@799"},
    "bianca":      {"id": "708", "nombre": "Bianca",     "en": "Bianca",     "parent_slug": "urano", "center": "@799"},
    "cressida":    {"id": "709", "nombre": "Cressida",   "en": "Cressida",   "parent_slug": "urano", "center": "@799"},
    "desdemona":   {"id": "710", "nombre": "Desdémona",  "en": "Desdemona",  "parent_slug": "urano", "center": "@799"},
    "julieta":     {"id": "711", "nombre": "Julieta",    "en": "Juliet",     "parent_slug": "urano", "center": "@799"},
    "portia":      {"id": "712", "nombre": "Portia",     "en": "Portia",     "parent_slug": "urano", "center": "@799"},
    "rosalind":    {"id": "713", "nombre": "Rosalind",   "en": "Rosalind",   "parent_slug": "urano", "center": "@799"},
    "belinda":     {"id": "714", "nombre": "Belinda",    "en": "Belinda",    "parent_slug": "urano", "center": "@799"},
    "puck":        {"id": "715", "nombre": "Puck",       "en": "Puck",       "parent_slug": "urano", "center": "@799"},
    "caliban":     {"id": "716", "nombre": "Caliban",    "en": "Caliban",    "parent_slug": "urano", "center": "@799"},
    "sycorax":     {"id": "717", "nombre": "Sycorax",    "en": "Sycorax",    "parent_slug": "urano", "center": "@799"},
    "prospero":    {"id": "718", "nombre": "Prospero",   "en": "Prospero",   "parent_slug": "urano", "center": "@799", "designacion": "S/1999 U 3"},
    "setebos":     {"id": "719", "nombre": "Setebos",    "en": "Setebos",    "parent_slug": "urano", "center": "@799", "designacion": "S/1999 U 1"},
    "stephano":    {"id": "720", "nombre": "Stephano",   "en": "Stephano",   "parent_slug": "urano", "center": "@799", "designacion": "S/1999 U 2"},
    "trinculo":    {"id": "721", "nombre": "Trínculo",   "en": "Trinculo",   "parent_slug": "urano", "center": "@799", "designacion": "S/2001 U 1"},
    "francisco":   {"id": "722", "nombre": "Francisco",  "en": "Francisco",  "parent_slug": "urano", "center": "@799", "designacion": "S/2001 U 3"},
    "margaret":    {"id": "723", "nombre": "Margaret",   "en": "Margaret",   "parent_slug": "urano", "center": "@799", "designacion": "S/2003 U 3"},
    "ferdinand":   {"id": "724", "nombre": "Ferdinand",  "en": "Ferdinand",  "parent_slug": "urano", "center": "@799", "designacion": "S/2001 U 2"},
    "perdita":     {"id": "725", "nombre": "Perdita",    "en": "Perdita",    "parent_slug": "urano", "center": "@799", "designacion": "S/1986 U 10"},
    "mab":         {"id": "726", "nombre": "Mab",        "en": "Mab",        "parent_slug": "urano", "center": "@799", "designacion": "S/2003 U 1"},
    "cupid":       {"id": "727", "nombre": "Cupid",      "en": "Cupid",      "parent_slug": "urano", "center": "@799", "designacion": "S/2003 U 2"},

    # Neptuno
    "triton":       {"id": "801",   "nombre": "Tritón",      "en": "Triton",      "parent_slug": "neptuno", "center": "@899"},
    "nereida":      {"id": "802",   "nombre": "Nereida",     "en": "Nereid",      "parent_slug": "neptuno", "center": "@899"},
    "nayade":       {"id": "803",   "nombre": "Náyade",      "en": "Naiad",       "parent_slug": "neptuno", "center": "@899"},
    "thalassa":     {"id": "804",   "nombre": "Talasa",      "en": "Thalassa",    "parent_slug": "neptuno", "center": "@899"},
    "despina":      {"id": "805",   "nombre": "Despina",     "en": "Despina",     "parent_slug": "neptuno", "center": "@899"},
    "galatea":      {"id": "806",   "nombre": "Galatea",     "en": "Galatea",     "parent_slug": "neptuno", "center": "@899"},
    "larisa":       {"id": "807",   "nombre": "Larisa",      "en": "Larissa",     "parent_slug": "neptuno", "center": "@899"},
    "proteo":       {"id": "808",   "nombre": "Proteo",      "en": "Proteus",     "parent_slug": "neptuno", "center": "@899"},
    "halimede":     {"id": "809",   "nombre": "Halimede",    "en": "Halimede",    "parent_slug": "neptuno", "center": "@899", "designacion": "S/2002 N 1"},
    "psamathe":     {"id": "810",   "nombre": "Psámate",     "en": "Psamathe",    "parent_slug": "neptuno", "center": "@899", "designacion": "S/2003 N 1"},
    "sao":          {"id": "811",   "nombre": "Sao",         "en": "Sao",         "parent_slug": "neptuno", "center": "@899", "designacion": "S/2002 N 2"},
    "laomedeia":    {"id": "812",   "nombre": "Laomedeia",   "en": "Laomedeia",   "parent_slug": "neptuno", "center": "@899", "designacion": "S/2002 N 3"},
    "neso":         {"id": "813",   "nombre": "Neso",        "en": "Neso",        "parent_slug": "neptuno", "center": "@899", "designacion": "S/2002 N 4"},
    "hippocamp":    {"id": "814",   "nombre": "Hipocampo",   "en": "Hippocamp",   "parent_slug": "neptuno", "center": "@899", "designacion": "S/2004 N 1"},
    "neptuno_s2002_n5": {"id": "85051", "nombre": "S/2002 N 5", "en": "S/2002 N 5", "parent_slug": "neptuno", "center": "@899", "designacion": "S/2002 N 5"},
    "neptuno_s2021_n1": {"id": "85052", "nombre": "S/2021 N 1", "en": "S/2021 N 1", "parent_slug": "neptuno", "center": "@899", "designacion": "S/2021 N 1"},

    # Plutón
    "caronte":   {"id": "901", "nombre": "Caronte",   "en": "Charon",     "parent_slug": "pluton",  "center": "@999"},
    "nix":       {"id": "902", "nombre": "Nix",       "en": "Nix",        "parent_slug": "pluton",  "center": "@999"},
    "hydra":     {"id": "903", "nombre": "Hydra",     "en": "Hydra",      "parent_slug": "pluton",  "center": "@999"},
    "kerberos":  {"id": "904", "nombre": "Kerberos",  "en": "Kerberos",   "parent_slug": "pluton",  "center": "@999"},
    "styx":      {"id": "905", "nombre": "Styx",      "en": "Styx",       "parent_slug": "pluton",  "center": "@999"},
}


# ── HELPERS ──────────────────────────────────────────────────────────────────
_wikidata_cache: dict = {}
NO_DISCOVERY_DATE = {
    "Mercury", "Venus", "Earth", "Mars", "Jupiter", "Saturn"
}

def ttl_escape(text: str) -> str:
    return str(text).replace("\\", "\\\\").replace('"', '\\"')
    

def clean_horizons_id(raw_id: str) -> str:
    if raw_id is None:
        return ""
    return raw_id.rstrip(";:")

def decimal_literal(value):
    if value is None:
        return None

    try:
        dec = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None

    text = format(dec, "f")

    if "." in text:
        text = text.rstrip("0").rstrip(".")
        if text == "-0":
            text = "0"

    return f'"{text}"^^xsd:decimal'

def url_literal(value):
    if not value:
        return []
    url_list = [f'"{v}"^^xsd:anyURI' for v in value if v]

    return url_list

def date_literal(value):
    if not value:
        return None
    if not _DATE_RE.match(str(value)):
        return None          
    return f'"{value}"^^xsd:date'

def satellite_enabled(sat_info):
    if not GENERAR_SATELITES:
        return False
    if SATELLITES_PLANETAS_ACTIVOS is None:
        return True
    return sat_info["parent_slug"] in SATELLITES_PLANETAS_ACTIVOS

G = 6.67430e-11  # m^3 kg^-1 s^-2

def to_float(value):
    if value is None:
        return None
    value = str(value).strip()
    if not value or value.lower() == "n.a.":
        return None

    if "+-" in value:
        value = value.split("+-")[0].strip()

    return float(value)


def extract_physical_properties(result: str):
    masa_kg = None
    gm_m3s2 = None
    duracion_dia_horas = None

    mass_match = _re.search(
        r"Mass\s*x10\^([0-9+\-]+)\s*\(kg\)\s*=\s*([0-9.Ee+\-]+(?:\+\-[0-9.Ee+\-]+)?)",
        result,
        _re.IGNORECASE
    )
    if mass_match:
        exponent = int(mass_match.group(1))
        mantissa = to_float(mass_match.group(2))
        if mantissa is not None:
            masa_kg = mantissa * (10 ** exponent)

    gm_match = _re.search(
        r"GM\s*(?:=\s*|,\s*)([0-9.Ee+\-]+)\s*(km\^3/s\^2|m\^3/s\^2)?",
        result,
        _re.IGNORECASE
    )
    if gm_match:
        gm_value = to_float(gm_match.group(1))
        gm_unit = gm_match.group(2).lower() if gm_match.group(2) else "km^3/s^2"

        if gm_value is not None:
            if gm_unit == "km^3/s^2":
                gm_m3s2 = gm_value * 1e9
            else:
                gm_m3s2 = gm_value

    rotper_match = _re.search(
        r"ROTPER\s*=\s*([0-9.Ee+\-]+)",
        result,
        _re.IGNORECASE
    )
    if rotper_match:
        duracion_dia_horas = to_float(rotper_match.group(1))

    if masa_kg is None and gm_m3s2 is not None:
        masa_kg = gm_m3s2 / G

    return {
        "masaKg": masa_kg,
        "gm": gm_m3s2,
        "duracionDiaHoras": duracion_dia_horas,
    }

def _sparql_request(query: str, timeout: int) -> dict:
    headers = {
        "Accept": "application/sparql-results+json",
        "User-Agent": "SistemaSolarTTL/1.0 (contacto@ejemplo.org)",
    }
    response = requests.get(
        WIKIDATA_SPARQL_URL,
        params={"query": query},
        headers=headers,
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json()
 
 
def _sparql_with_retry(query: str, timeouts=(10, 20, 40), pause=2) -> dict | None:
    for attempt, t in enumerate(timeouts, start=1):
        try:
            return _sparql_request(query, timeout=t)
        except requests.exceptions.Timeout:
            print(f"    Wikidata timeout (intento {attempt}/{len(timeouts)}, {t}s)...")
            if attempt < len(timeouts):
                time.sleep(pause * attempt)   # espera 2s, 4s…
        except requests.exceptions.RequestException as e:
            print(f"    Wikidata error (intento {attempt}): {e}")
            if attempt < len(timeouts):
                time.sleep(pause * attempt)
    return None
 
 
def wikidata_discovery_info(name_en: str) -> dict:
    if name_en in _wikidata_cache:
        return _wikidata_cache[name_en]

    empty = {"descubridores": [], "fechaDescubrimiento": None}

    query_main = f"""
    SELECT DISTINCT ?discoverer ?discovererLabel ?discoveryDate ?image WHERE {{
    ?body <http://www.w3.org/2000/01/rdf-schema#label> "{name_en}"@en .
    OPTIONAL {{
        ?body <http://www.wikidata.org/prop/direct/P61> ?discoverer .
        OPTIONAL {{ ?discoverer <http://www.wikidata.org/prop/direct/P18> ?image . }}
    }}
    OPTIONAL {{ ?body <http://www.wikidata.org/prop/direct/P575> ?discoveryDate . }}
    SERVICE <http://wikiba.se/ontology#label> {{
        <http://www.bigdata.com/rdf#serviceParam>
        <http://wikiba.se/ontology#language> "es,en" .
    }}
    }}
    LIMIT 10
    """

    data = _sparql_with_retry(query_main)
    if data is None:
        _wikidata_cache[name_en] = empty
        return empty

    discoverers: dict[str, dict] = {}
    discovery_date: str | None = None

    usar_fecha_descubrimiento = name_en not in NO_DISCOVERY_DATE

    for row in data["results"]["bindings"]:
        if usar_fecha_descubrimiento and not discovery_date and "discoveryDate" in row:
            raw = row["discoveryDate"]["value"][:10]
            if _DATE_RE.match(raw):
                discovery_date = raw

        if "discoverer" in row:
            uri = row["discoverer"]["value"]
            qid = uri.rsplit("/", 1)[-1]
            if not qid.startswith("Q"):
                continue
            label = row.get("discovererLabel", {}).get("value", qid)
            image = row.get("image", {}).get("value")

            if qid not in discoverers:
                discoverers[qid] = {
                    "qid": qid,
                    "nombre": label,
                    "imagen": image,
                    "slug": slugify_person(label),
                }
            elif not discoverers[qid].get("imagen") and image:
                discoverers[qid]["imagen"] = image

    result = {
        "descubridores": list(discoverers.values()),
        "fechaDescubrimiento": discovery_date,
    }
    _wikidata_cache[name_en] = result
    return result
 

def slugify_person(text: str) -> str:
    text = text.lower().strip()
    text = (
        text.replace("á", "a").replace("é", "e").replace("í", "i")
            .replace("ó", "o").replace("ú", "u").replace("ñ", "n")
    )
    text = _re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")

def normalize_name(text: str) -> str:
    text = text.lower().strip()
    text = (
        text.replace("á", "a")
            .replace("é", "e")
            .replace("í", "i")
            .replace("ó", "o")
            .replace("ú", "u")
    )
    text = _re.sub(r"[^a-z0-9]+", "", text)
    return text

def ensure_target_matches(result: str, expected_name: str):
    m = _re.search(r"Target body name:\s*(.+)", result)
    if not m:
        raise RuntimeError("Horizons no devolvió 'Target body name'")

    returned_name = m.group(1).strip()

    expected_norm = normalize_name(expected_name)
    returned_norm = normalize_name(returned_name)

    if expected_norm not in returned_norm:
        raise RuntimeError(
            f"Horizons devolvió otro cuerpo distinto de {expected_name}. "
            f"Devuelto: {returned_name}"
        )
    
def horizons_elements(command: str, center: str, out_units: str,  expected_name: str = None) -> dict:
    start = CONSULTA_FECHA
    stop = CONSULTA_FECHA_FIN

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

    if expected_name:
        ensure_target_matches(result, expected_name)

    if "$$SOE" not in result or "$$EOE" not in result:
        raise RuntimeError(
            f"Horizons no devolvió tabla válida para COMMAND={command}, CENTER={center}"
        )

    table = result.split("$$SOE")[1].split("$$EOE")[0].strip()
    first_line = table.splitlines()[0]

    reader = csv.reader(StringIO(first_line), skipinitialspace=True)
    row = next(reader)

    physical = extract_physical_properties(result)

    return {
        "excentricidad":              to_float(row[2]),
        "periapsis":                  to_float(row[3]),
        "inclinacionDeg":             to_float(row[4]),
        "longitudNodoAscendenteDeg":  to_float(row[5]),
        "argumentoPeriapsisDeg":      to_float(row[6]),
        "anomaliaMediaDeg":           to_float(row[9]),
        "semiejeMayor":               to_float(row[11]),
        "apoapsis":                   to_float(row[12]),
        "periodoOrbitalDias":         to_float(row[13]),
        "masaKg":                     physical["masaKg"],
        "gm":                         physical["gm"],
        "duracionDiaHoras":           physical["duracionDiaHoras"],
    }


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
        return []

    return [
    item.get("links", [{}])[0].get("href", "")
    for item in items[:3]
    ]



def add_orbit_ttl(lines, orbit_uri, orbit, unit: str):

    lines.append(f"{orbit_uri}")
    lines.append("    a sol:Orbita ;")
    fecha_consulta = date_literal(CONSULTA_FECHA)
    if fecha_consulta:
        lines.append(f"    sol:fechaConsulta {fecha_consulta} ;")

    if unit == "AU":
        props = [
            ("semiejeMayorAu",            "semiejeMayor",             "decimal"),
            ("perihelioAu",               "periapsis",                "decimal"),
            ("afelioAu",                  "apoapsis",                 "decimal"),
            ("excentricidad",             "excentricidad",            "decimal"),
            ("inclinacionDeg",            "inclinacionDeg",           "decimal"),
            ("longitudNodoAscendenteDeg", "longitudNodoAscendenteDeg","decimal"),
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


def add_heliocentric_bodies(lines, title, bodies, rdf_class, personas_cache):
    lines.extend([f"# ── {title} ", ""])

    for slug, info in bodies.items():
        print(f"  Consultando: {info['nombre']}...")
        orbit_uri = f"sol:orbita_{slug}"

        try:
            orbit = horizons_elements(
                command=info["id"],
                center="@10",
                out_units="AU-D",
                expected_name=info["en"]
            )
        except Exception as e:
            print(f"  ERROR con {info['nombre']}: {e}")
            continue

        try:
            discovery = wikidata_discovery_info(info["en"])
        except Exception as e:
            print(f"  AVISO discovery con {info['nombre']}: {e}")
            discovery = {"descubridores": [], "fechaDescubrimiento": None} 
        
        imagenes = url_literal(nasa_image(info["en"]))
        clean_id = clean_horizons_id(info["id"])

        satelites_del_cuerpo = [
            f"sol:{s_slug}"
            for s_slug, s_info in SATELLITES.items()
            if s_info["parent_slug"] == slug and satellite_enabled(s_info)
        ]

        body_lines = [
            f"sol:{slug}",
            f"    a sol:{rdf_class} ;",
            f'    sol:nombre "{info["nombre"]}" ;',
            f'    sol:nombreIngles "{info["en"]}" ;',
            f'    sol:horizonsId "{clean_id}" ;',
            "    sol:orbitaAlrededorDe sol:sol ;",
        ]

        masa_lit = decimal_literal(orbit.get("masaKg"))
        if masa_lit is not None:
            body_lines.append(f"    sol:masaKg {masa_lit} ;")

        gm_lit = decimal_literal(orbit.get("gm"))
        if gm_lit is not None:
            body_lines.append(f"    sol:gmM3s2 {gm_lit} ;")

        dia_lit = decimal_literal(orbit.get("duracionDiaHoras"))
        if dia_lit is not None:
            body_lines.append(f"    sol:duracionDiaHoras {dia_lit} ;")

        if discovery.get("fechaDescubrimiento"):
            body_lines.append(
                f'    sol:fechaDescubrimiento "{discovery["fechaDescubrimiento"]}"^^xsd:date ;'
            )

        for person in discovery.get("descubridores", []):
            body_lines.append(f"    sol:descubiertoPor sol:descubridor_{person['slug']} ;")
            personas_cache[person["qid"]] = person

        for imagen in imagenes:
            if imagen:
                body_lines.append(f"    sol:imagenUrl {imagen} ;")

        for sat_uri in satelites_del_cuerpo:
            body_lines.append(f"    sol:tieneSatelite {sat_uri} ;")

        body_lines.append(f"    sol:tieneOrbita {orbit_uri} .")
        body_lines.append("")

        lines.extend(body_lines)
        add_orbit_ttl(lines, orbit_uri, orbit, unit="AU")

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
    personas_cache = {}

    lines.extend(["# ── PLANETAS ────────────────────────────────────────────────", ""])

    for slug, info in PLANETS.items():
        print(f"  Consultando planeta: {info['nombre']}...")
        
        orbit_uri = f"sol:orbita_{slug}"

        try:
            orbit = horizons_elements(
                command=info["id"],
                center="@10",
                out_units="AU-D",
                expected_name=info["en"]
            )
        except Exception as e:
            print(f"  ERROR con {info['nombre']}: {e}")
            continue
        try:
            discovery = wikidata_discovery_info(info["en"])
        except Exception as e:
            print(f"  AVISO discovery con {info['nombre']}: {e}")
            discovery = {"descubridores": [], "fechaDescubrimiento": None}

        satelites_del_planeta = [
            f"sol:{s_slug}"
            for s_slug, s_info in SATELLITES.items()
            if s_info["parent_slug"] == slug and satellite_enabled(s_info)
        ]

        imagen_planeta =  url_literal(nasa_image(info["en"]))
        clean_id = clean_horizons_id(info["id"])
        body_lines = [
            f"sol:{slug}",
            "    a sol:Planeta ;",
            f'    sol:nombre "{info["nombre"]}" ;',
            f'    sol:nombreIngles "{info["en"]}" ;',
            f'    sol:horizonsId "{clean_id}" ;',
            f'    sol:tipoPlaneta "{info["tipo"]}" ;',
            "    sol:orbitaAlrededorDe sol:sol ;",
        ]
        masa_lit = decimal_literal(orbit.get("masaKg"))
        if masa_lit is not None:
            body_lines.append(f"    sol:masaKg {masa_lit} ;")

        gm_lit = decimal_literal(orbit.get("gm"))
        if gm_lit is not None:
            body_lines.append(f"    sol:gmM3s2 {gm_lit} ;")

        dia_lit = decimal_literal(orbit.get("duracionDiaHoras"))
        if dia_lit is not None:
            body_lines.append(f"    sol:duracionDiaHoras {dia_lit} ;")

        if discovery.get("fechaDescubrimiento"):
            body_lines.append(
                f'    sol:fechaDescubrimiento "{discovery["fechaDescubrimiento"]}"^^xsd:date ;'
            )

        for person in discovery.get("descubridores", []):
            body_lines.append(f"    sol:descubiertoPor sol:descubridor_{person['slug']} ;")
            personas_cache[person["qid"]] = person

        for imagen in imagen_planeta:
            if imagen:
                body_lines.append(f"    sol:imagenUrl {imagen} ;")

        for sat_uri in satelites_del_planeta:
            body_lines.append(f"    sol:tieneSatelite {sat_uri} ;")

        body_lines[-1] = body_lines[-1].rstrip(" ;") + " ;"
        body_lines.append(f"    sol:tieneOrbita {orbit_uri} .")

        lines.extend(body_lines)
        lines.append("")
        add_orbit_ttl(lines, orbit_uri, orbit, unit="AU")

    add_heliocentric_bodies(
        lines=lines,
        title="PLANETAS ENANOS",
        bodies=DWARF_PLANETS,
        rdf_class="PlanetaEnano",
        personas_cache=personas_cache,
    )

    add_heliocentric_bodies(
        lines=lines,
        title="ASTEROIDES",
        bodies=ASTEROIDS,
        rdf_class="Asteroide",
        personas_cache=personas_cache,
    )

    lines.extend(["# ── SATÉLITES NATURALES ─────────────────────────────────────", ""])

    for slug, info in SATELLITES.items():
        if not satellite_enabled(info):
            continue

        print(f"  Consultando satélite: {info['nombre']}...")
        
        parent_uri = f"sol:{info['parent_slug']}"
        orbit_uri  = f"sol:orbita_{slug}"

        try:
            orbit = horizons_elements(
                command=info["id"],
                center=info["center"],
                out_units="KM-D",
                expected_name=info["en"]
            )
        except Exception as e:
            print(f"  ERROR con {info['nombre']}: {e}")
            continue

        try:
            discovery = wikidata_discovery_info(info["en"])
        except Exception as e:
            print(f"  AVISO discovery con {info['nombre']}: {e}")
            discovery = {"descubridores": [], "fechaDescubrimiento": None}

        if info.get("designacion") and info["nombre"].startswith("S/"):
            imagen_satelite = []
        else:
            imagen_satelite = url_literal(nasa_image(info["en"]))

        body_lines = [
            f"sol:{slug}",
            "    a sol:Satelite ;",
            f'    sol:nombre "{info["nombre"]}" ;',
            f'    sol:nombreIngles "{info["en"]}" ;',
            f'    sol:horizonsId "{clean_horizons_id(info["id"])}" ;',
        ]

        masa_lit = decimal_literal(orbit.get("masaKg"))
        if masa_lit is not None:
            body_lines.append(f"    sol:masaKg {masa_lit} ;")

        gm_lit = decimal_literal(orbit.get("gm"))
        if gm_lit is not None:
            body_lines.append(f"    sol:gmM3s2 {gm_lit} ;")

        dia_lit = decimal_literal(orbit.get("duracionDiaHoras"))
        if dia_lit is not None:
            body_lines.append(f"    sol:duracionDiaHoras {dia_lit} ;")
            
        if discovery.get("fechaDescubrimiento"):
            body_lines.append(
                f'    sol:fechaDescubrimiento "{discovery["fechaDescubrimiento"]}"^^xsd:date ;'
            )

        for person in discovery.get("descubridores", []):
            body_lines.append(f"    sol:descubiertoPor sol:descubridor_{person['slug']} ;")
            personas_cache[person["qid"]] = person

        if info.get("designacion"):
            body_lines.append(f'    sol:designacionProvisional "{info["designacion"]}" ;')

        body_lines.extend([
            f"    sol:sateliteDe {parent_uri} ;",
            f"    sol:orbitaAlrededorDe {parent_uri} ;",
        ])

        for imagen in imagen_satelite:
            if imagen:
                body_lines.append(f"    sol:imagenUrl {imagen} ;")

        body_lines.append(f"    sol:tieneOrbita {orbit_uri} .")
        body_lines.append("")

        lines.extend(body_lines)
        add_orbit_ttl(lines, orbit_uri, orbit, unit="KM")

    lines.extend(["# ── DESCUBRIDORES ───────────────────────────────", ""])
    for person in personas_cache.values():
        lines.append(f"sol:descubridor_{person['slug']}")
        lines.append("    a sol:Descubridor ;")
        lines.append(f'    sol:nombreDescubridor "{ttl_escape(person["nombre"])}" ;')
        lines.append(f'    sol:wikidataId "{person["qid"]}" ;')
        if person.get("imagen"):
            lines.append(f'    sol:imagenDescubridorUrl "{person["imagen"]}"^^xsd:anyURI .')
        else:
            lines[-1] = lines[-1].rstrip(" ;") + " ."
        lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    print("Generando data_horizons.ttl desde NASA/JPL Horizons...\n")
    ttl = build_ttl()
    Path("data_horizons.ttl").write_text(ttl, encoding="utf-8")
    print("\nArchivo generado: data_horizons.ttl")
    imagen_Makemake =  nasa_image("Makemake")
    print(f"URL de imagen representativa de Makemake: {imagen_Makemake}")
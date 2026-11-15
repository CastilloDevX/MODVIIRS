"""Configuracion comun del modelo predictivo (rama `predictivo`)."""
from pathlib import Path
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]          # .../MODVIIRS/prediccion
DATA = RAIZ / "data"
RAW, PROC = DATA / "raw", DATA / "processed"
OUT = RAIZ / "outputs"
FIG = OUT / "figures"
FRONT = OUT / "frontend_data"
for _p in (RAW, PROC, FIG):
    _p.mkdir(parents=True, exist_ok=True)

# Entradas
ALEXIS_PUNTOS = RAIZ.parent / "backend" / "data" / "hotspots_harmonized.parquet"   # capa de puntos de Alexis (6 paises)
PUNTOS = RAW / "hotspots_harmonized_peninsula.parquet"                            # extracto (p00)
POWER = RAW / "power_daily.parquet"                                               # NASA POWER diario (00_descarga_power)

# Region y cuadricula
W, S, E, N = -92.5, 17.8, -86.7, 21.7
TAM_CELDA, CELDAS_POR_ZONA = 0.1, 5            # celda 0.1 deg (~10 km), zona 5x5 celdas = 0.5 deg (~55 km)
NF, NC = 39, 58                                 # filas x columnas de celdas
# cell_id = fila*100 + col ; fila = floor((lat-S)/0.1) ; col = floor((lon-W)/0.1)
# zona_id = (fila//5)*100 + col//5

INICIO = pd.Timestamp("2002-07-01")             # primer lunes con Aqua
# Eras de PLATAFORMA UNICA (R3 de Alexis): (era, satellite en el parquet de Alexis, desde, hasta)
# Era VIIRS = UNA plataforma a la vez: S-NPP hasta 2018-03-31 y NOAA-20 desde 2018-04-01 (gemelos, razon ~1.00).
# Asi la era VIIRS continua en vivo con NOAA-20 tras el cese de S-NPP (2-nov-2026).
ERAS = [
    ("MODIS_Aqua", "Aqua", "2002-07-01", "2012-01-22"),
    ("VIIRS",      "N",    "2012-01-23", "2018-03-31"),
    ("VIIRS",      "N20",  "2018-04-01", "2025-12-31"),
]
# type==0 no existe en NRT: para que historia y vivo usen la MISMA regla, se filtra solo con la mascara de
# fuentes persistentes de Alexis (captura ~98% de type 2/3).
USAR_FILTRO_TYPE = False
# Huecos de sensor (EXCLUDE_YM del pipeline de Alexis): semanas "sin datos", no "cero fuego"
HUECOS = {}   # los huecos de EXCLUDE_YM (S-NPP jul-ago 2022, MODIS abr 2022) no afectan a Aqua<=2012 ni a NOAA-20

# Anomalia
VENT_SEMANAS = 2            # historia: misma semana del anio +-2
MIN_ANIOS = 3               # minimo de anios previos DENTRO de la era
UMBRAL_MIN = 3              # actividad minima (dias-con-fuego en la zona) para llamar anomalia

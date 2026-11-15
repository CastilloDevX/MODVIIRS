# Intento desde hotspots_harmonized.parquet — 15 de noviembre de 2026

Se ejecutaron p00, p01 y p02 (clima, horizonte de una semana) desde el archivo original.
Fuente: /home/joseph/Documentos/MODVIIRS/backend/data/hotspots_harmonized.parquet
SHA-256: 4c3b206d269dea156b5c7ee5b5d081a2ab89554e211f2d0b6f3726cc9bbfb650
Clima: /home/joseph/Documentos/MODVIIRS/backend/data/prediccion/power_daily.parquet

Se extrajeron 1,271,634 detecciones de la península de Yucatán.
El pipeline produjo 65 zonas y 29.499 filas zona-semana, idénticas a las empaquetadas.
Se conservaron los filtros y parámetros existentes (type_filter=False).
La evaluación entrena para cada año solo con años anteriores; resumen VIIRS 2015–2025.

| Métrica | Este entrenamiento | Resultado guardado |
| --- | ---: | ---: |
| auc | 0.853818 | 0.853000 |
| ap | 0.284949 | 0.277900 |
| brier | 0.045289 | 0.045500 |

Las pequeñas diferencias de métricas no proceden de diferencias en la actividad zona-semana.
No se determinó su causa; las versiones de las bibliotecas de esta ejecución están en resultado.json.
No se realizó búsqueda de hiperparámetros ni se sustituyeron los artefactos de la API.
Se corrigió una conversión de matriz de solo lectura con to_numpy(copy=True) en anomalias.py.
No se evaluó generalización fuera de esta región ni validez operativa.

Archivos: resultado.json, logs por etapa, outputs/metricas_clima_h1.csv,
outputs/calibracion_clima_h1.csv, outputs/figures/modelo_clima_h1.png,
processed/pred_clima_h1.parquet.

Para repetir en este equipo, desde la raíz:

```bash
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=2 ARROW_NUM_THREADS=2 \
  backend/.venv/bin/python prediccion/data/experimentos/intento_hotspots.py
```

Cada ejecución crea una carpeta nueva. El runner y los artefactos están ignorados por Git.

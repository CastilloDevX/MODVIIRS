# Data pipeline — reference copies

These are read-only copies kept here for documentation purposes.
The canonical versions live in `NASA2026/Data/` and must be edited there.

## Data flow

```
descarga/download_firms.py          Download raw FIRMS CSVs from NASA API
descarga/csv_to_parquet.py          Validate and convert CSV → Parquet

armonizacion/harmonize_firms.py     Core harmonization (Methods D+G)
                                    Output: hotspots_harmonized, activity_grid,
                                            cell_climatology, scaling_factors,
                                            persistent_mask
armonizacion/build_training_dataset.py  Build continuous time-series for ML

armonizacion/aoi_queries.py         AOI-level query functions
                                    (also imported at runtime by the backend)
```

## Analysis notebooks

```
analisis/01_paises/01_justificacion_paises.ipynb   Country selection justification
analisis/02_eda/02_eda_seis_paises.ipynb           EDA before harmonization
```

Supporting scripts: `analisis/01_paises/summarize_firms.py`, `analisis/02_eda/eda_aggregate.py`.

## Docs

Decision log and dataset guides are under `armonizacion/docs/`.

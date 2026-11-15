"""Reproduce el pipeline existente en una carpeta aislada, desde el parquet original."""
import contextlib
import gc
import hashlib
import importlib.metadata
import json
from pathlib import Path
import runpy
import sys
import time
import traceback
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'prediccion/src'))
import config as C
import pyarrow as pa
import pyarrow.parquet as pq

pa.set_cpu_count(2)
pa.set_io_thread_count(2)
run = Path(__file__).parent / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ_hotspots')
run.mkdir()
C.DATA = run
C.RAW, C.PROC, C.OUT = run / 'raw', run / 'processed', run / 'outputs'
C.FIG = C.OUT / 'figures'
for p in [C.RAW, C.PROC, C.FIG]:
    p.mkdir(parents=True, exist_ok=True)
C.PUNTOS = C.RAW / 'hotspots_harmonized_peninsula.parquet'
C.POWER = ROOT / 'backend/data/prediccion/power_daily.parquet'
source = C.ALEXIS_PUNTOS
md = pq.ParquetFile(source).metadata
report = {
    'started_utc': datetime.now(timezone.utc).isoformat(),
    'source': str(source), 'source_bytes': source.stat().st_size,
    'source_mtime_ns': source.stat().st_mtime_ns, 'source_rows': md.num_rows,
    'climate_source': str(C.POWER),
    'region': {'west': C.W, 'south': C.S, 'east': C.E, 'north': C.N},
    'mode': 'clima', 'horizon_weeks': 1,
    'type_filter': C.USAR_FILTRO_TYPE,
    'params': dict(max_iter=200, learning_rate=0.05, max_leaf_nodes=15,
                   l2_regularization=1.0, random_state=0),
    'versions': {k: importlib.metadata.version(k) for k in ['pandas','numpy','pyarrow','scikit-learn']},
    'stages': [],
}
print('RUN:', run, flush=True)
try:
    for script in ['p00_extraer_peninsula.py', 'p01_actividad_semanal.py', 'p02_modelo.py']:
        print('START:', script, flush=True)
        start = time.monotonic()
        sys.argv = [script, 'clima', '1'] if script == 'p02_modelo.py' else [script]
        with (run / (script + '.log')).open('w') as log:
            with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
                runpy.run_path(str(ROOT / 'prediccion/src' / script), run_name='__main__')
        report['stages'].append({'script': script, 'seconds': round(time.monotonic()-start, 2)})
        print('DONE:', report['stages'][-1], flush=True)
        gc.collect()
        pa.default_memory_pool().release_unused()
    import pandas as pd
    met = pd.read_csv(C.OUT / 'metricas_clima_h1.csv')
    viirs = met[met.era == 'VIIRS']
    report['summary_2015_2025'] = viirs[['auc','auc_base','ap','ap_base','brier','brier_base']].mean().to_dict()
    report['extracted_detections'] = pq.ParquetFile(C.PUNTOS).metadata.num_rows
    act = pd.read_parquet(C.PROC / 'actividad_celda_semana.parquet')
    cells = pd.read_parquet(C.PROC / 'celdas.parquet')
    zones = act.merge(cells[['cell_id','zona_id']], on='cell_id').groupby(['zona_id','semana']).valor.sum().reset_index()
    saved = pd.read_parquet(ROOT / 'backend/data/prediccion/zonas_semana_hist.parquet')
    comparison = zones.merge(saved, on=['zona_id','semana'], how='outer', suffixes=('_new','_saved'), indicator=True)
    report['zone_history_comparison'] = {
        'zones': int(cells.zona_id.nunique()),
        'rows_new': len(zones), 'rows_saved': len(saved),
        'only_new': int((comparison._merge=='left_only').sum()),
        'only_saved': int((comparison._merge=='right_only').sum()),
        'different_values': int(((comparison._merge=='both') & (comparison.valor_new != comparison.valor_saved)).sum()),
    }
    report['stored_summary'] = json.loads((ROOT / 'backend/data/prediccion/validacion.json').read_text())['resumen_h1']
    digest = hashlib.sha256()
    print('SHA256 original...', flush=True)
    with source.open('rb') as stream:
        for chunk in iter(lambda: stream.read(4*1024*1024), b''):
            digest.update(chunk)
    report['source_sha256'] = digest.hexdigest()
    report['status'] = 'completed'
except Exception:
    report['status'] = 'failed'
    report['error'] = traceback.format_exc()
    print(report['error'], flush=True)
finally:
    report['finished_utc'] = datetime.now(timezone.utc).isoformat()
    (run / 'resultado.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2), flush=True)
if report['status'] != 'completed':
    raise SystemExit(1)

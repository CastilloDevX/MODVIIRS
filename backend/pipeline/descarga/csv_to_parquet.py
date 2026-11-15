#!/usr/bin/env python3
"""Valida los CSV por país contra el índice oficial y los convierte a Parquet particionado.

Uso (desde Data/):
  python descarga/csv_to_parquet.py . --countries Mexico Brazil Angola Australia Russian_Federation Democratic_Republic_of_the_Congo
Entrada : csv/<inst>/<año>/<inst>_<año>_<País>.csv     Salida: parquet/<inst>/<año>/<País>.parquet
Procesa un archivo a la vez y por bloques (sin cargar todo en memoria). Reanudable: omite Parquet más
nuevos que su CSV. Escribe meta/validacion_csv.csv (instrument,year,country,expected_bytes,actual_bytes,
rows,status). dtypes: acq_time, confidence, version, satellite, instrument, daynight = texto;
acq_date = date32; type = int16 (nulo si falta); resto numérico float32 (lat/lon float64).
"""
import argparse, csv, os, sys
import pyarrow as pa, pyarrow.csv as pacsv, pyarrow.parquet as pq

TEXT = ["acq_time", "confidence", "version", "satellite", "instrument", "daynight"]
TYPES = {c: pa.string() for c in TEXT}
TYPES.update({"acq_date": pa.date32(), "type": pa.int16(), "latitude": pa.float64(), "longitude": pa.float64()})
for c in ["brightness", "bright_t31", "bright_ti4", "bright_ti5", "scan", "track", "frp"]:
    TYPES[c] = pa.float32()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data_dir")
    ap.add_argument("--countries", nargs="+", default=None)
    ap.add_argument("--instruments", nargs="+", default=["modis", "viirs-snpp", "viirs-jpss1"])
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    d = a.data_dir
    with open(os.path.join(d, "meta", "yearly_summary_files.txt"), newline="", encoding="utf-8") as f:
        sizes = {r["filename"]: int(r["size"]) for r in csv.DictReader(f)}
    wanted = set(a.countries) if a.countries else None

    jobs = []
    for n, s in sizes.items():
        if not n.endswith(".csv"):
            continue
        inst, yr, country = n.split("_", 2)[0], n.split("_", 2)[1], n.split("_", 2)[2][:-4]
        if inst in a.instruments and (wanted is None or country in wanted):
            jobs.append((inst, yr, country, n, s))
    jobs.sort()

    rows, problems = [], 0
    for inst, yr, country, n, s in jobs:
        src = os.path.join(d, "csv", inst, yr, n)
        dst = os.path.join(d, "parquet", inst, yr, f"{country}.parquet")
        actual = os.path.getsize(src) if os.path.exists(src) else -1
        status, nrows = "OK", ""
        if actual < 0:
            status = "FALTA"
        elif actual != s:
            status = "TAMANO_DISTINTO"
        elif actual == 0:
            status = "VACIO"
        if status == "OK":
            if os.path.exists(dst) and os.path.getmtime(dst) >= os.path.getmtime(src) and not a.force:
                nrows = pq.ParquetFile(dst).metadata.num_rows
                status = "OK (ya convertido)"
            else:
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                with open(src, "rb") as fh:
                    cols = fh.readline().decode().strip().split(",")
                ct = {c: TYPES.get(c, pa.string()) for c in cols}
                unk = [c for c in cols if c not in TYPES]
                if unk:
                    print(f"  aviso {n}: columnas sin tipo definido (string): {unk}", file=sys.stderr)
                rd = pacsv.open_csv(src, convert_options=pacsv.ConvertOptions(column_types=ct),
                                    read_options=pacsv.ReadOptions(block_size=1 << 25))
                tmp = dst + ".part"
                nrows = 0
                with pq.ParquetWriter(tmp, rd.schema, compression="zstd") as w:
                    for batch in rd:
                        w.write_batch(batch); nrows += batch.num_rows
                os.replace(tmp, dst)
                if nrows == 0:
                    status = "VACIO"
        if not status.startswith("OK"):
            problems += 1
        rows.append([inst, yr, country, s, actual, nrows, status])
        print(f"{n}: {status} filas={nrows}", flush=True)

    with open(os.path.join(d, "meta", "validacion_csv.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["instrument", "year", "country", "expected_bytes", "actual_bytes", "rows", "status"])
        w.writerows(rows)
    print(f"FIN. archivos esperados={len(jobs)} con problemas={problems}")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()

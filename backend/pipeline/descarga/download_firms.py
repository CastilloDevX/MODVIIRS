#!/usr/bin/env python3
"""Descarga los CSV anuales POR PAIS de FIRMS (MODIS, VIIRS S-NPP, VIIRS NOAA-20). Sin llave, reanudable.

Uso (desde Data/):
  python descarga/download_firms.py . --dry-run            # lista que bajaria y cuanto pesa
  python descarga/download_firms.py .                      # los 6 paises del proyecto (288 CSV, ~16.1 GB)
  python descarga/download_firms.py . --countries Mexico   # solo Mexico (~0.67 GB)
  python descarga/download_firms.py . --workers 3          # descargas en paralelo (default 3)

Salida:
  meta/yearly_summary_files.txt, meta/AttributesReadme.txt   (indice oficial y atributos)
  csv/<inst>/<anio>/<inst>_<anio>_<Pais>.csv
  meta/manifest_csv.csv   (instrument,year,country,file,expected_bytes,actual_bytes,status)
URL: https://firms.modaps.eosdis.nasa.gov/data/country/{inst}/{anio}/{inst}_{anio}_{Pais}.csv
Reanuda con curl -C - y valida el tamano contra el indice oficial. Las conexiones se reinician a menudo: reintenta solo.
"""
import argparse, csv, os, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor

BASE = "https://firms.modaps.eosdis.nasa.gov/data/country"
INDEX = BASE + "/yearly_summary_files.txt"
SIX = ["Democratic_Republic_of_the_Congo", "Brazil", "Angola", "Australia", "Russian_Federation", "Mexico"]


def curl(url, out, retries=8):
    for i in range(retries):
        if subprocess.run(["curl", "-sS", "-f", "-C", "-", "-m", "3000", "-o", out, url]).returncode == 0:
            return True
        time.sleep(3 * (i + 1))
    return False


def fetch(job):
    inst, yr, country, name, size, root = job
    d = os.path.join(root, "csv", inst, yr); os.makedirs(d, exist_ok=True)
    p = os.path.join(d, name)
    have = os.path.getsize(p) if os.path.exists(p) else -1
    if have == size:
        status = "OK (ya existia)"
    else:
        if have > size:                      # archivo corrupto/mas grande: empezar de cero
            os.remove(p)
        curl(f"{BASE}/{inst}/{yr}/{name}", p)
        have = os.path.getsize(p) if os.path.exists(p) else -1
        status = "OK" if have == size else "TAMANO_DISTINTO"
    print(f"{name}: {have}/{size} {status}", flush=True)
    return [inst, yr, country, name, size, have, status]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data_dir")
    ap.add_argument("--countries", nargs="+", default=SIX)
    ap.add_argument("--instruments", nargs="+", default=["modis", "viirs-snpp", "viirs-jpss1"])
    ap.add_argument("--years", nargs=2, type=int, default=[2000, 2100])
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    meta = os.path.join(a.data_dir, "meta"); os.makedirs(meta, exist_ok=True)
    idx = os.path.join(meta, "yearly_summary_files.txt")
    if not os.path.exists(idx) and not curl(INDEX, idx):
        sys.exit("no se pudo bajar el indice")
    if not os.path.exists(os.path.join(meta, "AttributesReadme.txt")):
        curl(BASE + "/AttributesReadme.txt", os.path.join(meta, "AttributesReadme.txt"))
    with open(idx, newline="", encoding="utf-8") as f:
        sizes = {r["filename"]: int(r["size"]) for r in csv.DictReader(f)}

    wanted = set(a.countries); jobs = []
    for name, size in sizes.items():
        if not name.endswith(".csv"):
            continue
        inst, yr, country = name.split("_", 2)[0], name.split("_", 2)[1], name.split("_", 2)[2][:-4]
        if inst in a.instruments and country in wanted and a.years[0] <= int(yr) <= a.years[1]:
            jobs.append((inst, yr, country, name, size, a.data_dir))
    jobs.sort()
    missing = wanted - {j[2] for j in jobs}
    if missing:
        print("AVISO: sin archivos en el indice para:", sorted(missing), file=sys.stderr)
    total = sum(j[4] for j in jobs)
    print(f"{len(jobs)} archivos, {total / 1e9:.2f} GB")
    if a.dry_run:
        for j in jobs[:15]:
            print("  ", j[3], j[4])
        print("   ..." if len(jobs) > 15 else "")
        return

    with ThreadPoolExecutor(a.workers) as ex:
        rows = list(ex.map(fetch, jobs))
    with open(os.path.join(meta, "manifest_csv.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["instrument", "year", "country", "file", "expected_bytes", "actual_bytes", "status"]); w.writerows(rows)
    bad = [r[3] for r in rows if not r[6].startswith("OK")]
    print("FIN. archivos:", len(rows), "con problemas:", bad)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""EDA agregado de FIRMS (MODIS, VIIRS S-NPP, VIIRS NOAA-20): genera tablas pequeñas, NO armoniza.

Uso (desde Data/, dentro del .venv; la carpeta de datos se deduce de la ubicación del script):
  python analisis/02_eda/eda_aggregate.py --countries Mexico     # piloto
  python analisis/02_eda/eda_aggregate.py --workers 2            # los 6 países, 288 archivos (≈ 2-3 GB de RAM por proceso)
  python analisis/02_eda/eda_aggregate.py --finalize-only        # solo reconstruye las tablas finales desde _parts/
  (opcional) pasar la carpeta Data como primer argumento: python analisis/02_eda/eda_aggregate.py <DATA_DIR> ...

Lee  <Data>/parquet/<inst>/<año>/<País>.parquet  (salida de descarga/csv_to_parquet.py), un archivo a la vez, solo
las columnas necesarias. Escribe analisis/02_eda/tablas/_parts/<tabla>/<inst>_<año>_<País>.parquet (reanudable:
omite lo ya hecho) y al final concatena en analisis/02_eda/tablas/<tabla>.parquet (zstd). Objetivo < 100 MB.

Convenciones
  - satellite: Terra, Aqua (MODIS), N (S-NPP), N20 (NOAA-20). tb4 = brightness | bright_ti4; tb5 = bright_t31 | bright_ti5.
  - Hora solar local (LST, minutos) = UTC + lon*4 min. Todo lo de hora se guarda con ORIGEN 06:00 para no partir los
    pasos nocturnos (22:30, 01:30): lst_shift = (UTC_min + 4*lon - 360) mod 1440. Reloj = (lst_shift + 360) mod 1440.
  - Celda = piso de lat/lon (esquina SO de 1°). `cell_lat`, `cell_lon`.
  - Pasada (pass): por satélite y día, las detecciones ordenadas por hora UTC se separan cuando hay un hueco > 20 min
    (inferido: dos órbitas consecutivas están a ~100 min). Solo hay detecciones: es un proxy de cobertura, no cobertura real.
  - Filtros de confidence: MODIS numérico (>=30, >=50, >=80); VIIRS letras (n+h = 'nh', solo h = 'h').
"""
import argparse, csv, json, os, sys, time, warnings
from concurrent.futures import ProcessPoolExecutor, as_completed
import numpy as np, pandas as pd
import pyarrow as pa, pyarrow.compute as pc, pyarrow.parquet as pq

warnings.filterwarnings("ignore")
TABLES = ["profile", "inventory", "daily", "monthly_country", "cell_month", "cell_pass",
          "hist", "pixel", "passes_lat", "persistent"]
DONE = "profile"          # se escribe al final: marca de archivo terminado
PERSIST_MIN_DAYS, PERSIST_TOP = 30, 2000
GAP_MIN = 20              # minutos para separar pasadas
FRP_EDGES = 10 ** np.arange(-2, 4.001, 1 / 8)
K16 = 16384
KP = 65536               # multiplicador para ids de pasada


def nunique_by(k, v):
    """Nº de valores distintos de v por clave entera k (v < 16384). Devuelve (claves, conteos)."""
    u = np.unique(k.astype(np.int64) * K16 + v.astype(np.int64))
    return np.unique(u // K16, return_counts=True)


def cat_map(series, fn, dtype=float):
    """Aplica fn a las categorías (rápido) y devuelve array por fila (nan si nulo)."""
    cats = series.cat.categories
    m = np.array([fn(c) for c in cats] + [np.nan if dtype is float else False], dtype=dtype)
    return m[series.cat.codes.to_numpy()]


def load(path):
    pf = pq.ParquetFile(path)
    names = pf.schema_arrow.names
    tb4 = "brightness" if "brightness" in names else "bright_ti4"
    tb5 = "bright_t31" if "bright_t31" in names else "bright_ti5"
    want = ["latitude", "longitude", "acq_date", "acq_time", "satellite", "confidence", "daynight", "type",
            "version", "frp", "scan", "track", tb4, tb5]
    want = [c for c in want if c in names]
    t = pf.read(columns=want)
    schema = ";".join(f"{f.name}:{f.type}" for f in pf.schema_arrow)
    days = pc.cast(t.column("acq_date"), pa.int32()).to_numpy(zero_copy_only=False)
    t = t.drop_columns(["acq_date"])
    df = t.to_pandas(categories=["acq_time", "satellite", "confidence", "daynight", "version"],
                     self_destruct=True)
    df = df.rename(columns={tb4: "tb4", tb5: "tb5"})
    df["day"] = days
    return df, schema, tb4, tb5, pf.metadata.num_rows


def agg_sat(g, base, inst, dmin):
    """Todas las tablas para UN satélite de un archivo. g: DataFrame (reiniciado)."""
    n = len(g)
    sat = base["satellite"]
    out = {}
    lat, lon = g.latitude.to_numpy(), g.longitude.to_numpy()
    day = g.day.to_numpy()
    dayoff = (day - dmin).astype(np.int64)
    dn = g.daynight.astype(str).to_numpy()
    night = (dn == "N")
    dn_code = night.astype(np.int64)
    frp = g.frp.to_numpy(dtype=np.float64)
    frp0 = np.nan_to_num(frp)
    # tiempo
    tnum = cat_map(g.acq_time, lambda s: float(s) if str(s).isdigit() else np.nan)
    utc = (tnum // 100) * 60 + (tnum % 100)
    lst = np.mod(utc + 4.0 * lon - 360.0, 1440.0)
    # confidence
    cn = cat_map(g.confidence, lambda s: pd.to_numeric(s, errors="coerce"))
    c_n = cat_map(g.confidence, lambda s: str(s).lower() == "n", bool)
    c_h = cat_map(g.confidence, lambda s: str(s).lower() == "h", bool)
    c_l = cat_map(g.confidence, lambda s: str(s).lower() == "l", bool)
    f30, f50, f80 = cn >= 30, cn >= 50, cn >= 80
    fnh, fh = c_n | c_h, c_h
    hi = f80 | fh
    lo = (cn < 30) | c_l
    typ = np.nan_to_num(g["type"].to_numpy(dtype=np.float64), nan=-1).astype(np.int16)
    cell_lat = np.floor(lat).astype(np.int64)
    cell_lon = np.floor(lon).astype(np.int64)
    ckey = (cell_lat + 90) * 361 + (cell_lon + 180)
    ckey2 = ckey * 2 + dn_code
    # meses
    ud, inv = np.unique(day, return_inverse=True)
    mi = ud.astype("datetime64[D]").astype("datetime64[M]").astype(int)
    ym_u = (1970 + mi // 12) * 100 + (mi % 12 + 1)
    ym = ym_u[inv]
    # pasadas
    t_abs = day.astype(np.int64) * 1440 + np.nan_to_num(utc, nan=0).astype(np.int64)
    order = np.argsort(t_abs, kind="stable")
    ts = t_abs[order]
    newp = np.r_[True, np.diff(ts) > GAP_MIN]
    gid = np.empty(n, dtype=np.int64)
    gid[order] = np.cumsum(newp) - 1
    n_pass_total = int(newp.sum())

    # ---------- profile ----------
    p = dict(base)
    p["rows"] = n
    for c in ["latitude", "longitude", "tb4", "tb5", "frp", "scan", "track", "acq_time", "confidence",
              "daynight", "type", "version"]:
        p[f"null_{c}"] = int(g[c].isna().sum())
    p["lat_min"], p["lat_max"] = float(lat.min()), float(lat.max())
    p["lon_min"], p["lon_max"] = float(lon.min()), float(lon.max())
    p["lat_p001"], p["lat_p999"] = [float(x) for x in np.quantile(lat, [.001, .999])]
    p["lon_p001"], p["lon_p999"] = [float(x) for x in np.quantile(lon, [.001, .999])]
    p["day_min"], p["day_max"], p["n_days"] = int(day.min()), int(day.max()), int(ud.size)
    p["n_exact_dup"] = int(g.duplicated().sum())
    lat3, lon3 = np.rint(lat * 1000).astype(np.int64), np.rint(lon * 1000).astype(np.int64)
    lat2, lon2 = np.rint(lat * 100).astype(np.int64), np.rint(lon * 100).astype(np.int64)
    ut = np.nan_to_num(utc, nan=-1).astype(np.int64)
    k3 = ((lat3 + 90000) * 360001 + (lon3 + 180000))
    k2 = ((lat2 + 9000) * 36001 + (lon2 + 18000))
    p["n_dup_0001deg_same_time"] = int(n - np.unique((k3 * 16384 + dayoff) * 1500 + ut).size)
    p["n_dup_001deg_same_time"] = int(n - np.unique((k2 * 16384 + dayoff) * 1500 + ut).size)
    pk = k2 * K16 + dayoff                      # posición 0.01° + día
    up = np.unique(pk * KP + gid)
    _, cnt = np.unique(up // KP, return_counts=True)
    p["n_pos001_day_multipass"] = int((cnt >= 2).sum())
    p["n_pos001_day"] = int(cnt.size)
    p["n_passes"] = n_pass_total
    out["profile"] = pd.DataFrame([p])

    # ---------- inventory ----------
    inv_df = pd.DataFrame({"version": g.version.astype(str).to_numpy(), "daynight": dn,
                           "confidence": g.confidence.astype(str).to_numpy(), "type": typ})
    inv_t = inv_df.groupby(["version", "daynight", "confidence", "type"], observed=True).size().rename("n").reset_index()
    out["inventory"] = inv_t

    # ---------- daily ----------
    d = pd.DataFrame({"daynight": dn, "day": day, "frp": frp0})
    d["fz"] = (frp == 0)
    out["daily"] = d.groupby(["daynight", "day"]).agg(n=("frp", "size"), frp_sum=("frp", "sum"),
                                                     n_frp0=("fz", "sum")).reset_index()

    # ---------- monthly_country (filtros de confidence) ----------
    m = pd.DataFrame({"daynight": dn, "ym": ym, "n_all": 1, "n_ge30": f30, "n_ge50": f50, "n_ge80": f80,
                      "n_nh": fnh, "n_h": fh,
                      "frp_all": frp0, "frp_ge30": frp0 * f30, "frp_ge50": frp0 * f50, "frp_ge80": frp0 * f80,
                      "frp_nh": frp0 * fnh, "frp_h": frp0 * fh})
    out["monthly_country"] = m.groupby(["daynight", "ym"]).sum().reset_index()

    # ---------- cell_month ----------
    cm = pd.DataFrame({"cell_lat": cell_lat.astype(np.int16), "cell_lon": cell_lon.astype(np.int16), "ym": ym,
                       "n": 1, "frp_sum": frp0, "n_night": night, "n_night_lo": night & lo, "n_hi": hi})
    cmg = cm.groupby(["cell_lat", "cell_lon", "ym"]).sum().reset_index()
    # días con detección por celda-mes
    ym_idx = (ym // 100 - 1970) * 12 + (ym % 100 - 1)
    kk, cc = nunique_by(ckey * 400 + ym_idx, dayoff)
    ndays = pd.DataFrame({"_k": kk, "n_days": cc.astype(np.int16)})
    cmg["_k"] = ((cmg.cell_lat + 90) * 361 + (cmg.cell_lon + 180)).astype(np.int64) * 400 + \
                ((cmg.ym // 100 - 1970) * 12 + (cmg.ym % 100 - 1)).astype(np.int64)
    cmg = cmg.merge(ndays, on="_k", how="left").drop(columns="_k")
    for c in ["n", "n_night", "n_night_lo", "n_hi"]:
        cmg[c] = cmg[c].astype(np.int32)
    cmg["frp_sum"] = cmg.frp_sum.astype(np.float32)
    out["cell_month"] = cmg

    # ---------- cell_pass (hora solar local, por celda × día/noche) ----------
    cp = pd.DataFrame({"ck2": ckey2, "lst": lst})
    gb = cp.groupby("ck2")["lst"]
    cpt = pd.DataFrame({"n": gb.size(), "lst_med": gb.median(), "lst_p10": gb.quantile(.1),
                        "lst_p90": gb.quantile(.9)})
    kd2, cd2 = nunique_by(ckey2, dayoff)
    cpt["n_days"] = pd.Series(cd2, index=kd2)
    # nº medio de pasadas distintas por celda-día
    cdk = ckey2 * K16 + dayoff
    uu = np.unique(cdk * KP + gid)
    kcd, npass = np.unique(uu // KP, return_counts=True)
    cell_of_cd = kcd // K16
    mp = pd.Series(npass).groupby(cell_of_cd).mean()
    cpt["mean_passes"] = mp
    cpt = cpt.reset_index()
    cpt["daynight"] = np.where(cpt.ck2 % 2 == 1, "N", "D")
    ck = cpt.ck2 // 2
    cpt["cell_lat"] = (ck // 361 - 90).astype(np.int16)
    cpt["cell_lon"] = (ck % 361 - 180).astype(np.int16)
    cpt = cpt.drop(columns="ck2")
    for c in ["lst_med", "lst_p10", "lst_p90", "mean_passes"]:
        cpt[c] = cpt[c].astype(np.float32)
    cpt["n"] = cpt.n.astype(np.int32); cpt["n_days"] = cpt.n_days.astype(np.int16)
    out["cell_pass"] = cpt

    # ---------- passes_lat: pasadas distintas por celda-día según latitud ----------
    pl = pd.DataFrame({"cell_lat": ((cell_of_cd // 2) // 361 - 90).astype(np.int16),
                       "k": np.minimum(npass, 5).astype(np.int8)})
    out["passes_lat"] = pl.groupby(["cell_lat", "k"]).size().rename("n_celldays").reset_index()

    # ---------- hist (frp, tb4, tb5, utc, lst) ----------
    parts = []

    def addh(var, dnv, bins):
        s = pd.DataFrame({"daynight": dnv, "bin": bins}).groupby(["daynight", "bin"]).size().rename("n").reset_index()
        s.insert(0, "var", var); parts.append(s)

    pos = frp > 0
    idx = np.clip(np.digitize(frp, FRP_EDGES) - 1, 0, len(FRP_EDGES) - 1)
    fb = np.where(pos, FRP_EDGES[idx], 0.0)
    fb = np.where(np.isnan(frp), -1.0, fb)           # -1 = FRP nulo, 0 = FRP cero
    addh("frp", dn, fb)
    for v in ["tb4", "tb5"]:
        a = g[v].to_numpy(dtype=np.float64)
        addh(v, dn, np.where(np.isnan(a), -1.0, np.floor(a)))
    addh("utc", dn, np.floor(np.nan_to_num(utc, nan=-10) / 10) * 10)
    addh("lst", dn, np.floor(np.nan_to_num(lst, nan=-10) / 10) * 10)
    out["hist"] = pd.concat(parts, ignore_index=True)

    # ---------- pixel (scan × track) ----------
    px = pd.DataFrame({"scan": np.round(g.scan.to_numpy(dtype=np.float64), 2),
                       "track": np.round(g.track.to_numpy(dtype=np.float64), 2), "frp_sum": frp0, "n_night": night})
    pxg = px.groupby(["scan", "track"]).agg(n=("frp_sum", "size"), frp_sum=("frp_sum", "sum"),
                                            n_night=("n_night", "sum")).reset_index()
    out["pixel"] = pxg

    # ---------- persistent (0.01°, >= PERSIST_MIN_DAYS días distintos) ----------
    kk2, cc2 = nunique_by(k2, dayoff)
    sel = kk2[cc2 >= PERSIST_MIN_DAYS]
    if sel.size:
        order2 = np.argsort(-cc2[cc2 >= PERSIST_MIN_DAYS], kind="stable")[:PERSIST_TOP]
        sel_k, sel_nd = sel[order2], cc2[cc2 >= PERSIST_MIN_DAYS][order2]
        m_ = np.isin(k2, sel_k)
        ps = pd.DataFrame({"k2": k2[m_], "frp": frp0[m_], "night": night[m_], "hi": hi[m_], "typ": typ[m_],
                           "lat": lat[m_], "lon": lon[m_]})
        pg = ps.groupby("k2").agg(n=("frp", "size"), frp_mean=("frp", "mean"), n_night=("night", "sum"),
                                  n_hi=("hi", "sum"), type_mode=("typ", lambda s: s.mode().iat[0]),
                                  lat=("lat", "mean"), lon=("lon", "mean")).reset_index()
        pg["n_days"] = pg.k2.map(dict(zip(sel_k, sel_nd))).astype(np.int16)
        out["persistent"] = pg.drop(columns="k2")
    else:
        out["persistent"] = pd.DataFrame(columns=["n", "frp_mean", "n_night", "n_hi", "type_mode", "lat", "lon", "n_days"])
    return out


def process_one(job):
    d, inst, yr, country, outdir, force = job
    key = f"{inst}_{yr}_{country}"
    done = os.path.join(outdir, "_parts", DONE, key + ".parquet")
    if os.path.exists(done) and not force:
        return key, "omitido", 0.0
    t0 = time.time()
    src = os.path.join(d, "parquet", inst, yr, f"{country}.parquet")
    df, schema, tb4, tb5, nrows = load(src)
    dmin = int(df.day.min())
    res = {t: [] for t in TABLES}
    for sat, g in df.groupby("satellite", observed=True):
        g = g.reset_index(drop=True)
        base = {"instrument": inst, "year": int(yr), "country": country, "satellite": str(sat)}
        r = agg_sat(g, base, inst, dmin)
        for t, x in r.items():
            if t != "profile":
                for k, v in base.items():
                    x.insert(list(base).index(k), k, v)
            res[t].append(x)
    for t in TABLES:
        x = pd.concat(res[t], ignore_index=True)
        if t == "profile":
            x["schema"] = schema; x["tb4_name"] = tb4; x["tb5_name"] = tb5
            x["parquet_rows"] = nrows
        os.makedirs(os.path.join(outdir, "_parts", t), exist_ok=True)
        tmp = os.path.join(outdir, "_parts", t, key + ".tmp")
        x.to_parquet(tmp, index=False, compression="zstd")
        os.replace(tmp, os.path.join(outdir, "_parts", t, key + ".parquet"))
    return key, "ok", time.time() - t0


def finalize(outdir, keep_parts):
    tot = 0
    for t in TABLES:
        fs = sorted(os.listdir(os.path.join(outdir, "_parts", t))) if os.path.isdir(os.path.join(outdir, "_parts", t)) else []
        fs = [f for f in fs if f.endswith(".parquet")]
        if not fs:
            continue
        x = pd.concat([pd.read_parquet(os.path.join(outdir, "_parts", t, f)) for f in fs], ignore_index=True)
        if "day" in x.columns:
            x["date"] = pd.to_datetime(x.day, unit="D").dt.date; x = x.drop(columns="day")
        if t == "profile":
            for c in ["day_min", "day_max"]:
                x[c.replace("day", "date")] = pd.to_datetime(x[c], unit="D").dt.date
            x = x.drop(columns=["day_min", "day_max"])
        x.to_parquet(os.path.join(outdir, f"{t}.parquet"), index=False, compression="zstd", compression_level=9)
        s = os.path.getsize(os.path.join(outdir, f"{t}.parquet")); tot += s
        print(f"  {t:16s} {len(x):>10,d} filas  {s/1e6:7.2f} MB", flush=True)
    print(f"TOTAL tablas finales: {tot/1e6:.1f} MB")
    if not keep_parts:
        print("(se conservan _parts/ para reanudar; bórralos cuando termines: analisis/02_eda/tablas/_parts)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data_dir", nargs="?", default=None, help="carpeta Data (default: dos niveles sobre este script)")
    ap.add_argument("--countries", nargs="+", default=["Democratic_Republic_of_the_Congo", "Brazil", "Angola",
                                                       "Australia", "Russian_Federation", "Mexico"])
    ap.add_argument("--instruments", nargs="+", default=["modis", "viirs-snpp", "viirs-jpss1"])
    ap.add_argument("--years", nargs=2, type=int, default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--finalize-only", action="store_true")
    ap.add_argument("--keep-parts", action="store_true")
    a = ap.parse_args()
    here = os.path.dirname(os.path.abspath(__file__))
    d = a.data_dir or os.path.abspath(os.path.join(here, "..", ".."))
    outdir = a.out or os.path.join(here, "tablas")
    os.makedirs(outdir, exist_ok=True)
    if not a.finalize_only:
        with open(os.path.join(d, "meta", "validacion_csv.csv"), newline="", encoding="utf-8") as f:
            ok = [r for r in csv.DictReader(f) if r["status"].startswith("OK")]
        jobs = [(d, r["instrument"], r["year"], r["country"], outdir, a.force) for r in ok
                if r["instrument"] in a.instruments and r["country"] in a.countries
                and (a.years is None or a.years[0] <= int(r["year"]) <= a.years[1])]
        jobs.sort(key=lambda j: (j[2], j[1], j[3]))
        print(f"{len(jobs)} archivos; salida: {outdir}", flush=True)
        t0 = time.time()
        if a.workers > 1:
            with ProcessPoolExecutor(a.workers) as ex:
                futs = [ex.submit(process_one, j) for j in jobs]
                for i, f in enumerate(as_completed(futs), 1):
                    k, s, dt = f.result(); print(f"[{i}/{len(jobs)}] {k}: {s} {dt:.1f}s", flush=True)
        else:
            for i, j in enumerate(jobs, 1):
                k, s, dt = process_one(j); print(f"[{i}/{len(jobs)}] {k}: {s} {dt:.1f}s", flush=True)
        print(f"Procesado en {(time.time()-t0)/60:.1f} min")
    finalize(outdir, a.keep_parts)


if __name__ == "__main__":
    main()

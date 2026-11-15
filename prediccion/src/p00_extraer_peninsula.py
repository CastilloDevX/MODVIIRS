"""p00 - Extrae de la capa de puntos de Alexis (6 paises, ~2.9 GB) solo Mexico en el recuadro de la peninsula.
Uso: python prediccion/src/p00_extraer_peninsula.py   (~15 s; usa estadisticas de row group para saltar paises)"""
import pyarrow as pa, pyarrow.compute as pc, pyarrow.parquet as pq
import config as C

f = pq.ParquetFile(C.ALEXIS_PUNTOS)
md = f.metadata
ci = [md.schema.column(i).name for i in range(md.num_columns)].index("country")
rgs = [i for i in range(md.num_row_groups)
       if (st := md.row_group(i).column(ci).statistics) is not None and st.min <= "Mexico" <= st.max]
cols = ["latitude", "longitude", "acq_date_d", "year", "month", "country", "sensor_group", "satellite",
        "conf_class", "frp", "daynight", "type", "is_persistent", "cy", "cx"]
partes = []
for i in rgs:
    t = f.read_row_group(i, columns=cols)
    m = pc.and_(pc.equal(t["country"], "Mexico"), pc.and_(
        pc.and_(pc.greater_equal(t["longitude"], C.W), pc.less_equal(t["longitude"], C.E)),
        pc.and_(pc.greater_equal(t["latitude"], C.S), pc.less_equal(t["latitude"], C.N))))
    partes.append(t.filter(m))
tab = pa.concat_tables(partes)
pq.write_table(tab, C.PUNTOS)
print(f"{tab.num_rows:,} detecciones -> {C.PUNTOS}")

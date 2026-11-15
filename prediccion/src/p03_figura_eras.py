"""p03 - Figura del pitch: % de zona-semanas 'anomalas' con historia MEZCLADA (MODIS y VIIRS juntos,
sin armonizar) vs historia POR ERA (normalizacion de Alexis)."""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import config as C
from anomalias import cargar_matriz, percentiles_historicos, anomalias

Z, sem, _ = cargar_matriz()
filas = {}
for nombre, por_era in [("mezclada", False), ("por_era", True)]:
    _, P90, _ = percentiles_historicos(Z, sem, por_era=por_era)
    A = anomalias(Z, P90)
    with np.errstate(all="ignore"):
        tasa = pd.Series(np.nanmean(A, axis=1), index=sem.semana)
    g = tasa.groupby(sem.anio.to_numpy())
    filas[nombre] = (g.mean() * 100).where(g.count() >= 26)      # anio con >= 26 semanas con linea base
t = pd.DataFrame(filas)
t.to_csv(C.OUT / "tasa_anomalias_mezclada_vs_por_era.csv")
fig, ax = plt.subplots(figsize=(10, 4.5))
ax.plot(t.index, t.mezclada, "o-", color="tab:red", label="Historia mezclada MODIS+VIIRS (sin armonizar)")
ax.plot(t.index, t.por_era, "o-", color="tab:blue", label="Normalizada por era (armonización)")
ax.axvline(2012, color="gray", ls=":"); ax.text(2012.2, ax.get_ylim()[1] * 0.92, "entra VIIRS", color="gray")
ax.axvspan(2011.9, 2014.9, color="gray", alpha=.1)
ax.set_ylabel("% de zona-semanas marcadas como 'anómalas'")
ax.set_title("Sin armonizar, la alerta temprana da falsas anomalías después de 2012")
ax.grid(alpha=.3); ax.legend()
fig.tight_layout(); fig.savefig(C.FIG / "falsas_anomalias_mezclada_vs_por_era.png", dpi=140)
print(t.round(1).to_string())

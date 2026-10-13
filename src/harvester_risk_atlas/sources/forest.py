"""Tree-cover loss by Philippine province (Global Forest Watch, 2001–2023).

Hansen et al. (2013) / UMD tree-cover loss, summarised by GFW to GADM
level 1 (the 81 provinces). Licence: CC BY 4.0. The province names match
the ``gadm.level1`` names GBIF attaches to each record, so records join
without a boundary layer.

The rate used is total loss 2001–2023 divided by year-2000 extent, at the
30% canopy threshold (GFW's default).
"""
from __future__ import annotations

import pandas as pd

from ..config import DATA_PROCESSED, DATA_RAW
from .http import session

URL = "https://gfw2-data.s3.amazonaws.com/country-pages/country_stats/download/2023/PHL.xlsx"
RAW = DATA_RAW / "gfw" / "PHL_2023.xlsx"
PROCESSED = DATA_PROCESSED / "v2" / "province_forest_loss.csv"
THRESHOLD = 30
YEARS = range(2001, 2024)
CITATION = (
    "Hansen MC et al. (2013) High-resolution global maps of 21st-century forest cover change. "
    "Science 342: 850–853. Province statistics from Global Forest Watch (2024), CC BY 4.0."
)


def province_loss(offline: bool = False) -> pd.DataFrame:
    """Province, extent 2000 (ha), loss 2001–2023 (ha), and loss rate."""
    if PROCESSED.exists():
        return pd.read_csv(PROCESSED)
    if not RAW.exists():
        if offline:
            raise FileNotFoundError(RAW)
        RAW.parent.mkdir(parents=True, exist_ok=True)
        r = session().get(URL, timeout=120)
        r.raise_for_status()
        RAW.write_bytes(r.content)
    d = pd.read_excel(RAW, sheet_name="Subnational 1 tree cover loss")
    d = d[d["threshold"] == THRESHOLD]
    loss_cols = [f"tc_loss_ha_{y}" for y in YEARS]
    out = pd.DataFrame(
        {
            "province": d["subnational1"],
            "extent_2000_ha": d["extent_2000_ha"],
            "loss_2001_2023_ha": d[loss_cols].sum(axis=1),
        }
    )
    out["loss_rate"] = (out["loss_2001_2023_ha"] / out["extent_2000_ha"]).where(out["extent_2000_ha"] > 0)
    out = out.sort_values("province").reset_index(drop=True)
    PROCESSED.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(PROCESSED, index=False)
    return out

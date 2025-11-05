# utils/data_loader.py
import pandas as pd
from pathlib import Path
from functools import lru_cache

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

@lru_cache(maxsize=1)
def load_pax_data():
    return {
        "pax": pd.read_csv(DATA_DIR / "pax.csv"),
        "pax_topics": pd.read_csv(DATA_DIR / "all_pax_topics_no_imp.csv"),
        "pax_id_to_con": pd.read_csv(DATA_DIR / "pax_id_to_con_info.csv"),
        "signatories": pd.read_csv(DATA_DIR / "paax_signatory_v0.2_internal.csv"),
        "con_ent": pd.read_csv(DATA_DIR / "country_entity_geo_v9.csv"),
    }

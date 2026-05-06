# utils/data_loader.py
import pandas as pd
import numpy as np
from pathlib import Path
from functools import lru_cache

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

def add_category_level_rows(pax_topics):
    """
    Add synthetic category-level rows to pax_topics.
    For each AgtId-Category combination, create a row where:
    - value = 1 if ANY issue under that category has value > 0 for that AgtId
    - value = 0 otherwise

    This ensures that selecting a bare category works correctly in the UI.
    """
    category_rows = []

    # Get unique categories (only those that are not NaN)
    categories = pax_topics[pax_topics['category'].notna()]['category'].unique()

    for category in categories:
        # Get all rows for this category
        category_data = pax_topics[pax_topics['category'] == category].copy()

        # For each unique AgtId in this category, determine if it has any value > 0
        for agt_id in category_data['AgtId'].unique():
            agt_category_data = category_data[category_data['AgtId'] == agt_id]
            # Check if any issue/subissue under this category has value > 0
            has_mention = (agt_category_data['value'] > 0).any()
            value = 1 if has_mention else 0

            # Create synthetic category-level row
            row = {
                'AgtId': agt_id,
                'variable': None,
                'value': value,
                'level_0': None,
                'ID': None,
                'label': None,
                'type': None,
                'category': category,
                'issue': None,
                'sub-issue': None,
                'definition': None,
                'max': None,
                'issue_label': None,
                'subissue_label': None,
            }
            category_rows.append(row)

    # Create dataframe from category rows and append
    if category_rows:
        category_df = pd.DataFrame(category_rows)
        pax_topics_with_categories = pd.concat([pax_topics, category_df], ignore_index=True)
        return pax_topics_with_categories

    return pax_topics

@lru_cache(maxsize=1)
def load_pax_data():
    pax_topics = pd.read_csv(DATA_DIR / "all_pax_topics_no_imp.csv")

    # Remove powersharing state/substate level rows (Pps*:St or Pps*:Sub)
    # These are flags, not substantive topics
    pax_topics = pax_topics[
        ~(pax_topics['variable'].fillna('').str.contains(r'^Pps.*:(St|Sub)$', regex=True))
    ]

    pax_topics = add_category_level_rows(pax_topics)

    return {
        "pax": pd.read_csv(DATA_DIR / "pax.csv"),
        "pax_topics": pax_topics,
        "pax_id_to_con": pd.read_csv(DATA_DIR / "pax_id_to_con_info.csv"),
        "signatories": pd.read_csv(DATA_DIR / "paax_signatory_v0.3_internal.csv"),
        "con_ent": pd.read_csv(DATA_DIR / "country_entity_geo.csv"),
        "pax_wide": pd.read_csv(DATA_DIR / "pax_data_2257_agreements_v10.csv"),
        "wgg": pd.read_csv(DATA_DIR / "pax_wgg_data_494_agreements_v10.csv")
    }

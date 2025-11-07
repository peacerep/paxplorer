# server/topics.py
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from shiny import reactive, render, ui
from shinywidgets import output_widget, render_widget
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
from utils.png_export_utils import export_with_branding, get_data_version, LOGO_POSITIONS

# ---------------------------------------------------------------------
# CONSTANTS & CONFIG
# ---------------------------------------------------------------------

from utils.data_loader import load_pax_data

data = load_pax_data()
pax = data["pax"]
pax_topics = data["pax_topics"]
pax_id_to_con = data["pax_id_to_con"]
con_ent = data["con_ent"]
signatories = data["signatories"]

# DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# # Data
# pax = pd.read_csv("data/pax.csv")
# pax_topics = pd.read_csv("data/all_pax_topics_no_imp.csv")
# pax_id_to_con = pd.read_csv("data/pax_id_to_con_info.csv")
# con_ent = pd.read_csv("data/country_entity_geo_v9.csv")

# try:
#     signatories = pd.read_csv("data/paax_signatory_v0.2_internal.csv")
# except FileNotFoundError:
#     print("Signatory file missing — actor charts will be limited.")
#     signatories = pd.DataFrame()

# Colors
stage_order = [
    "Pre-negotiation/process", "Ceasefire",
    "Framework-substantive, partial", "Framework-substantive, comprehensive",
    "Implementation", "Renewal", "Other"
]
stage_color_map = {
    "Pre-negotiation/process": "#016099",
    "Ceasefire": "#df1f36",
    "Framework-substantive, partial": "#fd8189",
    "Framework-substantive, comprehensive": "#fdd900",
    "Implementation": "#3aae2a",
    "Renewal": "#7b8ad6",
    "Other": "#c0de88"
}
type_color_map = {
    "Intrastate": "#0b5740",
    "Local": "#ac4399",
    "Interstate/mixed": "#df1f36",
    "Interstate": "#f28b20"
}

# Branding positions (custom for this page)
TOPICS_LOGO_POSITION = (0.95, 0.97, 0.078, 0.078)
TOPICS_FILTER_TEXT_POSITION = (0.5, 0.004)
TOPICS_VERSION_POSITION = (0.98, 0.005)


# ---------------------------------------------------------------------
# SERVER LOGIC
# ---------------------------------------------------------------------
def server(input, output, session):

    # -------------------------------------------------------
    #  HELPERS
    # -------------------------------------------------------
    def get_colors_for_grouping(group_mode, categories):
        if group_mode == "Stage":
            return [stage_color_map.get(cat, "#cccccc") for cat in categories]
        return [type_color_map.get(cat, "#cccccc") for cat in categories]

    @reactive.calc
    def get_topics_filter_text():
        """Combine general + topic filters for PNG export"""
        selected = input.selected_topics()
        if not selected:
            return "Showing all data"

        parts = []
        for topic in selected[:3]:
            clean_text = topic.replace("CATEGORY:", "").replace("ISSUE:", "").strip()
            parts.append(clean_text)
        if len(selected) > 3:
            parts.append(f"+ {len(selected)-3} more")

        return f"Topics: {' | '.join(parts)}"
    
    @reactive.calc
    def topics_title_prefix():
        """Return a clean, readable title for selected topics respecting hierarchy and AND/OR logic."""
        selected = input.selected_topics()
        if not selected:
            return "All Topics"

        clean = []
        for t in selected:
            # Clean up category/issue markers
            t = (
                t.replace("CATEGORY:", "")
                .replace("ISSUE:", "")
                .replace("SUB-ISSUE:", "")
                .strip()
            )

            # Handle hierarchy depth
            parts = [p.strip() for p in t.split(">") if p.strip()]
            if len(parts) == 1:
                label = parts[0]
            elif len(parts) == 2:
                label = parts[-1]
            else:  # len >= 3
                label = " > ".join(parts[-2:])
            clean.append(label)

        # Remove duplicates, preserve order
        clean = list(dict.fromkeys(clean))

        # --- Combine into a readable string ---
        if len(clean) == 1:
            return clean[0]
        elif len(clean) == 2:
            return f"{clean[0]}, {clean[1]}"
        elif len(clean) == 3:
            return f"{clean[0]}, {clean[1]}, {clean[2]}"
        else:
            return f"{', '.join(clean[:3])} + {len(clean) - 3} more"

    
    # -------------------------------------------------------
    #  POPULATE TOPIC AND FILTER DROPDOWNS
    # -------------------------------------------------------
    @reactive.calc
    def topic_hierarchy():
        """Build hierarchical topic structure"""
        topics_with_values = pax_topics[pax_topics['value'] > 0]
        hierarchy = {}

        for _, row in topics_with_values.iterrows():
            category = row['category']
            issue = row['issue_label']
            subissue = row['subissue_label']

            if pd.notna(category):
                hierarchy.setdefault(category, {})
                if pd.notna(issue):
                    hierarchy[category].setdefault(issue, [])
                    if pd.notna(subissue) and subissue not in hierarchy[category][issue]:
                        hierarchy[category][issue].append(subissue)
        return hierarchy


    @reactive.calc
    def topic_choices():
        """Flatten hierarchical structure for selectize"""
        hierarchy = topic_hierarchy()
        choices = []
        for category, issues in hierarchy.items():
            choices.append(f"{category}")
            for issue, subissues in issues.items():
                choices.append(f"{category} > {issue}")
                for sub in subissues:
                    choices.append(f"{category} > {issue} > {sub}")
        return choices


    @reactive.effect
    def _populate_topic_dropdown():
        """Update topic dropdown choices"""
        ui.update_selectize("selected_topics", choices=topic_choices(), selected=[])

    @render.ui
    def topics_summary_stats():
        selected = input.selected_topics()
        if not selected:
            return ui.div(
                "No topics selected",
                style="color: #6c757d; font-style: italic;"
            )

        total_agreements = pax["AgtId"].nunique()
        filtered_agreements_count = filtered_agreements()["AgtId"].nunique()
        percentage = (filtered_agreements_count / total_agreements * 100) if total_agreements > 0 else 0

        topic_summary = []
        for topic in selected[:3]:
            clean = topic.replace("CATEGORY:", "").replace("ISSUE:", "").replace("SUB-ISSUE:", "").strip()
            topic_summary.append(clean)
        if len(selected) > 3:
            topic_summary.append(f"+ {len(selected) - 3} more")

        topics_text = " | ".join(topic_summary)

        return ui.div(
            ui.div(
                ui.tags.strong("Selected Topics: ", style="color: #091f40;"),
                topics_text,
                style="margin-bottom: 5px;"
            ),
            ui.div(
                ui.tags.strong(f"{filtered_agreements_count:,} agreements ({percentage:.1f}%)", style="color: #df1f36;"),
                " match selected topics",
                style="font-size: 0.9em; color: #666;"
            ),
            style="background-color: white; padding: 10px; border-radius: 4px; border-left: 3px solid #df1f36;"
        )



    # -------------------------------------------------------
    #  POPULATE GENERAL FILTER DROPDOWNS
    # -------------------------------------------------------
    @reactive.calc
    def region_choices():
        return sorted(pax["Reg"].dropna().unique().tolist())

    @reactive.calc
    def country_choices():
        return sorted(pax_id_to_con["name"].dropna().unique().tolist())

    @reactive.calc
    def agt_type_choices():
        return sorted(pax["agt_type"].dropna().unique().tolist())

    @reactive.calc
    def peace_process_choices():
        return sorted(pax["PPName"].dropna().unique().tolist())

    @reactive.calc
    def stage_choices():
        return sorted(pax["stage_label"].dropna().unique().tolist())

    @reactive.calc
    def year_range():
        min_year = int(pax["year"].min())
        max_year = int(pax["year"].max())
        return [min_year, max_year]


    @reactive.effect
    def _populate_general_filters():
        """Populate all general filter dropdowns"""
        ui.update_selectize("topics_region", choices=region_choices(), selected=[])
        ui.update_selectize("topics_country", choices=country_choices(), selected=[])
        ui.update_selectize("topics_agt_type", choices=agt_type_choices(), selected=[])
        ui.update_selectize("topics_peace_process", choices=peace_process_choices(), selected=[])
        ui.update_selectize("topics_stage", choices=stage_choices(), selected=[])

        year_min, year_max = year_range()
        ui.update_slider("topics_year_range", min=year_min, max=year_max, value=[year_min, year_max])

    
    

    # -------------------------------------------------------
    #  REACTIVE DATA
    # -------------------------------------------------------
    @reactive.calc
    def filtered_agreements():
        """Filter agreements by selected topics and general filters (supports AND/OR mode)."""
        df = pax.copy()

        # --- Helper for normalized text ---
        def norm(x):
            return str(x).strip().lower() if pd.notna(x) else ""

        # --- General filters ---
        countries = input.topics_country()
        if countries:
            agt_ids = pax_id_to_con[pax_id_to_con["name"].isin(countries)]["AgtId"].unique()
            df = df[df["AgtId"].isin(agt_ids)]

        agt_types = input.topics_agt_type()
        if agt_types:
            df = df[df["agt_type"].isin(agt_types)]

        regions = input.topics_region()
        if regions:
            df = df[df["Reg"].isin(regions)]

        peace_processes = input.topics_peace_process()
        if peace_processes:
            df = df[df["PPName"].isin(peace_processes)]

        stages = input.topics_stage()
        if stages:
            df = df[df["stage_label"].isin(stages)]

        yr = input.topics_year_range()
        if yr:
            df = df[(df["year"] >= yr[0]) & (df["year"] <= yr[1])]

        # --- Topic filtering ---
        selected = input.selected_topics()
        if not selected:
            return df

        topics_df = pax_topics.copy()
        topics_df["category_norm"] = topics_df["category"].apply(norm)
        topics_df["issue_norm"] = topics_df["issue_label"].apply(norm)
        topics_df["subissue_norm"] = topics_df["subissue_label"].apply(norm)

        categories, issues, subissues = [], [], []
        for t in selected:
            parts = [p.strip() for p in t.split(">")]
            if len(parts) == 1:
                categories.append(norm(parts[0]))
            elif len(parts) == 2:
                issues.append({"category": norm(parts[0]), "issue": norm(parts[1])})
            elif len(parts) == 3:
                subissues.append({
                    "category": norm(parts[0]),
                    "issue": norm(parts[1]),
                    "subissue": norm(parts[2]),
                })

        match_mode = input.topics_match_mode()  # False = OR, True = AND

        # --- OR logic (default) ---
        if not match_mode:
            topic_mask = pd.Series(False, index=topics_df.index)

            if categories:
                topic_mask |= topics_df["category_norm"].isin(categories) & (topics_df["value"] > 0)
            for i in issues:
                topic_mask |= (
                    (topics_df["category_norm"] == i["category"]) &
                    (topics_df["issue_norm"] == i["issue"]) &
                    (topics_df["value"] > 0)
                )
            for s in subissues:
                topic_mask |= (
                    (topics_df["category_norm"] == s["category"]) &
                    (topics_df["issue_norm"] == s["issue"]) &
                    (topics_df["subissue_norm"] == s["subissue"]) &
                    (topics_df["value"] > 0)
                )

            agt_ids = topics_df.loc[topic_mask, "AgtId"].unique()
            filtered = df[df["AgtId"].isin(agt_ids)]
            return filtered

        # --- AND logic (agreements must include ALL selected topics) ---
        else:
            # For AND logic, start with all agreements and filter down
            valid_agt_ids = set(df["AgtId"].unique())

            for t in selected:
                parts = [p.strip() for p in t.split(">")]
                cat = norm(parts[0])
                issue = norm(parts[1]) if len(parts) > 1 else None
                subissue = norm(parts[2]) if len(parts) > 2 else None

                topic_mask = (
                    (topics_df["category_norm"] == cat) &
                    (topics_df["value"] > 0)
                )
                if issue:
                    topic_mask &= topics_df["issue_norm"] == issue
                if subissue:
                    topic_mask &= topics_df["subissue_norm"] == subissue

                agt_ids = set(topics_df.loc[topic_mask, "AgtId"].unique())
                valid_agt_ids &= agt_ids  # intersection (AND)

            filtered = df[df["AgtId"].isin(valid_agt_ids)]
            return filtered
        
    @reactive.effect
    @reactive.event(input.topics_reset_filters)
    def _():
        """Reset all topic-related filters and controls to their default states."""

        # --- Main topic selectors ---
        ui.update_selectize("selected_topics", selected=[])

        # --- AND / OR logic toggle ---
        if hasattr(input, "topics_logic"):
            ui.update_radio_buttons("topics_logic", selected="OR")  # or whatever your default is

        # --- Custom title input (if present) ---
        if hasattr(input, "topics_custom_title"):
            ui.update_text("topics_custom_title", value="")

        # You can add other ui.update_* calls here if you add more topic controls later.


    @reactive.calc
    def topics_time_data():
        df = filtered_agreements()
        if df.empty:
            return pd.DataFrame()

        yearly = df.groupby("year")["AgtId"].nunique().reset_index(name="agreements")
        all_yearly = pax.groupby("year")["AgtId"].nunique().reset_index(name="total")
        merged = all_yearly.merge(yearly, on="year", how="left").fillna(0)
        merged["percentage"] = merged["agreements"] / merged["total"] * 100
        return merged

    @reactive.calc
    def topics_grouped_time_data():
        df = filtered_agreements()
        if df.empty:
            return pd.DataFrame()

        group_col = "stage_label" if input.topics_group_mode() == "Stage" else "agt_type"
        all_years = list(range(1990, 2025))
        all_groups = stage_order if input.topics_group_mode() == "Stage" else sorted(
            pax["agt_type"].dropna().unique().tolist()
        )

        grid = pd.MultiIndex.from_product([all_years, all_groups],
                                          names=["year", group_col]).to_frame(index=False)
        grouped = df.groupby(["year", group_col])["AgtId"].nunique().reset_index(name="count")
        result = grid.merge(grouped, on=["year", group_col], how="left").fillna(0)
        result["count"] = result["count"].astype(int)
        pivot_df = result.pivot(index="year", columns=group_col, values="count").fillna(0)
        if input.topics_group_mode() == "Stage":
            pivot_df = pivot_df[[c for c in stage_order if c in pivot_df.columns]]
        return pivot_df.reset_index()

    @reactive.calc
    def topics_stage_data():
        df = filtered_agreements()
        all_stages_df = pd.DataFrame({"stage_label": stage_order})
        if input.topics_stage_mode() == "Count":
            counts = df.groupby("stage_label")["AgtId"].nunique().reset_index(name="count")
            merged = all_stages_df.merge(counts, on="stage_label", how="left").fillna(0)
            merged["count"] = merged["count"].astype(int)
            return merged
        else:
            filtered = df.groupby("stage_label")["AgtId"].nunique().reset_index(name="filtered_count")
            all_data = pax.groupby("stage_label")["AgtId"].nunique().reset_index(name="all_count")
            merged = all_stages_df.merge(filtered, on="stage_label", how="left").fillna(0)
            merged = merged.merge(all_data, on="stage_label", how="left").fillna(0)
            total_filtered = df["AgtId"].nunique() or 1
            total_all = pax["AgtId"].nunique() or 1
            merged["filtered_percentage"] = merged["filtered_count"] / total_filtered * 100
            merged["all_percentage"] = merged["all_count"] / total_all * 100
            return merged

    @reactive.calc
    def topics_peace_process_data():
        df = filtered_agreements()
        if df.empty:
            return pd.DataFrame()
        n = input.topics_top_processes() or 20
        return (
            df.groupby("PPName")["AgtId"].nunique().reset_index(name="count")
            .sort_values("count", ascending=True)
            .tail(int(n))
        )

    @reactive.calc
    def topics_actor_data():
        df = filtered_agreements()
        if df.empty or signatories.empty:
            return pd.DataFrame()

        actor_data = signatories[signatories["AgtId"].isin(df["AgtId"])]
        summary = (actor_data.groupby(["actor_name", "practical_third"])["AgtId"]
                   .nunique().reset_index(name="count"))
        summary = summary.sort_values("count", ascending=False).drop_duplicates("actor_name")
        return summary.sort_values("count", ascending=True).tail(20)

    @reactive.calc
    def topics_map_data():
        df = filtered_agreements()  # Use the full filtered data (general + topics)
        if df.empty:
            return pd.DataFrame()
        
        # Get country data for agreements
        iso_long = pd.melt(df, id_vars=["AgtId"], value_vars=["Loc1ISO", "Loc2ISO"]).dropna()
        iso_grouped = iso_long.groupby("value")["AgtId"].nunique().reset_index(name="Number of Agreements")
        
        # Merge with geographic data
        geo = iso_grouped.merge(con_ent, left_on="value", right_on="iso_code", how="left").dropna(
            subset=["central_latitude", "central_longitude"]
        )
        return geo

    @render_widget
    def topics_map():
        geo = topics_map_data()
        
        if geo.empty:
            fig = go.Figure()
            fig.add_annotation(text="No geographic data available for selected topics", 
                            xref="paper", yref="paper", 
                            x=0.5, y=0.5, showarrow=False, font=dict(size=16))
            fig.update_layout(height=500)
            return fig
        
        # Create scatter_geo plot
        fig = px.scatter_geo(
            geo, 
            lat='central_latitude', 
            lon='central_longitude', 
            hover_name="name", 
            size="Number of Agreements",
            hover_data={"Number of Agreements": True, "central_latitude": False, "central_longitude": False},
            projection="natural earth"
        )
        
        # Update layout
        fig.update_layout(
            title={
                "text": f"Geographic Distribution of Agreements with {topics_title_prefix()}",
                "x": 0.5,
                "xanchor": "center",
                "font": {"size": 18}
            },
            height=500
        )
        
        # Style the markers
        fig.update_traces(
            marker=dict(
                color="#091F40",
                line=dict(width=1, color='white'),
                sizemin=5,
                sizemode='area'
            )
        )
        
        # Style the geography
        fig.update_geos(
            landcolor="#f0e8d9",
            showframe=False,
            showcoastlines=True,
            coastlinecolor="white"
        )
        
        return fig

    # Map export functions
    @render.download(filename="topics_map.csv")
    def topics_export_map_csv():
        geo = topics_map_data()
        if not geo.empty:
            export_data = geo[['value', 'name', 'Number of Agreements', 'central_latitude', 'central_longitude']].copy()
            export_data.columns = ['ISO_Code', 'Country_Name', 'Number_of_Agreements', 'Latitude', 'Longitude']
        else:
            export_data = pd.DataFrame(columns=['ISO_Code', 'Country_Name', 'Number_of_Agreements', 'Latitude', 'Longitude'])
        
        csv_string = export_data.to_csv(index=False)
        return io.BytesIO(csv_string.encode('utf-8'))


    # -------------------------------------------------------
    #  FIGURE CREATION FUNCTIONS
    # -------------------------------------------------------
    def make_topics_over_time_figure():
        time_data = topics_time_data()
        fig, ax = plt.subplots(figsize=(14, 8))

        if time_data.empty:
            ax.text(0.5, 0.5, "No data available", ha="center", va="center", transform=ax.transAxes)
            return fig

        if input.topics_time_mode() == "Percentage":
            y_values, color, y_title = time_data["percentage"], "#7b8ad6", "Percentage of All Agreements"
            labels = time_data["percentage"].round(1).astype(str) + "%"
        else:
            y_values, color, y_title = time_data["agreements"], "#091f40", "Number of Agreements"
            labels = time_data["agreements"].astype(int).astype(str)

        ax.plot(time_data["year"], y_values, marker="o", color=color, linewidth=2, markersize=6)

        # --- Add data labels above markers ---
        for x, y, label in zip(time_data["year"], y_values, labels):
            if y > 0:
                ax.text(x, y + max(y_values) * 0.02, label, ha="center", va="bottom", fontsize=8)

        ax.set_xlabel("Year", fontsize=12)
        ax.set_ylabel(y_title, fontsize=12)
        ax.set_title(f"Agreements with {topics_title_prefix()} Over Time", fontsize=16, fontweight="bold", pad=20, y=1.01)
        ax.grid(alpha=0.3)
        plt.ylim(0, y_values.max() * 1.15)
        plt.tight_layout()
        return fig


    def make_topics_grouped_over_time_figure():
        grouped = topics_grouped_time_data()
        fig, ax = plt.subplots(figsize=(14, 8))

        if grouped.empty:
            ax.text(0.5, 0.5, "No data available for selected topics",
                    ha="center", va="center", transform=ax.transAxes, fontsize=14)
            return fig

        # Prepare data
        pivot_df = grouped.set_index("year")
        colors = get_colors_for_grouping(input.topics_group_mode(), pivot_df.columns)

        # Plot stacked bar chart
        pivot_df.plot(kind="bar", stacked=True, color=colors, width=0.8, ax=ax)

        # === Add labels ===
        # White labels for each stack segment
        for container in ax.containers:
            labels = [int(v) if v > 0 else "" for v in container.datavalues]
            ax.bar_label(container, labels=labels, label_type="center", color="white", fontsize=8)

        # Compute maximum height across all stacks (to pad the top)
        ymax = pivot_df.sum(axis=1).max()
        ax.set_ylim(0, ymax * 1.15)

        # Bold total above each stacked bar
        totals = pivot_df.sum(axis=1)
        for i, total in enumerate(totals):
            if total > 0:
                ax.text(
                    i, total + (totals.max() * 0.02),
                    f"{int(total)}",
                    ha="center",
                    va="bottom",
                    fontsize=10,
                    fontweight="bold",
                )

        # === Axis and title ===
        ax.set_xlabel("Year", fontsize=12)
        ax.set_ylabel("Number of Agreements", fontsize=12)
        ax.set_title(
            f"Agreements with {topics_title_prefix()} by {input.topics_group_mode()} Over Time",
            fontsize=16,
            fontweight="bold",
            pad=20,
            y=1.15,
        )
        plt.xticks(rotation=45, ha="right")

        # === Legend (consistent with peace_process) ===
        ncol = len(pivot_df.columns) if len(pivot_df.columns) <= 4 else 4
        ax.legend(
            title=input.topics_group_mode(),
            bbox_to_anchor=(0.5, 1),
            loc="lower center",
            ncol=ncol,
            fontsize=10,
            frameon=False,
        )

        plt.tight_layout()
        return fig

    def make_topics_stage_figure():
        data = topics_stage_data()
        fig, ax = plt.subplots(figsize=(14, 8))

        # --- Count mode ---
        if input.topics_stage_mode() == "Count":
            bars = ax.bar(data["stage_label"], data["count"], color="#091f40")
            for bar in bars:
                height = bar.get_height()
                if height > 0:
                    ax.text(
                        bar.get_x() + bar.get_width() / 2,
                        height + 0.5,
                        f"{int(height)}",
                        ha="center", va="bottom",
                        fontsize=9,
                        fontweight="bold",
                    )

            ax.set_ylabel("Number of Agreements")
            ymax = data["count"].max() if not data.empty else 0
            ax.set_ylim(0, ymax * 1.15)

        # --- Percentage mode (consistent with peace_process style) ---
        else:
            x = np.arange(len(data))
            width = 0.35

            bars_selected = ax.bar(
                x - width / 2,
                data["filtered_percentage"],
                width,
                label=f"Agts with {topics_title_prefix()}",
                color="#091f40",
            )
            bars_all = ax.bar(
                x + width / 2,
                data["all_percentage"],
                width,
                label="All Agreements",
                color="#cccccc",
            )

            # Only one label per bar — above the bar
            for bars in [bars_selected, bars_all]:
                for bar in bars:
                    height = bar.get_height()
                    if height > 0:
                        ax.text(
                            bar.get_x() + bar.get_width() / 2,
                            height + 1,
                            f"{height:.0f}%",
                            ha="center",
                            va="bottom",
                            fontsize=9,
                            fontweight="bold",
                        )

            ax.set_xticks(x)
            ax.set_xticklabels(data["stage_label"], rotation=45, ha="right")
            ax.set_ylabel("Percentage of Agreements")
            ax.legend(
                title="Stage",
                bbox_to_anchor=(0.5, 1),
                loc="lower center",
                ncol=2,
                fontsize=10,
                frameon=False,
            )
            ymax = max(data["filtered_percentage"].max(), data["all_percentage"].max())
            ax.set_ylim(0, ymax * 1.25)

        # --- Shared styling for both modes ---
        ax.set_xlabel("Stage", fontsize=12)
        ax.set_title(
            f"Agreements with {topics_title_prefix()}, by Stage",
            fontsize=16,
            fontweight="bold",
            pad=20,
            y=1.15,
        )
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        return fig





    def make_topics_peace_process_figure():
        df = topics_peace_process_data()
        fig, ax = plt.subplots(figsize=(14, 10))

        if df.empty:
            ax.text(0.5, 0.5, "No data available", ha="center", va="center", transform=ax.transAxes)
            return fig

        if not input.topics_show_stage_legend():
            bars = ax.barh(df["PPName"], df["count"], color="#091f40")
            for bar in bars:
                width = bar.get_width()
                ax.text(width + max(df["count"]) * 0.01,
                        bar.get_y() + bar.get_height() / 2,
                        f"{int(width)}",
                        ha="left", va="center", fontsize=9)
            n = input.topics_top_processes() or 20
            ax.set_xlabel("Number of Agreements")
            ax.set_ylabel("Peace Process")
            ax.set_title(
                f"Peace Processes with {topics_title_prefix()} (Top {int(n)})",
                fontsize=16,
                fontweight="bold"
            )

        else:
            # Stage breakdown
            pax_df = filtered_agreements()
            stage_data = pax_df.groupby(["PPName", "stage_label"])["AgtId"].nunique().reset_index(name="count")
            stage_pivot = stage_data.pivot(index="PPName", columns="stage_label", values="count").fillna(0)
            stage_pivot = stage_pivot.reindex(df["PPName"])
            colors = [stage_color_map.get(s, "#cccccc") for s in stage_pivot.columns]
            stage_pivot.plot(kind="barh", stacked=True, color=colors, ax=ax, width=0.8)

            for container in ax.containers:
                ax.bar_label(container, fmt="%d", label_type="center", color="white", fontsize=8)

            totals = stage_pivot.sum(axis=1)
            for i, total in enumerate(totals):
                if total > 0:
                    ax.text(total + totals.max() * 0.01, i, f"{int(total)}", va="center", fontsize=9, fontweight="bold")

            ncol = min(4, len(stage_pivot.columns))
            ax.legend(title="Stage", bbox_to_anchor=(0.5, 1), loc="lower center", ncol=ncol, frameon=False)
            ax.set_xlabel("Number of Agreements")
            ax.set_ylabel("Peace Process")
            ax.set_title(f"Peace Processes with {topics_title_prefix()}, by Stage of Process", fontsize=16, fontweight="bold", pad=15, y=1.09)

        plt.tight_layout()
        return fig



    # def make_topics_actors_figure():
    #     data = topics_actor_data()
    #     fig, ax = plt.subplots(figsize=(12, 8))

    #     if data.empty:
    #         ax.text(0.5, 0.5, "No actor data", ha="center", va="center", transform=ax.transAxes)
    #         return fig

    #     colors = data["practical_third"].apply(lambda x: "#df1f36" if x == 1 else "#091f40")
    #     bars = ax.barh(data["actor_name"], data["count"], color=colors)

    #     for bar in bars:
    #         width = bar.get_width()
    #         ax.text(width + max(data["count"]) * 0.01,
    #                 bar.get_y() + bar.get_height() / 2,
    #                 f"{int(width)}",
    #                 ha="left", va="center", fontsize=9, fontweight="bold")

    #     from matplotlib.patches import Patch
    #     ax.legend(
    #         handles=[
    #             Patch(facecolor="#091f40", label="Party Actors"),
    #             Patch(facecolor="#df1f36", label="Third Party Actors"),
    #         ],
    #         loc="lower right",
    #         fontsize=10,
    #         frameon=False,
    #     )

    #     ax.set_xlabel("Number of Agreements", fontsize=12)
    #     ax.set_title("Top Actors Signing Agreements with Selected Topics", fontsize=16, fontweight="bold", pad=15, y=1.05)
    #     plt.tight_layout()
    #     return fig

    @reactive.calc
    def topics_actor_split_data():
        df = filtered_agreements()
        if df.empty or signatories.empty:
            return {"party": pd.DataFrame(), "third_party": pd.DataFrame()}

        sigs = signatories[signatories["AgtId"].isin(df["AgtId"])].copy()
        sigs["signatory_type"] = sigs["practical_third"].apply(lambda x: "third" if x == 1 else "party")

        party = sigs[sigs["signatory_type"] == "party"].groupby("actor_name")["AgtId"].nunique().reset_index(name="count")
        third = sigs[sigs["signatory_type"] == "third"].groupby("actor_name")["AgtId"].nunique().reset_index(name="count")

        n = input.topics_top_actors() or 15
        return {
            "party": party.sort_values("count", ascending=True).tail(int(n)),
            "third": third.sort_values("count", ascending=True).tail(int(n)),
        }
    
    def make_topics_party_actors_figure():
        data = topics_actor_split_data()["party"]
        fig, ax = plt.subplots(figsize=(12, 8))
        if data.empty:
            ax.text(0.5, 0.5, "No party actor data", ha="center", va="center", transform=ax.transAxes)
            return fig

        bars = ax.barh(data["actor_name"], data["count"], color="#091f40")
        for bar in bars:
            width = bar.get_width()
            ax.text(width + max(data["count"]) * 0.01, bar.get_y() + bar.get_height()/2,
                    f"{int(width)}", ha="left", va="center", fontsize=9)
        ax.set_xlabel("Number of Agreements")
        ax.set_title(f"Party Actors Signing Agreements with {topics_title_prefix()}", fontsize=16,
                fontweight="bold")
        ax.set_xlim(0, data["count"].max() * 1.15)
        plt.tight_layout()
        return fig


    def make_topics_third_actors_figure():
        data = topics_actor_split_data()["third"]
        fig, ax = plt.subplots(figsize=(12, 8))
        if data.empty:
            ax.text(0.5, 0.5, "No third-party actor data", ha="center", va="center", transform=ax.transAxes)
            return fig

        bars = ax.barh(data["actor_name"], data["count"], color="#df1f36")
        for bar in bars:
            width = bar.get_width()
            ax.text(width + max(data["count"]) * 0.01, bar.get_y() + bar.get_height()/2,
                    f"{int(width)}", ha="left", va="center", fontsize=9)
        ax.set_xlabel("Number of Agreements")
        ax.set_title(f"Third-Party Actors Signing Agreements with {topics_title_prefix()}", fontsize=16,
                fontweight="bold")
        ax.set_xlim(0, data["count"].max() * 1.15)
        plt.tight_layout()
        return fig




    # -------------------------------------------------------
    #  RENDER PLOTS
    # -------------------------------------------------------
    @render.plot
    def topics_over_time(): return make_topics_over_time_figure()

    @render.plot
    def topics_grouped_over_time(): return make_topics_grouped_over_time_figure()

    @render.plot
    def topics_by_stage(): return make_topics_stage_figure()

    @render.plot
    def topics_by_peace_process(): return make_topics_peace_process_figure()

    #@render.plot
    #def topics_by_actors(): return make_topics_actors_figure()

    @render.plot
    def topics_party_actors(): return make_topics_party_actors_figure()

    @render.plot
    def topics_third_actors(): return make_topics_third_actors_figure()

    # -------------------------------------------------------
    #  DOWNLOADS (PNG + CSV)
    # -------------------------------------------------------
    @render.download(filename="topics_over_time.png")
    def topics_export_time_png():
        return export_with_branding(
            make_topics_over_time_figure,
            filter_text_fn=get_topics_filter_text,
            data_version_fn=get_data_version,
            load_data_fn=lambda: {"pax": pax},
            logo_position=(0.98, 0.98, 0.075, 0.075),
            filter_text_position=(0.5, 0.0035),
            version_position=TOPICS_VERSION_POSITION,
        )

    @render.download(filename="topics_grouped_over_time.png")
    def topics_export_grouped_time_png():
        return export_with_branding(
            make_topics_grouped_over_time_figure,
            filter_text_fn=get_topics_filter_text,
            data_version_fn=get_data_version,
            load_data_fn=lambda: {"pax": pax},
            logo_position=(0.96, 0.96, 0.075, 0.075), #HERE
            filter_text_position=(0.5, 0.0035),
        )

    @render.download(filename="topics_stage.png")
    def topics_export_stage_png():
        return export_with_branding(
            make_topics_stage_figure,
            filter_text_fn=get_topics_filter_text,
            data_version_fn=get_data_version,
            load_data_fn=lambda: {"pax": pax},
            filter_text_position=(0.5, 0.0035),
        )

    @render.download(filename="topics_peace_process.png")
    def topics_export_pp_png():
        return export_with_branding(
            make_topics_peace_process_figure,
            filter_text_fn=get_topics_filter_text,
            data_version_fn=get_data_version,
            load_data_fn=lambda: {"pax": pax},
            logo_position=(1, 1, 0.075, 0.075),
            filter_text_position = (0.5, 0.0035),
            version_position=(1, 0.015),

        )

    # @render.download(filename="topics_actors.png")
    # def topics_export_actors_png():
    #     return export_with_branding(
    #         make_topics_actors_figure,
    #         filter_text_fn=get_topics_filter_text,
    #         data_version_fn=get_data_version,
    #         load_data_fn=lambda: {"pax": pax},
    #     )

    @render.download(filename="topics_party_actors.png")
    def topics_export_party_actors_png():
        return export_with_branding(
            make_topics_party_actors_figure,
            filter_text_fn=get_topics_filter_text,
            data_version_fn=get_data_version,
            load_data_fn=lambda: {"pax": pax},
            logo_position=(1, 1, 0.075, 0.075),
            filter_text_position = (0.5, 0.004)
        )

    @render.download(filename="topics_third_actors.png")
    def topics_export_third_actors_png():
        return export_with_branding(
            make_topics_third_actors_figure,
            filter_text_fn=get_topics_filter_text,
            data_version_fn=get_data_version,
            load_data_fn=lambda: {"pax": pax},
            logo_position=(1, 1, 0.075, 0.075),
            filter_text_position = (0.5, 0.004)
        )

    # CSVs (unchanged)
    @render.download(filename="topics_over_time.csv")
    def topics_export_time_csv(): return io.BytesIO(topics_time_data().to_csv(index=False).encode())

    @render.download(filename="topics_grouped_over_time.csv")
    def topics_export_grouped_time_csv(): return io.BytesIO(topics_grouped_time_data().to_csv(index=False).encode())

    @render.download(filename="topics_stage.csv")
    def topics_export_stage_csv(): return io.BytesIO(topics_stage_data().to_csv(index=False).encode())

    @render.download(filename="topics_peace_process.csv")
    def topics_export_pp_csv(): return io.BytesIO(topics_peace_process_data().to_csv(index=False).encode())

    # @render.download(filename="topics_actors.csv")
    # def topics_export_actors_csv(): return io.BytesIO(topics_actor_data().to_csv(index=False).encode())
    @render.download(filename="topics_party_actors.csv")
    def topics_export_party_actors_csv():
        df = topics_actor_split_data()["party"]
        csv = df.to_csv(index=False)
        return io.BytesIO(csv.encode("utf-8"))

    @render.download(filename="topics_third_actors.csv")
    def topics_export_third_actors_csv():
        df = topics_actor_split_data()["third"]
        csv = df.to_csv(index=False)
        return io.BytesIO(csv.encode("utf-8"))


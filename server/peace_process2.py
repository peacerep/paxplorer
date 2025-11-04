#server/peace_processes.py
import io
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from shiny import reactive, render, ui
from datetime import datetime
import matplotlib.dates as mdates
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.io as pio
from upsetplot import UpSet

DATA_DIR = "data"
LOGO_PATH = "static/logos/Pax.png"

#define stage order and stage colours
stage_order = [
    'Pre-negotiation/process', 'Ceasefire', 'Framework-substantive, partial',
    'Framework-substantive, comprehensive', 'Implementation', 'Renewal', 'Other'
]

stage_color_map = {
    'Pre-negotiation/process': '#016099',
    'Ceasefire': '#df1f36',
    'Framework-substantive, partial': '#fd8189',
    'Framework-substantive, comprehensive': '#fdd900',
    'Implementation': '#3aae2a',
    'Renewal': '#7b8ad6',
    'Other': '#c0de88'
}

type_color_map = {
    "Intrastate": "#0b5740",
    "Local": "#ac4399",
    "Interstate/mixed": "#df1f36",
    "Interstate": "#f28b20",
}


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def get_colors_for_grouping(group_mode: str, categories):
    if group_mode == "Stage":
        return [stage_color_map.get(cat, "#cccccc") for cat in categories]
    else:  # Agreement Type
        return [type_color_map.get(cat, "#cccccc") for cat in categories]


def _input_value(input, name: str, default=None):
    try:
        return getattr(input, name)()
    except Exception:
        return default


def _get_pp_filter_text_for_png(get_applied_filters_fn) -> str:
    try:
        filters = get_applied_filters_fn()
    except Exception:
        filters = []
    if not filters:
        return "No filters applied"
    return "; ".join(filters)


def _get_data_version(load_data_fn) -> str:
    try:
        pax = load_data_fn()["pax"]
        if "Ver" in pax.columns and not pax["Ver"].isna().all():
            return str(pax["Ver"].max())
    except Exception:
        pass
    return "Unknown"


def _add_logo_and_subtitle(fig, filter_text: str, data_version: str):
    # Subtitle (bottom-center)
    fig.text(
        0.5,
        0.025,
        filter_text,
        transform=fig.transFigure,
        ha="center",
        va="bottom",
        fontsize=8,
        style="italic",
        color="#666666",
    )
    # Data version (bottom-right)
    fig.text(
        0.98,
        0.02,
        f"PA-X Database v{data_version}",
        transform=fig.transFigure,
        ha="right",
        va="bottom",
        fontsize=7,
        color="#999999",
    )
    # Logo (top-right)
    if LOGO_PATH.exists():
        try:
            logo_img = plt.imread(LOGO_PATH)
            logo_ax = fig.add_axes([0.92, 0.94, 0.078, 0.078])
            logo_ax.imshow(logo_img, alpha=0.8)
            logo_ax.axis("off")
        except Exception as e:
            print(f"Warning: Could not add logo: {e}")


# -----------------------------------------------------------------------------
# Server
# -----------------------------------------------------------------------------

def server(input, output, session):
    # ------------------------------
    # Data loading
    # ------------------------------
    @reactive.calc
    def load_data():
        pax = pd.read_csv(DATA_DIR / "pax.csv")
        pax_id_to_con = pd.read_csv(DATA_DIR / "pax_id_to_con_info.csv")
        pax_topics = pd.read_csv(DATA_DIR / "all_pax_topics_no_imp.csv")
        sig_path = DATA_DIR / "paax_signatory_v0.2_internal.csv"
        signatories = pd.read_csv(sig_path) if sig_path.exists() else pd.DataFrame()

        pax["date"] = pd.to_datetime(pax["Dat"], errors="coerce")

        return {
            "pax": pax,
            "pax_id_to_con": pax_id_to_con,
            "pax_topics": pax_topics,
            "signatories": signatories,
        }

    # ------------------------------
    # Filter choice calculations
    # ------------------------------
    @reactive.calc
    def pp_agt_type_choices():
        data = load_data()
        return sorted(data["pax"]["agt_type"].dropna().unique().tolist())

    @reactive.calc
    def pp_stage_choices():
        data = load_data()
        return sorted(data["pax"]["stage_label"].dropna().unique().tolist())

    @reactive.calc
    def pp_year_range():
        data = load_data()
        min_year = int(data["pax"]["year"].min())
        max_year = int(data["pax"]["year"].max())
        return [min_year, max_year]

    @reactive.calc
    def peace_process_choices():
        data = load_data()
        if "PPName" not in data["pax"].columns:
            return []
        return sorted(data["pax"]["PPName"].dropna().unique().tolist())

    @reactive.calc
    def pp_date_range():
        data = load_data()
        dates = pd.to_datetime(data["pax"]["Dat"], errors="coerce").dropna()
        if dates.empty:
            return [None, None]
        return [dates.min().date(), dates.max().date()]

    # ------------------------------
    # Populate dropdowns
    # ------------------------------
    @reactive.effect
    def _populate_inputs():
        peace_processes = peace_process_choices()
        agt_types = pp_agt_type_choices()
        stages = pp_stage_choices()
        year_min, year_max = pp_year_range()
        date_min, date_max = pp_date_range()

        ui.update_selectize(
            "selected_peace_process",
            choices=peace_processes,
            selected=peace_processes[0] if peace_processes else None,
        )
        ui.update_selectize("pp_agt_type", choices=agt_types, selected=[])
        ui.update_selectize("pp_stage", choices=stages, selected=[])
        ui.update_slider("pp_year_range", min=year_min, max=year_max, value=[year_min, year_max])
        if date_min and date_max:
            ui.update_date_range("pp_date_range", start=date_min, end=date_max)

    # ------------------------------
    # Filtering
    # ------------------------------
    @reactive.calc
    def filtered_pp_data():
        data = load_data()
        df = data["pax"].copy()

        selected_pp = _input_value(input, "selected_peace_process")
        if selected_pp:
            df = df[df["PPName"] == selected_pp]

        selected_types = _input_value(input, "pp_agt_type", [])
        if selected_types:
            selected_types = [selected_types] if isinstance(selected_types, str) else selected_types
            df = df[df["agt_type"].isin(selected_types)]

        year_range_vals = _input_value(input, "pp_year_range", None)
        if year_range_vals and len(year_range_vals) == 2:
            df = df[(df["year"] >= year_range_vals[0]) & (df["year"] <= year_range_vals[1])]

        date_range_vals = _input_value(input, "pp_date_range", None)
        if date_range_vals and len(date_range_vals) == 2 and date_range_vals[0] and date_range_vals[1]:
            start_date = pd.to_datetime(date_range_vals[0])
            end_date = pd.to_datetime(date_range_vals[1])
            df = df[(df["date"] >= start_date) & (df["date"] <= end_date)]

        selected_stages = _input_value(input, "pp_stage", [])
        if selected_stages:
            selected_stages = [selected_stages] if isinstance(selected_stages, str) else selected_stages
            df = df[df["stage_label"].isin(selected_stages)]

        agt_ids = df["AgtId"].unique()
        filtered_topics = data["pax_topics"][data["pax_topics"]["AgtId"].isin(agt_ids)]
        filtered_signatories = (
            data["signatories"][data["signatories"]["AgtId"].isin(agt_ids)]
            if not data["signatories"].empty
            else pd.DataFrame()
        )

        return {
            "pax": df,
            "pax_id_to_con": data["pax_id_to_con"],
            "pax_topics": filtered_topics,
            "signatories": filtered_signatories,
        }

    # ------------------------------
    # Applied filters and summary
    # ------------------------------
    @reactive.calc
    def get_applied_filters():
        filters = []

        selected_pp = _input_value(input, "selected_peace_process")
        if selected_pp:
            filters.append(f"Peace Process: {selected_pp}")

        types = _input_value(input, "pp_agt_type", []) or []
        if types:
            text = f"Agreement Type: {', '.join(types[:2])}" + (f" + {len(types)-2} more" if len(types) > 2 else "")
            filters.append(text)

        year_min, year_max = pp_year_range()
        year_range_vals = _input_value(input, "pp_year_range", None)
        if year_range_vals and len(year_range_vals) == 2:
            if year_range_vals[0] != year_min or year_range_vals[1] != year_max:
                filters.append(f"Years: {year_range_vals[0]}–{year_range_vals[1]}")

        date_range_vals = _input_value(input, "pp_date_range", None)
        if date_range_vals and len(date_range_vals) == 2 and date_range_vals[0] and date_range_vals[1]:
            filters.append(f"Date Range: {date_range_vals[0]} to {date_range_vals[1]}")

        stages = _input_value(input, "pp_stage", []) or []
        if stages:
            text = f"Stages: {', '.join(stages[:3])}" + (f" + {len(stages)-3} more" if len(stages) > 3 else "")
            filters.append(text)

        return filters

    @render.ui
    def pp_applied_filters():
        filters = get_applied_filters()
        if not filters:
            return ui.div(
                ui.tags.i(class_="fas fa-info-circle me-2"),
                "No filters applied",
                style="color: #6c757d; font-style: italic;",
            )
        return ui.div(
            *(ui.div(ui.tags.i(class_="fas fa-filter me-2", style="color: #007bff;"), f, class_="mb-1") for f in filters)
        )

    @render.ui
    def pp_filter_summary():
        data = load_data()
        total = data["pax"]["AgtId"].nunique()
        filtered = filtered_pp_data()["pax"]["AgtId"].nunique()
        percentage = (filtered / total * 100) if total > 0 else 0
        year_min, year_max = pp_year_range()
        yr = _input_value(input, "pp_year_range", [year_min, year_max])
        year_span = "" if yr[0] == year_min and yr[1] == year_max else f" ({yr[0]}–{yr[1]})"
        return ui.div(
            f"Showing {filtered:,} of {total:,} agreements ({percentage:.1f}%)" + year_span,
            style="font-weight: 500;",
        )

    @reactive.effect
    @reactive.event(input.pp_reset_filters)
    def _reset_filters():
        peace_processes = peace_process_choices()
        year_min, year_max = pp_year_range()
        date_min, date_max = pp_date_range()
        ui.update_selectize("selected_peace_process", selected=peace_processes[0] if peace_processes else None)
        ui.update_selectize("pp_agt_type", selected=[])
        ui.update_selectize("pp_stage", selected=[])
        ui.update_slider("pp_year_range", value=[year_min, year_max])
        if date_min and date_max:
            ui.update_date_range("pp_date_range", start=date_min, end=date_max)

    # ------------------------------
    # Summary stats and PA-X link
    # ------------------------------
    @render.ui
    def pp_summary_stats():
        selected_pp = _input_value(input, "selected_peace_process")
        if not selected_pp:
            return ui.div("Select a peace process to see summary", style="color: #6c757d; font-style: italic;")

        data = filtered_pp_data()
        df = data["pax"]
        if df.empty:
            return ui.div("No data available", style="color: #6c757d;")

        num_agreements = df["AgtId"].nunique()
        dates = pd.to_datetime(df["Dat"], errors="coerce").dropna()
        if not dates.empty:
            first_date = dates.min().strftime("%d-%m-%Y")
            last_date = dates.max().strftime("%d-%m-%Y")
            date_range = f"{first_date} to {last_date}"
        else:
            date_range = "No dates available"

        return ui.div(
            ui.div(
                ui.tags.img(
                    src="/logos/agreements_icon.png",
                    style="width: 20px; height: 20px; margin-right: 8px; vertical-align: middle;",
                ),
                f"{num_agreements} agreements",
                style="font-weight: bold; margin-bottom: 5px; display: flex; align-items: center;",
            ),
            ui.div(
                ui.tags.img(
                    src="/logos/calendar.png",
                    style="width: 18px; height: 18px; margin-right: 8px; vertical-align: middle;",
                ),
                f"{date_range}",
                style="font-size: 0.9em; color: #666; display: flex; align-items: center;",
            ),
            style="text-align: left;",
        )

    @render.ui
    def pp_database_link():
        selected_pp_name = _input_value(input, "selected_peace_process")
        if not selected_pp_name:
            return ui.div()

        data = load_data()
        matching_rows = data["pax"][data["pax"]["PPName"] == selected_pp_name]
        if matching_rows.empty:
            return ui.div()
        selected_pp_id = matching_rows["PP"].iloc[0]

        base_url = "https://www.peaceagreements.org/agreements/search/?search_type=basic-search&match_any_issues=True"
        search_url = f"{base_url}&process={selected_pp_id}#timeline"

        return ui.tags.a(
            ui.tags.img(
                src="/logos/Pax_white.png",
                style="width: 18px; height: 18px; margin-right: 8px; vertical-align: middle;",
            ),
            "View Agreements on PA-X",
            href=search_url,
            target="_blank",
            class_="btn btn-primary",
            style="text-decoration: none;",
        )

    # ------------------------------
    # Messy timeline block: title + full-screen button + iframe
    # ------------------------------
    @render.ui
    def external_viz_iframe():
        selected_pp_name = _input_value(input, "selected_peace_process")
        if not selected_pp_name:
            return ui.div("Please select a peace process to view the visualization.")

        data = load_data()
        matching_rows = data["pax"][data["pax"]["PPName"] == selected_pp_name]
        if matching_rows.empty:
            return ui.div("No matching peace process found.")

        selected_pp_id = matching_rows["PP"].iloc[0]
        base_url = "https://peacerep.github.io/v7_messy_timeline/"
        full_url = f"{base_url}?subset={selected_pp_id}"

        return ui.div(
            ui.div(
                ui.h5("Messy timeline", class_="mb-2"),
                ui.tags.a(
                    "View in full screen",
                    href=full_url,
                    target="_blank",
                    class_="btn btn-outline-primary btn-sm ms-2",
                    style="vertical-align: baseline;",
                ),
                class_="d-flex align-items-center gap-2 mb-2",
            ),
            ui.tags.iframe(
                src=full_url,
                width="100%",
                height="100%",
                style="border: 1px solid #ddd; border-radius: 4px; min-height: 500px;",
            ),
        )

    # ------------------------------
    # Agreements over time
    # ------------------------------
    @reactive.calc
    def pp_agreements_time_data():
        data = filtered_pp_data()
        df = data["pax"]
        if df.empty:
            return pd.DataFrame()

        df = df.dropna(subset=["date"]).copy()
        granularity = _input_value(input, "pp_time_granularity", "month")

        if granularity == "year":
            df["time_period"] = df["date"].dt.year
        else:
            df["time_period"] = df["date"].dt.strftime("%Y-%m")

        time_data = df.groupby(["time_period", "stage_label"])["AgtId"].nunique().reset_index(name="count")

        # Fill gaps
        if not time_data.empty:
            if granularity == "month":
                min_date = df["date"].min()
                max_date = df["date"].max()
                all_periods = pd.date_range(start=min_date.replace(day=1), end=max_date, freq="MS").strftime("%Y-%m")
            else:
                min_year = df["date"].dt.year.min()
                max_year = df["date"].dt.year.max()
                all_periods = range(min_year, max_year + 1)

            complete_grid = [{"time_period": p, "stage_label": s} for p in all_periods for s in stage_order]
            complete_df = pd.DataFrame(complete_grid)
            time_data = complete_df.merge(time_data, on=["time_period", "stage_label"], how="left").fillna(0)
            time_data["count"] = time_data["count"].astype(int)

        return time_data

    def build_pp_agreements_over_time(time_data: pd.DataFrame, granularity: str, show_labels: bool) -> plt.Figure:
        fig, ax = plt.subplots(figsize=(12, 8))

        if time_data.empty:
            ax.text(
                0.5, 0.5, "No data available for selected peace process",
                ha="center", va="center", transform=ax.transAxes, fontsize=14
            )
            ax.set_xticks([]); ax.set_yticks([])
            return fig

        pivot_df = time_data.pivot(index="time_period", columns="stage_label", values="count").fillna(0)

        available_stages = [s for s in stage_order if s in pivot_df.columns]
        other_stages = [s for s in pivot_df.columns if s not in stage_order]
        pivot_df = pivot_df[available_stages + other_stages]

        colors = get_colors_for_grouping("Stage", pivot_df.columns)
        pivot_df.plot(kind="bar", stacked=True, ax=ax, color=colors, width=0.8)

        totals = pivot_df.sum(axis=1)
        ax.set_ylim(0, totals.max() + 2)

        if show_labels:
            for i, total in enumerate(totals):
                if total > 0:
                    ax.text(i, total + 0.25, f"{int(total)}", ha="center", fontsize=10, fontweight="bold")
            for container in ax.containers:
                ax.bar_label(container, fmt="%d", label_type="center", fontsize=8, color="white")

        ax.set_xlabel("Time Period", fontsize=12)
        ax.set_ylabel("Number of Agreements", fontsize=12)
        ax.set_title("Agreements by Stage Over Time", fontsize=16, fontweight="bold", pad=20, y=1.15)

        ax.tick_params(axis="x", rotation=45)
        if granularity == "month" and len(pivot_df) > 12:
            n_ticks = max(1, len(pivot_df) // 6)
            tick_positions = list(range(0, len(pivot_df), n_ticks))
            ax.set_xticks(tick_positions)
            ax.set_xticklabels([pivot_df.index[i] for i in tick_positions])

        ncol = min(len(pivot_df.columns), 4)
        ax.legend(title="Stage", bbox_to_anchor=(0.5, 1), loc="lower center", fontsize=10, ncol=ncol)

        plt.tight_layout()
        return fig

    @render.plot
    def pp_agreements_over_time():
        td = pp_agreements_time_data()
        return build_pp_agreements_over_time(td, _input_value(input, "pp_time_granularity", "month"), _input_value(input, "pp_show_labels", False))

    # ------------------------------
    # Stage analysis
    # ------------------------------
    @reactive.calc
    def pp_stage_analysis_data():
        data = filtered_pp_data()
        df = data["pax"]
        all_data = load_data()["pax"]
        if df.empty:
            return pd.DataFrame()

        filtered_stage = df.groupby("stage_label")["AgtId"].nunique().reset_index(name="filtered_count")
        all_stage = all_data.groupby("stage_label")["AgtId"].nunique().reset_index(name="all_count")
        total_filtered = df["AgtId"].nunique()
        total_all = all_data["AgtId"].nunique()

        stage_data = (
            pd.DataFrame({"stage_label": stage_order})
            .merge(filtered_stage, on="stage_label", how="left")
            .merge(all_stage, on="stage_label", how="left")
            .fillna(0)
        )

        stage_data["filtered_percentage"] = (stage_data["filtered_count"] / total_filtered * 100) if total_filtered > 0 else 0
        stage_data["all_percentage"] = (stage_data["all_count"] / total_all * 100) if total_all > 0 else 0

        return stage_data

    def build_pp_stage_analysis(stage_data: pd.DataFrame, show_labels: bool) -> plt.Figure:
        fig, ax = plt.subplots(figsize=(14, 8))

        if stage_data.empty:
            ax.text(0.5, 0.5, "No stage data available", ha="center", va="center", transform=ax.transAxes, fontsize=14)
            return fig

        x = np.arange(len(stage_data))
        width = 0.35

        bars1 = ax.bar(x - width / 2, stage_data["filtered_percentage"], width, label="Selected Process", color="#091f40")
        bars2 = ax.bar(x + width / 2, stage_data["all_percentage"], width, label="All Agreements", color="#cccccc")

        if show_labels:
            filtered_labels = (stage_data["filtered_percentage"].round(0).astype(int).astype(str) + "%").tolist()
            all_labels = (stage_data["all_percentage"].round(0).astype(int).astype(str) + "%").tolist()
            for bars, labels in [(bars1, filtered_labels), (bars2, all_labels)]:
                for bar, label in zip(bars, labels):
                    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1, label, ha="center", va="bottom", fontsize=10, fontweight="bold")

        ax.set_xticks(x)
        ax.set_xticklabels(stage_data["stage_label"], rotation=45, ha="right")
        ax.set_xlabel("Stage", fontsize=12)
        ax.set_ylabel("Percentage of Agreements", fontsize=12)
        ax.set_title("Number of Agreements per Stage of Process", fontsize=16, fontweight="bold", pad=20, y=1.15)
        ax.spines[["top", "right"]].set_visible(False)

        max1 = max((b.get_height() for b in bars1), default=0)
        max2 = max((b.get_height() for b in bars2), default=0)
        ax.set_ylim(0, max(max1, max2) + 10)

        ax.legend(bbox_to_anchor=(0.5, 1), loc="lower center", ncol=2, fontsize=12)
        plt.tight_layout()
        return fig

    @render.plot
    def pp_stage_analysis():
        sd = pp_stage_analysis_data()
        return build_pp_stage_analysis(sd, _input_value(input, "pp_show_labels", False))

    # ------------------------------
    # NEW: Agreement type pie (after stage analysis)
    # ------------------------------
    @reactive.calc
    def pp_agreement_type_counts():
        data = filtered_pp_data()
        df = data["pax"]
        if df.empty:
            return pd.DataFrame(columns=["agt_type", "count"])
        counts = df.groupby("agt_type")["AgtId"].nunique().reset_index(name="count")
        counts = counts.sort_values("count", ascending=False)
        return counts

    def build_pp_agt_type_pie(counts: pd.DataFrame) -> plt.Figure:
        fig, ax = plt.subplots(figsize=(10, 8))
        if counts.empty or counts["count"].sum() == 0:
            ax.text(0.5, 0.5, "No data for agreement type", ha="center", va="center", transform=ax.transAxes)
            return fig

        labels = counts["agt_type"].fillna("Unknown").tolist()
        sizes = counts["count"].tolist()
        colors = [type_color_map.get(t, "#cccccc") for t in labels]

        wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct="%1.0f%%", startangle=90, colors=colors, textprops={"fontsize": 9})
        ax.set_title("Agreements by Type", fontsize=14, fontweight="bold")
        ax.axis("equal")
        plt.tight_layout()
        return fig

    @render.plot
    def pp_agreement_type_pie():
        return build_pp_agt_type_pie(pp_agreement_type_counts())

    # ------------------------------
    # Signatories
    # ------------------------------
    @reactive.calc
    def pp_signatories_data():
        data = filtered_pp_data()
        signatories = data["signatories"]
        if signatories.empty:
            return {"party": pd.DataFrame(), "third_party": pd.DataFrame()}

        sig = signatories.copy()
        sig["signatory_type"] = sig["practical_third"].apply(lambda x: "third party" if x == 1 else "party")

        party_signatories = sig[sig["signatory_type"] == "party"]
        third_signatories = sig[sig["signatory_type"] == "third party"]

        party_counts = (
            party_signatories.groupby("actor_name")["AgtId"].nunique().reset_index(name="count")
            if not party_signatories.empty
            else pd.DataFrame(columns=["actor_name", "count"])
        )
        third_counts = (
            third_signatories.groupby("actor_name")["AgtId"].nunique().reset_index(name="count")
            if not third_signatories.empty
            else pd.DataFrame(columns=["actor_name", "count"])
        )

        total_agts = data["pax"]["AgtId"].nunique()
        if total_agts > 0:
            if not party_counts.empty:
                party_counts["percentage"] = party_counts["count"] / total_agts * 100.0
            if not third_counts.empty:
                third_counts["percentage"] = third_counts["count"] / total_agts * 100.0

        return {"party": party_counts, "third_party": third_counts}

    def _adjust_left_margin_for_labels(fig, labels, base=0.12, per_char=0.008, max_left=0.45):
        max_len = max((len(str(s)) for s in labels), default=10)
        left = min(max_left, base + per_char * max_len)
        try:
            fig.subplots_adjust(left=left, right=0.98, bottom=0.12, top=0.9)
        except Exception:
            pass

    def build_signatories_bar(df: pd.DataFrame, title: str, color: str, mode: str) -> plt.Figure:
        fig, ax = plt.subplots(figsize=(16, 9))  # wider to avoid crop
        if df.empty:
            ax.text(0.5, 0.5, f"No {title.lower()} data available", ha="center", va="center", transform=ax.transAxes)
            return fig

        df = df.sort_values("count", ascending=True).tail(15)
        if mode == "percentage":
            y_vals = df["percentage"]
            xlabel = "Percentage of Agreements"
        else:
            y_vals = df["count"]
            xlabel = "Number of Agreements"

        bars = ax.barh(df["actor_name"], y_vals, color=color)
        ax.set_xlabel(xlabel, fontsize=12)
        ax.set_ylabel(title, fontsize=12)
        ax.set_title(title, fontsize=14, fontweight="bold")

        y_max = float(y_vals.max()) if len(y_vals) else 0.0
        for bar in bars:
            w = bar.get_width()
            if mode == "percentage":
                label = f"{w:.0f}%" if w >= 1 else f"{w:.1f}%"
            else:
                label = f"{int(w)}"
            ax.text(w + (0.01 * y_max if y_max else 0.1), bar.get_y() + bar.get_height() / 2, label, ha="left", va="center", fontsize=9)

        # Make room for long actor names
        _adjust_left_margin_for_labels(fig, df["actor_name"])
        return fig

    @render.plot
    def pp_party_signatories():
        sig = pp_signatories_data()["party"]
        return build_signatories_bar(sig, title="Party Signatories", color="#091f40", mode=_input_value(input, "pp_signatory_mode", "count"))

    @render.plot
    def pp_third_party_signatories():
        sig = pp_signatories_data()["third_party"]
        return build_signatories_bar(sig, title="Third Party Signatories", color="#df1f36", mode=_input_value(input, "pp_signatory_mode", "count"))

    # ------------------------------
    # UpSet plot (actor co-occurrence) with colored labels and dots, better margins
    # ------------------------------
    @render.plot
    def pp_upset_plot():
        data = filtered_pp_data()
        signatories = data["signatories"]

        fig, ax = plt.subplots(figsize=(15, 8))
        if signatories.empty:
            ax.text(0.5, 0.5, "No signatory data available", ha="center", va="center", transform=ax.transAxes)
            return fig

        min_cooccurrence = _input_value(input, "pp_upset_min_cooccurrence", 2)

        unique_combinations = signatories.drop_duplicates(["AgtId", "actor_name"])

        actor_agreement_matrix = (
            unique_combinations.pivot_table(
                index="AgtId",
                columns="actor_name",
                values="practical_third",
                aggfunc=lambda x: True,
                fill_value=False,
            )
            .astype(bool)
        )

        actor_counts = actor_agreement_matrix.sum()
        frequent_actors = actor_counts[actor_counts >= min_cooccurrence].index.tolist()
        if len(frequent_actors) < 2:
            ax.text(
                0.5,
                0.5,
                f"Insufficient data for UpSet plot\n(Need at least 2 actors with {min_cooccurrence}+ agreements)",
                ha="center",
                va="center",
                transform=ax.transAxes,
            )
            return fig

        # Determine actor types for labeling
        actor_type_map = {}
        for actor in frequent_actors:
            is_third_party = signatories[signatories["actor_name"] == actor]["practical_third"].max() == 1
            actor_type_map[actor] = "third_party" if is_third_party else "party"

        party_color = "#091f40"
        third_party_color = "#df1f36"

        actor_agreement_matrix = actor_agreement_matrix[frequent_actors]

        # Build memberships (only agreements with 2+ frequent actors)
        s = actor_agreement_matrix.stack()
        s = s[s]
        memberships = []
        for agt_id in s.index.get_level_values(0).unique():
            actors_for_agreement = s.loc[agt_id].index.tolist()
            if len(actors_for_agreement) > 1:
                memberships.append(actors_for_agreement)

        if len(memberships) == 0:
            ax.text(0.5, 0.5, "No agreements with multiple frequent actors found", ha="center", va="center", transform=ax.transAxes)
            return fig

        from upsetplot import from_memberships
        upset_series = from_memberships(memberships)

        # Create the UpSet plot; get the figure it creates
        upset = UpSet(upset_series, subset_size="count", show_counts=True)
        plot_result = upset.plot()

        # Extract figure
        if isinstance(plot_result, dict):
            fig = plot_result.get("fig", None) or plot_result.get("figure", None) or plt.gcf()
        else:
            fig = plot_result if plot_result is not None else plt.gcf()

        # Try to color ytick labels by actor type and the membership dots as well
        try:
            # Increase left margin based on longest label
            _adjust_left_margin_for_labels(fig, frequent_actors, base=0.2, per_char=0.01, max_left=0.6)
            try:
                fig.subplots_adjust(right=0.85, top=0.88)
            except Exception:
                pass

            actor_axis = None
            for axx in fig.axes:
                labels = [lab.get_text() for lab in axx.get_yticklabels()]
                if labels and any(lab in frequent_actors for lab in labels):
                    actor_axis = axx
                    break

            if actor_axis is not None:
                ytick_labels = actor_axis.get_yticklabels()
                ytick_positions = actor_axis.get_yticks().tolist()

                # Color y-axis labels to match actor type
                for lab in ytick_labels:
                    name = lab.get_text()
                    if name in actor_type_map:
                        if actor_type_map[name] == "third_party":
                            lab.set_color(third_party_color)
                            lab.set_weight("bold")
                        else:
                            lab.set_color(party_color)
                            lab.set_weight("bold")

                # Color the membership dots to match the actor type
                for axx in fig.axes:
                    for coll in getattr(axx, "collections", []):
                        try:
                            offsets = coll.get_offsets()
                            if offsets is None or len(offsets) == 0:
                                continue
                            colors = []
                            for (x, y) in offsets:
                                if not ytick_positions:
                                    colors.append((0.6, 0.6, 0.6, 1.0))
                                    continue
                                dists = [abs(y - yp) for yp in ytick_positions]
                                idx = int(np.argmin(dists))
                                actor_name = ytick_labels[idx].get_text() if idx < len(ytick_labels) else None
                                if actor_name in actor_type_map:
                                    colors.append(third_party_color if actor_type_map[actor_name] == "third_party" else party_color)
                                else:
                                    colors.append((0.6, 0.6, 0.6, 1.0))
                            coll.set_facecolor(colors)
                            coll.set_edgecolor(colors)
                        except Exception:
                            continue

            # Legend
            from matplotlib.patches import Patch
            legend_elements = [
                Patch(facecolor=party_color, label="Party Actors"),
                Patch(facecolor=third_party_color, label="Third Party Actors"),
            ]
            fig.legend(handles=legend_elements, loc="upper right", bbox_to_anchor=(0.98, 0.85))
        except Exception as e:
            print(f"Warning during UpSet coloring: {e}")

        fig.suptitle(
            f"Actor Co-occurrence Analysis\n(Minimum {min_cooccurrence} agreement{'s' if min_cooccurrence != 1 else ''} per actor)",
            fontsize=14,
            fontweight="bold",
            y=0.95,
        )

        plt.tight_layout()
        return fig

    # ------------------------------
    # Topics analysis (categories and issues)
    # ------------------------------
    @reactive.calc
    def pp_topics_category_data():
        data = filtered_pp_data()
        topics = data["pax_topics"]
        if topics.empty:
            return pd.DataFrame()
        topics_filtered = topics[topics["value"] > 0]
        topic_counts = topics_filtered.groupby("category")["AgtId"].nunique().reset_index(name="count")
        return topic_counts

    @reactive.calc
    def pp_topics_subissue_data():
        data = filtered_pp_data()
        topics = data["pax_topics"]
        if topics.empty:
            return pd.DataFrame()
        topics_filtered = topics[
            (topics["value"] > 0)
            & (topics["subissue_label"].notna())
            & (topics["subissue_label"] != "")
        ]
        subissue_counts = topics_filtered.groupby(["subissue_label", "category"])["AgtId"].nunique().reset_index(name="count")
        return subissue_counts

    @reactive.calc
    def pp_topics_issue_data():
        data = filtered_pp_data()
        topics = data["pax_topics"]
        if topics.empty:
            return pd.DataFrame()
        topics_filtered = topics[
            (topics["value"] > 0)
            & (topics["issue_label"].notna())
            & (topics["issue_label"] != "")
        ]
        issue_counts = topics_filtered.groupby(["issue_label", "category"])["AgtId"].nunique().reset_index(name="count")
        return issue_counts

    @render.plot
    def pp_topics_categories_chart():
        topics_data = pp_topics_category_data()
        fig, ax = plt.subplots(figsize=(14, 8))
        if topics_data.empty:
            ax.text(0.5, 0.5, "No topic categories data available", ha="center", va="center", transform=ax.transAxes)
            return fig

        topics_sorted = topics_data.sort_values("count", ascending=True)
        bars = ax.barh(topics_sorted["category"], topics_sorted["count"], color="#091f40")
        ax.set_xlabel("Number of Agreements", fontsize=12)
        ax.set_ylabel("Topic Category", fontsize=12)
        ax.set_title("Topic Categories in Peace Process", fontsize=14, fontweight="bold")

        # Add labels
        x_max = topics_sorted["count"].max()
        for bar in bars:
            width = bar.get_width()
            ax.text(width + x_max * 0.01, bar.get_y() + bar.get_height() / 2, f"{int(width)}", ha="left", va="center", fontsize=9)

        plt.tight_layout()
        return fig

    @render.plot
    def pp_topics_issues_chart():
        issue_data = pp_topics_issue_data()
        fig, ax = plt.subplots(figsize=(14, 12))
        if issue_data.empty:
            ax.text(0.5, 0.5, "No issue data available", ha="center", va="center", transform=ax.transAxes)
            return fig

        issue_sorted = issue_data.sort_values("count", ascending=True)

        if _input_value(input, "pp_topics_show_stage_legend", False):
            pax_df = filtered_pp_data()["pax"]
            topics_df = filtered_pp_data()["pax_topics"]

            if not pax_df.empty and not topics_df.empty:
                issue_stage_data = []
                for _, issue_row in issue_sorted.iterrows():
                    issue_name = issue_row["issue_label"]
                    issue_agreements = topics_df[
                        (topics_df["issue_label"] == issue_name) & (topics_df["value"] > 0)
                    ]["AgtId"].unique()
                    issue_pax = pax_df[pax_df["AgtId"].isin(issue_agreements)]
                    stage_counts = issue_pax["stage_label"].value_counts()
                    for stage in stage_order:
                        issue_stage_data.append({"issue_label": issue_name, "stage_label": stage, "count": stage_counts.get(stage, 0)})

                stage_df = pd.DataFrame(issue_stage_data)
                stage_pivot = stage_df.pivot(index="issue_label", columns="stage_label", values="count").fillna(0)
                available_stages = [s for s in stage_order if s in stage_pivot.columns]
                stage_pivot = stage_pivot[available_stages]
                stage_pivot = stage_pivot.reindex(issue_sorted["issue_label"])
                colors = [stage_color_map.get(s, "#cccccc") for s in stage_pivot.columns]
                stage_pivot.plot(kind="barh", stacked=True, ax=ax, color=colors, width=0.8)
                ax.legend(title="Stage", bbox_to_anchor=(0.5, 1), loc="lower center", ncol=2)
            else:
                bars = ax.barh(issue_sorted["issue_label"], issue_sorted["count"], color="#091f40")
        else:
            bars = ax.barh(issue_sorted["issue_label"], issue_sorted["count"], color="#091f40")
            x_max = issue_sorted["count"].max()
            for bar in bars:
                width = bar.get_width()
                ax.text(width + x_max * 0.01, bar.get_y() + bar.get_height() / 2, f"{int(width)}", ha="left", va="center", fontsize=9)

        ax.set_xlabel("Number of Agreements", fontsize=12)
        ax.set_ylabel("Issue", fontsize=12)
        ax.set_title("Issues in Peace Process", fontsize=14, fontweight="bold")
        plt.tight_layout()
        return fig

    # ------------------------------
    # NEW: Topics radial chart (issues or sub-issues) + switch control
    # ------------------------------
    @render.ui
    def pp_topics_radial_controls():
        # A single inline switch to toggle sub-issues; place this output in the UI near the radial chart
        return ui.div(
            ui.div(
                ui.input_switch("pp_topics_radial_subissues", "Sub-issues", False),
                class_="d-flex align-items-center gap-3",
            ),
            class_="mb-2",
        )

    def _topics_counts_for_radial(level: str) -> pd.DataFrame:
        data = filtered_pp_data()
        topics = data["pax_topics"]
        if topics.empty:
            return pd.DataFrame(columns=["label", "count"])

        if level == "subissues":
            filt = topics[
                (topics["value"] > 0)
                & (topics["subissue_label"].notna())
                & (topics["subissue_label"] != "")
            ]
            counts = filt.groupby("subissue_label")["AgtId"].nunique().reset_index(name="count")
            counts = counts.rename(columns={"subissue_label": "label"})
        else:
            filt = topics[
                (topics["value"] > 0)
                & (topics["issue_label"].notna())
                & (topics["issue_label"] != "")
            ]
            counts = filt.groupby("issue_label")["AgtId"].nunique().reset_index(name="count")
            counts = counts.rename(columns={"issue_label": "label"})

        counts = counts.sort_values("count", ascending=False)
        return counts

    def build_topics_radial(counts: pd.DataFrame, title: str, max_topics: int = 24) -> plt.Figure:
        # Use polar bar chart
        fig = plt.figure(figsize=(12, 12))
        ax = fig.add_subplot(111, polar=True)

        if counts.empty:
            ax.text(0.5, 0.5, "No topic data available", transform=ax.transAxes, ha="center", va="center")
            return fig

        counts = counts.head(max_topics).copy()
        labels = counts["label"].tolist()
        values = counts["count"].tolist()

        angles = np.linspace(0.0, 2.0 * np.pi, len(values), endpoint=False)
        bars = ax.bar(angles, values, width=(2 * np.pi / len(values)) * 0.9, bottom=0.0, color="#7b8ad6", alpha=0.85)

        # Add labels around circle
        ax.set_xticks(angles)
        ax.set_xticklabels(labels, fontsize=9)
        ax.set_yticklabels([])  # cleaner
        ax.set_title(title, fontsize=14, fontweight="bold", pad=20)
        plt.tight_layout()
        return fig

    @render.plot
    def pp_topics_radial_chart():
        level = "subissues" if _input_value(input, "pp_topics_radial_subissues", False) else "issues"
        counts = _topics_counts_for_radial(level)
        title = "Sub-issues by Number of Agreements" if level == "subissues" else "Issues by Number of Agreements"
        return build_topics_radial(counts, title)

    # ------------------------------
    # Diffusion analysis (controls via switches, display only relevant ones)
    # ------------------------------
    @render.ui
    def pp_diffusion_controls():
        # Place this output above the diffusion chart in the UI
        show_topics = _input_value(input, "pp_diffusion_mode_switch", None)
        # If not set yet, default to False (actors)
        show_topics = bool(False if show_topics is None else show_topics)

        return ui.div(
            ui.div(
                # Left-to-right inline switches
                ui.input_switch("pp_diffusion_mode_switch", "Topics over time", show_topics),
                ui.input_switch("pp_diffusion_xaxis_switch", "Use date axis", True),
                # Only show topic-level switch when "Topics over time" is selected
                ui.output_ui("pp_diffusion_topic_level_switch_ui"),
                class_="d-flex flex-wrap align-items-center gap-3",
            ),
            class_="mb-2",
        )

    @render.ui
    def pp_diffusion_topic_level_switch_ui():
        show_topics = bool(_input_value(input, "pp_diffusion_mode_switch", False))
        if not show_topics:
            return ui.div()
        # Switch for sub-issues (off -> issues; on -> sub-issues)
        return ui.input_switch("pp_diffusion_topic_level_switch", "Sub-issues", False)

    # Data
    @reactive.calc
    def pp_diffusion_data():
        data = filtered_pp_data()
        pax_df = data["pax"]
        if pax_df.empty:
            return {"agreements": [], "actors": [], "topics": []}

        pax_sorted = pax_df.copy()
        pax_sorted["date"] = pd.to_datetime(pax_sorted["Dat"], errors="coerce")
        pax_sorted = pax_sorted.dropna(subset=["date"]).sort_values("date")

        agreements = pax_sorted[["AgtId", "Agt", "date", "stage_label"]].to_dict("records")

        actors_data = []
        signatories = data["signatories"]
        if not signatories.empty:
            for _, agt in pax_sorted.iterrows():
                agt_signatories = signatories[signatories["AgtId"] == agt["AgtId"]]
                for _, sig in agt_signatories.iterrows():
                    actors_data.append(
                        {
                            "AgtId": agt["AgtId"],
                            "actor_name": sig["actor_name"],
                            "actor_type": "third_party" if sig["practical_third"] == 1 else "party",
                            "date": agt["date"],
                        }
                    )

        topics_data = []
        topics_df = data["pax_topics"]
        if not topics_df.empty:
            topics_level_switch = _input_value(input, "pp_diffusion_topic_level_switch", False)
            # Back-compat: if radio 'pp_diffusion_topic_level' exists, prefer it if available
            topics_level_radio = _input_value(input, "pp_diffusion_topic_level", None)
            diffusion_topic_level = "subissues" if topics_level_switch else "issues"
            if topics_level_radio in ("issues", "subissues"):
                diffusion_topic_level = topics_level_radio

            if diffusion_topic_level == "subissues":
                topics_filtered = topics_df[
                    (topics_df["value"] > 0)
                    & (topics_df["subissue_label"].notna())
                    & (topics_df["subissue_label"] != "")
                    & (topics_df["issue_label"].notna())
                    & (topics_df["issue_label"] != "")
                ]
                for _, agt in pax_sorted.iterrows():
                    agt_topics = topics_filtered[topics_filtered["AgtId"] == agt["AgtId"]]
                    for _, topic in agt_topics.iterrows():
                        combined_name = f"{topic['issue_label']} > {topic['subissue_label']}"
                        topics_data.append(
                            {"AgtId": agt["AgtId"], "topic_label": combined_name, "category": topic["category"], "date": agt["date"]}
                        )
            else:
                topics_filtered = topics_df[
                    (topics_df["value"] > 0) & (topics_df["issue_label"].notna()) & (topics_df["issue_label"] != "")
                ]
                for _, agt in pax_sorted.iterrows():
                    agt_topics = topics_filtered[topics_filtered["AgtId"] == agt["AgtId"]]
                    for _, topic in agt_topics.iterrows():
                        topics_data.append(
                            {"AgtId": agt["AgtId"], "topic_label": topic["issue_label"], "category": topic["category"], "date": agt["date"]}
                        )

        return {"agreements": agreements, "actors": actors_data, "topics": topics_data}

    def build_pp_diffusion_chart(diffusion_data, diffusion_type: str, x_axis_mode: str):
        agreements = diffusion_data["agreements"]
        fig, ax = plt.subplots(figsize=(20, 12))
        if not agreements:
            ax.text(0.5, 0.5, "No data available for diffusion chart", ha="center", va="center", transform=ax.transAxes)
            return fig

        if diffusion_type == "actors":
            actors_data = diffusion_data["actors"]
            if not actors_data:
                ax.text(0.5, 0.5, "No actor data available", ha="center", va="center", transform=ax.transAxes)
                return fig

            actors_df = pd.DataFrame(actors_data)
            actor_first_appearance = actors_df.groupby("actor_name")["date"].min().sort_values()
            sorted_actors = actor_first_appearance.index.tolist()
            agreement_ids = [a["AgtId"] for a in agreements]

            for i, actor in enumerate(sorted_actors):
                actor_agreements = actors_df[actors_df["actor_name"] == actor]["AgtId"].tolist()
                x_positions = [j for j, agt_id in enumerate(agreement_ids) if agt_id in actor_agreements]
                y_positions = [i] * len(x_positions)
                actor_type = actors_df[actors_df["actor_name"] == actor]["actor_type"].iloc[0]
                color = "#df1f36" if actor_type == "third_party" else "#091f40"
                if x_positions:
                    ax.scatter(x_positions, y_positions, alpha=0.9, s=20, color=color)
                    ax.plot(x_positions, y_positions, alpha=0.7, linewidth=1, color=color)

            ax.set_yticks(range(len(sorted_actors)))
            ax.set_yticklabels(sorted_actors, fontsize=10)
            ax.set_ylabel("Actors (in order of first appearance)", fontsize=12)

            from matplotlib.patches import Patch
            legend_elements = [Patch(facecolor="#091f40", label="Party Actors"), Patch(facecolor="#df1f36", label="Third Party Actors")]
            ax.legend(handles=legend_elements, bbox_to_anchor=(0.5, 1), loc="lower center", ncol=2, fontsize=12)
        else:
            topics_data = diffusion_data["topics"]
            if not topics_data:
                ax.text(0.5, 0.5, "No topic data available", ha="center", va="center", transform=ax.transAxes)
                return fig

            topics_df = pd.DataFrame(topics_data)
            topic_first_appearance = topics_df.groupby("topic_label")["date"].min().sort_values()
            sorted_topics = topic_first_appearance.index.tolist()

            if len(sorted_topics) > 30:
                topic_counts = topics_df["topic_label"].value_counts()
                sorted_topics = topic_counts.head(30).index.tolist()
                sorted_topics.sort(key=lambda x: topic_first_appearance.get(x, pd.Timestamp.max))

            agreement_ids = [a["AgtId"] for a in agreements]
            topic_categories = []
            for i, topic in enumerate(sorted_topics):
                topic_agreements = topics_df[topics_df["topic_label"] == topic]["AgtId"].tolist()
                topic_category = topics_df[topics_df["topic_label"] == topic]["category"].iloc[0]
                topic_categories.append(topic_category)
                x_positions = [j for j, agt_id in enumerate(agreement_ids) if agt_id in topic_agreements]
                y_positions = [i] * len(x_positions)
                unique_categories = list(set(topic_categories))
                category_colors = plt.cm.Set3(np.linspace(0, 1, len(unique_categories)))
                color_map = dict(zip(unique_categories, category_colors))
                color = color_map[topic_category]
                if x_positions:
                    ax.scatter(x_positions, y_positions, alpha=0.9, s=20, color=color)
                    ax.plot(x_positions, y_positions, alpha=0.7, linewidth=1, color=color)

            ax.set_yticks(range(len(sorted_topics)))
            ax.set_yticklabels(sorted_topics, fontsize=9)
            # Label depends on topic level: handled by switch/radio upstream
            ax.set_ylabel("Topics (in order of first appearance)", fontsize=12)

            # Legend for categories
            unique_categories = list(set(topic_categories))
            category_colors = plt.cm.Set3(np.linspace(0, 1, len(unique_categories)))
            color_map = dict(zip(unique_categories, category_colors))
            legend_elements = [plt.Line2D([0], [0], marker="o", color="w", markerfacecolor=color_map[cat], markersize=8, label=cat) for cat in unique_categories]
            ax.legend(handles=legend_elements, title="Topic Category", bbox_to_anchor=(0.5, 1), loc="lower center", ncol=5, fontsize=11)

        # X-axis handling
        if x_axis_mode == "date":
            dates = [a["date"] for a in agreements]
            if len(dates) > 1:
                date_range = pd.date_range(start=min(dates), end=max(dates), freq="MS")
                idx_map = {}
                for i, agt_date in enumerate(dates):
                    closest_month = min(date_range, key=lambda x: abs((x - agt_date).days))
                    month_pos = list(date_range).index(closest_month)
                    idx_map[i] = month_pos

                # Remap current lines/points
                for line in ax.lines:
                    x_data = line.get_xdata()
                    new_x_data = [idx_map.get(int(x), x) for x in x_data]
                    line.set_xdata(new_x_data)
                for coll in ax.collections:
                    offsets = coll.get_offsets()
                    if len(offsets) > 0:
                        new_offsets = [(idx_map.get(int(x), x), y) for x, y in offsets]
                        coll.set_offsets(new_offsets)

                # Ticks
                step = max(1, len(date_range) // 12)
                tick_positions = list(range(0, len(date_range), step))
                tick_labels = [date_range[i].strftime("%Y-%m") for i in tick_positions]
                ax.set_xticks(tick_positions)
                ax.set_xticklabels(tick_labels, rotation=45, fontsize=8)
                ax.set_xlabel("Agreement Date", fontsize=12)
            else:
                ax.set_xlabel("Agreement Date", fontsize=12)
        else:
            agt_names = [a["Agt"][:50] + "..." if len(a["Agt"]) > 50 else a["Agt"] for a in agreements]
            ax.set_xticks(range(len(agt_names)))
            ax.set_xticklabels(agt_names, rotation=90, fontsize=8)
            ax.set_xlabel("Agreements in Time Order", fontsize=12)

        ax.set_title(f"{diffusion_type.capitalize()} Diffusion Over Time", fontsize=16, fontweight="bold", y=1.15)
        ax.grid(alpha=0.2)
        plt.tight_layout()
        return fig

    @render.plot
    def pp_diffusion_chart():
        diffusion_data = pp_diffusion_data()

        # Prefer switches; fall back to legacy radios if present
        mode_switch = _input_value(input, "pp_diffusion_mode_switch", None)
        if mode_switch is not None:
            diffusion_type = "topics" if mode_switch else "actors"
        else:
            diffusion_type = _input_value(input, "pp_diffusion_type", "topics")

        xaxis_switch = _input_value(input, "pp_diffusion_xaxis_switch", None)
        if xaxis_switch is not None:
            x_axis_mode = "date" if xaxis_switch else "order"
        else:
            x_axis_mode = _input_value(input, "pp_diffusion_x_axis", "order")

        return build_pp_diffusion_chart(diffusion_data, diffusion_type, x_axis_mode)

    # -----------------------------------------------------------------------------
    # DOWNLOADS (PNG) — exported using builders + consistent filter/brand stamping
    # -----------------------------------------------------------------------------

    @output
    @render.download(filename="pp_agreements_over_time.png")
    def pp_export_over_time_png():
        try:
            td = pp_agreements_time_data()
            fig = build_pp_agreements_over_time(td, _input_value(input, "pp_time_granularity", "month"), _input_value(input, "pp_show_labels", False))
            filter_text = _get_pp_filter_text_for_png(get_applied_filters)
            data_version = _get_data_version(load_data)
            _add_logo_and_subtitle(fig, filter_text, data_version)

            buf = io.BytesIO()
            fig.savefig(buf, format="png", bbox_inches="tight", dpi=300, facecolor="white", edgecolor="none")
            buf.seek(0)
            plt.close(fig)
            return buf
        except Exception as e:
            print(f"Error in PNG export: {e}")
            return io.BytesIO()

    @output
    @render.download(filename="pp_stage_analysis.png")
    def pp_export_stage_png():
        try:
            sd = pp_stage_analysis_data()
            fig = build_pp_stage_analysis(sd, _input_value(input, "pp_show_labels", False))
            filter_text = _get_pp_filter_text_for_png(get_applied_filters)
            data_version = _get_data_version(load_data)
            _add_logo_and_subtitle(fig, filter_text, data_version)
            buf = io.BytesIO()
            fig.savefig(buf, format="png", bbox_inches="tight", dpi=300, facecolor="white", edgecolor="none")
            buf.seek(0)
            plt.close(fig)
            return buf
        except Exception as e:
            print(f"Error in PNG export: {e}")
            return io.BytesIO()

    @output
    @render.download(filename="pp_agreement_type_pie.png")
    def pp_export_agt_type_pie_png():
        try:
            fig = build_pp_agt_type_pie(pp_agreement_type_counts())
            filter_text = _get_pp_filter_text_for_png(get_applied_filters)
            data_version = _get_data_version(load_data)
            _add_logo_and_subtitle(fig, filter_text, data_version)
            buf = io.BytesIO()
            fig.savefig(buf, format="png", bbox_inches="tight", dpi=300, facecolor="white", edgecolor="none")
            buf.seek(0)
            plt.close(fig)
            return buf
        except Exception as e:
            print(f"Error in PNG export: {e}")
            return io.BytesIO()

    @output
    @render.download(filename="pp_party_signatories.png")
    def pp_export_party_sig_png():
        try:
            df = pp_signatories_data()["party"]
            fig = build_signatories_bar(df, title="Party Signatories", color="#091f40", mode=_input_value(input, "pp_signatory_mode", "count"))
            filter_text = _get_pp_filter_text_for_png(get_applied_filters)
            data_version = _get_data_version(load_data)
            _add_logo_and_subtitle(fig, filter_text, data_version)
            buf = io.BytesIO()
            fig.savefig(buf, format="png", bbox_inches="tight", dpi=300, facecolor="white", edgecolor="none")
            buf.seek(0)
            plt.close(fig)
            return buf
        except Exception as e:
            print(f"Error in PNG export: {e}")
            return io.BytesIO()

    @output
    @render.download(filename="pp_third_party_signatories.png")
    def pp_export_third_party_sig_png():
        try:
            df = pp_signatories_data()["third_party"]
            fig = build_signatories_bar(df, title="Third Party Signatories", color="#df1f36", mode=_input_value(input, "pp_signatory_mode", "count"))
            filter_text = _get_pp_filter_text_for_png(get_applied_filters)
            data_version = _get_data_version(load_data)
            _add_logo_and_subtitle(fig, filter_text, data_version)
            buf = io.BytesIO()
            fig.savefig(buf, format="png", bbox_inches="tight", dpi=300, facecolor="white", edgecolor="none")
            buf.seek(0)
            plt.close(fig)
            return buf
        except Exception as e:
            print(f"Error in PNG export: {e}")
            return io.BytesIO()

    @output
    @render.download(filename="pp_upset.png")
    def pp_export_upset_png():
        try:
            # Reuse the render logic by re-drawing via the same function
            # (Shiny figures are not guaranteed to persist; re-create figure)
            fig = pp_upset_plot()  # this returns a Matplotlib figure
            filter_text = _get_pp_filter_text_for_png(get_applied_filters)
            data_version = _get_data_version(load_data)
            _add_logo_and_subtitle(fig, filter_text, data_version)
            buf = io.BytesIO()
            fig.savefig(buf, format="png", bbox_inches="tight", dpi=300, facecolor="white", edgecolor="none")
            buf.seek(0)
            plt.close(fig)
            return buf
        except Exception as e:
            print(f"Error in PNG export: {e}")
            return io.BytesIO()

    @output
    @render.download(filename="pp_topics_categories.png")
    def pp_export_topic_categories_png():
        try:
            fig = pp_topics_categories_chart()
            filter_text = _get_pp_filter_text_for_png(get_applied_filters)
            data_version = _get_data_version(load_data)
            _add_logo_and_subtitle(fig, filter_text, data_version)
            buf = io.BytesIO()
            fig.savefig(buf, format="png", bbox_inches="tight", dpi=300, facecolor="white", edgecolor="none")
            buf.seek(0)
            plt.close(fig)
            return buf
        except Exception as e:
            print(f"Error in PNG export: {e}")
            return io.BytesIO()

    @output
    @render.download(filename="pp_topics_issues.png")
    def pp_export_topic_issues_png():
        try:
            fig = pp_topics_issues_chart()
            filter_text = _get_pp_filter_text_for_png(get_applied_filters)
            data_version = _get_data_version(load_data)
            _add_logo_and_subtitle(fig, filter_text, data_version)
            buf = io.BytesIO()
            fig.savefig(buf, format="png", bbox_inches="tight", dpi=300, facecolor="white", edgecolor="none")
            buf.seek(0)
            plt.close(fig)
            return buf
        except Exception as e:
            print(f"Error in PNG export: {e}")
            return io.BytesIO()

    @output
    @render.download(filename="pp_topics_radial.png")
    def pp_export_topics_radial_png():
        try:
            level = "subissues" if _input_value(input, "pp_topics_radial_subissues", False) else "issues"
            counts = _topics_counts_for_radial(level)
            title = "Sub-issues by Number of Agreements" if level == "subissues" else "Issues by Number of Agreements"
            fig = build_topics_radial(counts, title)
            filter_text = _get_pp_filter_text_for_png(get_applied_filters)
            data_version = _get_data_version(load_data)
            _add_logo_and_subtitle(fig, filter_text, data_version)
            buf = io.BytesIO()
            fig.savefig(buf, format="png", bbox_inches="tight", dpi=300, facecolor="white", edgecolor="none")
            buf.seek(0)
            plt.close(fig)
            return buf
        except Exception as e:
            print(f"Error in PNG export: {e}")
            return io.BytesIO()

    @output
    @render.download(filename="pp_diffusion_chart.png")
    def pp_export_diffusion_png():
        try:
            diffusion_data = pp_diffusion_data()
            mode_switch = _input_value(input, "pp_diffusion_mode_switch", None)
            if mode_switch is not None:
                diffusion_type = "topics" if mode_switch else "actors"
            else:
                diffusion_type = _input_value(input, "pp_diffusion_type", "topics")

            xaxis_switch = _input_value(input, "pp_diffusion_xaxis_switch", None)
            if xaxis_switch is not None:
                x_axis_mode = "date" if xaxis_switch else "order"
            else:
                x_axis_mode = _input_value(input, "pp_diffusion_x_axis", "order")

            fig = build_pp_diffusion_chart(diffusion_data, diffusion_type, x_axis_mode)
            filter_text = _get_pp_filter_text_for_png(get_applied_filters)
            data_version = _get_data_version(load_data)
            _add_logo_and_subtitle(fig, filter_text, data_version)
            buf = io.BytesIO()
            fig.savefig(buf, format="png", bbox_inches="tight", dpi=300, facecolor="white", edgecolor="none")
            buf.seek(0)
            plt.close(fig)
            return buf
        except Exception as e:
            print(f"Error in PNG export: {e}")
            return io.BytesIO()

    # -----------------------------------------------------------------------------
    # DOWNLOADS (CSV)
    # -----------------------------------------------------------------------------

    @output
    @render.download(filename="pp_agreements_over_time.csv")
    def pp_export_time_csv():
        try:
            df = pp_agreements_time_data()
            csv_string = df.to_csv(index=False)
            return io.BytesIO(csv_string.encode("utf-8"))
        except Exception as e:
            print(f"Error in CSV export: {e}")
            return io.BytesIO(b"Error,Message\nExport Failed,Please try again")

    @output
    @render.download(filename="pp_stage_analysis.csv")
    def pp_export_stage_csv():
        try:
            df = pp_stage_analysis_data()
            csv_string = df.to_csv(index=False)
            return io.BytesIO(csv_string.encode("utf-8"))
        except Exception as e:
            print(f"Error in CSV export: {e}")
            return io.BytesIO(b"Error,Message\nExport Failed,Please try again")

    @output
    @render.download(filename="pp_agreement_type_pie.csv")
    def pp_export_agt_type_pie_csv():
        try:
            df = pp_agreement_type_counts()
            csv_string = df.to_csv(index=False)
            return io.BytesIO(csv_string.encode("utf-8"))
        except Exception as e:
            print(f"Error in CSV export: {e}")
            return io.BytesIO(b"Error,Message\nExport Failed,Please try again")

    @output
    @render.download(filename="pp_signatories.csv")
    def pp_export_sig_csv():
        try:
            sig_data = pp_signatories_data()
            party_df = sig_data["party"].copy()
            third_party_df = sig_data["third_party"].copy()
            if not party_df.empty:
                party_df["signatory_type"] = "party"
            if not third_party_df.empty:
                third_party_df["signatory_type"] = "third_party"
            combined_df = pd.concat([party_df, third_party_df], ignore_index=True)
            csv_string = combined_df.to_csv(index=False)
            return io.BytesIO(csv_string.encode("utf-8"))
        except Exception as e:
            print(f"Error in CSV export: {e}")
            return io.BytesIO(b"Error,Message\nExport Failed,Please try again")

    @output
    @render.download(filename="pp_third_party_signatories.csv")
    def pp_export_third_party_sig_csv():
        try:
            sig_data = pp_signatories_data()
            third_party_df = sig_data["third_party"].copy()
            if not third_party_df.empty:
                third_party_df["signatory_type"] = "third_party"
            csv_string = third_party_df.to_csv(index=False)
            return io.BytesIO(csv_string.encode("utf-8"))
        except Exception as e:
            print(f"Error in CSV export: {e}")
            return io.BytesIO(b"Error,Message\nExport Failed,Please try again")

    @output
    @render.download(filename="pp_topic_categories.csv")
    def pp_export_topic_categories_csv():
        try:
            df = pp_topics_category_data()
            csv_string = df.to_csv(index=False)
            return io.BytesIO(csv_string.encode("utf-8"))
        except Exception as e:
            print(f"Error in CSV export: {e}")
            return io.BytesIO(b"Error,Message\nExport Failed,Please try again")

    @output
    @render.download(filename="pp_topic_subissues.csv")
    def pp_export_topic_subissues_csv():
        try:
            df = pp_topics_subissue_data()
            csv_string = df.to_csv(index=False)
            return io.BytesIO(csv_string.encode("utf-8"))
        except Exception as e:
            print(f"Error in CSV export: {e}")
            return io.BytesIO(b"Error,Message\nExport Failed,Please try again")

    @output
    @render.download(filename="pp_topic_issues.csv")
    def pp_export_topic_issues_csv():
        try:
            df = pp_topics_issue_data()
            csv_string = df.to_csv(index=False)
            return io.BytesIO(csv_string.encode("utf-8"))
        except Exception as e:
            print(f"Error in CSV export: {e}")
            return io.BytesIO(b"Error,Message\nExport Failed,Please try again")

    @output
    @render.download(filename="pp_topics_radial.csv")
    def pp_export_topics_radial_csv():
        try:
            level = "subissues" if _input_value(input, "pp_topics_radial_subissues", False) else "issues"
            df = _topics_counts_for_radial(level)
            csv_string = df.to_csv(index=False)
            return io.BytesIO(csv_string.encode("utf-8"))
        except Exception as e:
            print(f"Error in CSV export: {e}")
            return io.BytesIO(b"Error,Message\nExport Failed,Please try again")
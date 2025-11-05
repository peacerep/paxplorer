#server/peace_process.py
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
from utils.png_export_utils import (
    export_with_branding,
    get_data_version,
    add_logo_and_subtitle,
    LOGO_POSITIONS
)

from utils.data_loader import load_pax_data

# alias to match old export_with_branding argument
def load_data():
    """Compatibility wrapper for exports after migrating to load_pax_data()."""
    return load_pax_data()



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


def input_value(input, name: str, default=None):
    try:
        return getattr(input, name)()
    except Exception:
        return default


def get_pp_filter_text_for_png(get_applied_filters_fn) -> str:
    try:
        filters = get_applied_filters_fn()
    except Exception:
        filters = []
    if not filters:
        return "No filters applied"
    return " | ".join(filters)  # Changed to match home.py style


# def get_data_version(load_data_fn) -> str:
#     try:
#         pax = load_data_fn()["pax"]
#         if "Ver" in pax.columns and not pax["Ver"].isna().all():
#             return str(pax["Ver"].max())
#     except Exception:
#         pass
#     return "Unknown"


# def add_logo_and_subtitle(
#     fig,
#     filter_text: str,
#     data_version: str,
#     *,
#     logo_position=(0.92, 0.94, 0.078, 0.078),
#     filter_text_position=(0.5, 0.009),
#     version_position=(0.98, 0.02)
# ):
#     """Add filter text, data version, and logo to a Matplotlib figure.
#     Positions can be overridden per chart.
#     """
#     # Subtitle (bottom-center)
#     fig.text(
#         filter_text_position[0],
#         filter_text_position[1],
#         filter_text,
#         transform=fig.transFigure,
#         ha="center",
#         va="bottom",
#         fontsize=8,
#         style="italic",
#         color="#666666",
#     )

#     # Data version (bottom-right)
#     fig.text(
#         version_position[0],
#         version_position[1],
#         f"PA-X Database v{data_version}",
#         transform=fig.transFigure,
#         ha="right",
#         va="bottom",
#         fontsize=7,
#         color="#999999",
#     )

#     # Logo (top-right)
#     try:
#         logo_img = plt.imread(LOGO_PATH)
#         logo_ax = fig.add_axes(list(logo_position))
#         logo_ax.imshow(logo_img, alpha=0.8)
#         logo_ax.axis("off")
#     except Exception as e:
#         print(f"Warning: Could not add logo: {e}")

# def export_with_branding(
#     plot_func,
#     *,
#     filter_text_fn=None,
#     data_version_fn=None,
#     load_data_fn=None,
#     logo_position=(0.92, 0.94, 0.078, 0.078),
#     filter_text_position=(0.5, 0.009),
#     version_position=(0.98, 0.02),
# ):
#     """
#     Reuse a rendered Matplotlib figure for PNG export, then add branding.
#     - load_data_fn: pass your load_data function if needed for data_version_fn
#     """
#     try:
#         if hasattr(plot_func, "_fn"):
#             fig = plot_func._fn()
#         else:
#             fig = plot_func()

#         # Compute metadata
#         filter_text = filter_text_fn() if filter_text_fn else "Filters applied"
#         data_version = (
#             data_version_fn(load_data_fn) if (data_version_fn and load_data_fn)
#             else (data_version_fn() if data_version_fn else "Unknown")
#         )

#         add_logo_and_subtitle(
#             fig,
#             filter_text,
#             data_version,
#             logo_position=logo_position,
#             filter_text_position=filter_text_position,
#             version_position=version_position,
#         )

#         buf = io.BytesIO()
#         fig.savefig(
#             buf,
#             format="png",
#             bbox_inches="tight",
#             dpi=300,
#             facecolor="white",
#             edgecolor="none",
#         )
#         buf.seek(0)
#         plt.close(fig)
#         print(f"[DEBUG] Successfully exported {plot_func.__name__}")
#         return buf

#     except Exception as e:
#         print(f"Error exporting PNG: {e}")
#         return io.BytesIO()



def server(input, output, session):
    """Server logic for peace process page"""

    plt.rcParams.update({
        "figure.dpi": 110,
        "figure.autolayout": False,
        "figure.subplot.left": 0.25,
        "figure.subplot.right": 0.95,
        "figure.subplot.bottom": 0.12,
        "figure.subplot.top": 0.9,
    })

    
    # =========================================================================
    # DATA LOADING - Load once and cache
    # =========================================================================
    
    # @reactive.calc
    # # Load once, outside reactive context
    # def load_data():
    #     """Load all data once (non-reactive)."""
    #     if not hasattr(load_data, "_cache"):
    #         pax = pd.read_csv("data/pax.csv")
    #         pax_id_to_con = pd.read_csv("data/pax_id_to_con_info.csv")
    #         pax_topics = pd.read_csv("data/all_pax_topics_no_imp.csv")
    #         signatories = pd.read_csv("data/paax_signatory_v0.2_internal.csv")

    #         pax["date"] = pd.to_datetime(pax["Dat"], errors="coerce")
    #         load_data._cache = {
    #             "pax": pax,
    #             "pax_id_to_con": pax_id_to_con,
    #             "pax_topics": pax_topics,
    #             "signatories": signatories,
    #         }
    #     return load_data._cache

    #HERE

    
    # =========================================================================
    # FILTER CHOICES - Calculate available options for each filter
    # =========================================================================
    
    @reactive.calc
    def peace_process_choices():
        """Get available peace processes"""
        data = load_pax_data()
        return sorted(data["pax"]["PPName"].dropna().unique().tolist())
    
    @reactive.calc  
    def pp_agt_type_choices():
        """Get available agreement types"""
        data = load_pax_data()
        return sorted(data["pax"]["agt_type"].dropna().unique().tolist())
    
    @reactive.calc
    def pp_stage_choices():
        """Get available stages"""
        data = load_pax_data()
        return sorted(data["pax"]["stage_label"].dropna().unique().tolist())
    
    @reactive.calc
    def pp_year_range():
        """Get min and max years in dataset"""
        data = load_pax_data()
        min_year = int(data["pax"]["year"].min())
        max_year = int(data["pax"]["year"].max())
        return [min_year, max_year]
    
    @reactive.calc
    def pp_date_range():
        """Get min and max dates in dataset"""
        data = load_pax_data()
        dates = pd.to_datetime(data["pax"]["Dat"], errors='coerce', dayfirst=True).dropna()
        if dates.empty:
            return [None, None]
        return [dates.min().date(), dates.max().date()]
    
    # =========================================================================
    # POPULATE UI - Update all dropdowns and controls
    # =========================================================================
    
    @reactive.effect
    def _():
        """Populate all UI controls with choices"""
        peace_processes = peace_process_choices()
        agt_types = pp_agt_type_choices()
        stages = pp_stage_choices()
        year_min, year_max = pp_year_range()
        date_min, date_max = pp_date_range()
        
        # Update all controls
        ui.update_selectize("selected_peace_process", 
                          choices=peace_processes, 
                          selected=peace_processes[0] if peace_processes else None)
        ui.update_selectize("pp_agt_type", choices=agt_types, selected=[])
        ui.update_selectize("pp_stage", choices=stages, selected=[])
        ui.update_slider("pp_year_range", min=year_min, max=year_max, value=[year_min, year_max])
        if date_min and date_max:
            ui.update_date_range("pp_date_range", start=date_min, end=date_max)
    
    # =========================================================================
    # FILTERED DATA - Apply all selected filters
    # =========================================================================
    @reactive.calc
    def base_pp_data():
        """Filter only by selected peace process (primary filter)."""
        data = load_pax_data()
        df = data["pax"]

        selected_pp = input.selected_peace_process()
        if not selected_pp:
            return pd.DataFrame(columns=df.columns)

        # Filter once by peace process
        df = df[df["PPName"] == selected_pp].copy()

        return df

    @reactive.calc
    def filtered_pp_data():
        """Apply all selected filters to the data"""
        data = load_pax_data()
        df = base_pp_data()  # start from peace-process–filtered data
        if df.empty:
            return {"pax": df, "pax_id_to_con": data["pax_id_to_con"], "pax_topics": pd.DataFrame(), "signatories": pd.DataFrame()}
        
        # Filter by peace process (PRIMARY FILTER)
        selected_pp = input.selected_peace_process()
        if selected_pp:
            df = df[df["PPName"] == selected_pp]
        
        # Filter by agreement type
        selected_types = input.pp_agt_type()
        if selected_types and len(selected_types) > 0:
            if isinstance(selected_types, str):
                selected_types = [selected_types]
            df = df[df["agt_type"].isin(selected_types)]
        
        # Filter by year range
        year_range_vals = input.pp_year_range()
        if year_range_vals and len(year_range_vals) == 2:
            df = df[(df["year"] >= year_range_vals[0]) & (df["year"] <= year_range_vals[1])]
        
        # Filter by date range
        date_range_vals = input.pp_date_range()
        if date_range_vals and len(date_range_vals) == 2 and date_range_vals[0] and date_range_vals[1]:
            df['date'] = pd.to_datetime(df['Dat'], errors='coerce', dayfirst=True)
            start_date = pd.to_datetime(date_range_vals[0])
            end_date = pd.to_datetime(date_range_vals[1])
            df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
        
        # Filter by stage
        selected_stages = input.pp_stage()
        if selected_stages and len(selected_stages) > 0:
            if isinstance(selected_stages, str):
                selected_stages = [selected_stages]
            df = df[df["stage_label"].isin(selected_stages)]
        
        # Get agreement IDs and filter related datasets
        agt_ids = df["AgtId"].unique()
        filtered_topics = data["pax_topics"][data["pax_topics"]["AgtId"].isin(agt_ids)]
        filtered_signatories = data["signatories"][data["signatories"]["AgtId"].isin(agt_ids)] if not data["signatories"].empty else pd.DataFrame()
        
        return {
            "pax": df,
            "pax_id_to_con": data["pax_id_to_con"],
            "pax_topics": filtered_topics,
            "signatories": filtered_signatories
        }
    
    # =========================================================================
    # APPLIED FILTERS - Track and display selected filters
    # =========================================================================
    
    @reactive.calc
    def get_applied_filters():
        """Get applied filters summary for SIDEBAR display (truncated)"""
        filters = []

        # Peace Process (always shown as it's the primary filter)
        selected_pp = input.selected_peace_process()
        if selected_pp:
            filters.append(f"Peace Process: {selected_pp}")

        # Agreement Types
        types = input.pp_agt_type()
        if types:
            text = f"Agreement Type: {', '.join(types)}"
            if len(types) > 2:
                text = f"Agreement Type: {', '.join(types[:2])} + {len(types)-2} more"
            filters.append(text)

        # Year Range (only show if not default)
        year_range_vals = input.pp_year_range()
        year_min, year_max = pp_year_range()
        if year_range_vals and len(year_range_vals) == 2:
            if year_range_vals[0] != year_min or year_range_vals[1] != year_max:
                filters.append(f"Years: {year_range_vals[0]}-{year_range_vals[1]}")

        # Date Range
        date_range_vals = input.pp_date_range()
        date_min, date_max = pp_date_range()
        if date_range_vals and len(date_range_vals) == 2 and date_range_vals[0] and date_range_vals[1]:
            # Only show if not default range
            if date_range_vals[0] != date_min or date_range_vals[1] != date_max:
                filters.append(f"Date Range: {date_range_vals[0]} to {date_range_vals[1]}")

        # Stages
        stages = input.pp_stage()
        if stages:
            text = f"Stages: {', '.join(stages)}"
            if len(stages) > 3:
                text = f"Stages: {', '.join(stages[:3])} + {len(stages)-3} more"
            filters.append(text)

        return filters
    
    @reactive.calc
    def get_applied_filters_full():
        """Get applied filters for PNG export (FULL - no truncation)"""
        filters = []
        
        # Peace Process (PRIMARY - always include)
        selected_pp = input.selected_peace_process()
        if selected_pp:
            filters.append(f"Peace Process = {selected_pp}")
        
        # Agreement Types - show all
        types = input.pp_agt_type()
        if types and len(types) > 0:
            filters.append(f"Agreement Type = {', '.join(types)}")
        
        # Year Range (only show if not default)
        year_range_vals = input.pp_year_range()
        year_min, year_max = pp_year_range()
        if year_range_vals and len(year_range_vals) == 2:
            if year_range_vals[0] != year_min or year_range_vals[1] != year_max:
                filters.append(f"Years = {year_range_vals[0]}-{year_range_vals[1]}")
        
        # Date Range (only show if not default)
        date_range_vals = input.pp_date_range()
        date_min, date_max = pp_date_range()
        if date_range_vals and len(date_range_vals) == 2 and date_range_vals[0] and date_range_vals[1]:
            if date_range_vals[0] != date_min or date_range_vals[1] != date_max:
                filters.append(f"Date Range = {date_range_vals[0]} to {date_range_vals[1]}")
        
        # Stages - show all
        stages = input.pp_stage()
        if stages and len(stages) > 0:
            filters.append(f"Stages = {', '.join(stages)}")
        
        return filters
    
    @reactive.calc
    def get_filter_text_for_png():
        """Get filter text formatted for PNG annotations"""
        filters = get_applied_filters_full()
        if not filters:
            return "Showing all data"
        return f"Filters applied: {' | '.join(filters)}"
    
    # =========================================================================
    # UI DISPLAY FUNCTIONS
    # =========================================================================
    
    @render.ui
    def pp_applied_filters():
        """Display applied filters in sidebar"""
        filters = get_applied_filters()
        
        if not filters:
            return ui.div(
                ui.tags.i(class_="fas fa-info-circle me-2"),
                "No filters applied",
                style="color: #6c757d; font-style: italic;"
            )
        
        filter_items = []
        for filter_text in filters:
            filter_items.append(
                ui.div(
                    ui.tags.i(class_="fas fa-filter me-2", style="color: #007bff;"),
                    filter_text,
                    class_="mb-1"
                )
            )
        
        return ui.div(*filter_items)
    
    @render.ui
    def pp_filter_summary():
        """Display filter summary statistics"""
        data = load_pax_data()
        total_agreements = data["pax"]["AgtId"].nunique()
        
        filtered_data_result = filtered_pp_data()
        filtered_agreements = filtered_data_result["pax"]["AgtId"].nunique()
        percentage = (filtered_agreements / total_agreements * 100) if total_agreements > 0 else 0
        
        # Year range display
        year_range_vals = input.pp_year_range()
        year_min, year_max = pp_year_range()
        if year_range_vals[0] == year_min and year_range_vals[1] == year_max:
            year_span = ""
        else:
            year_span = f" ({year_range_vals[0]}-{year_range_vals[1]})"
        
        return ui.div(
            f"Showing {filtered_agreements:,} of {total_agreements:,} agreements ({percentage:.1f}%){year_span}",
            style="font-weight: 500;"
        )
    
    # =========================================================================
    # RESET FILTERS
    # =========================================================================
    
    @reactive.effect
    @reactive.event(input.pp_reset_filters)
    def _():
        """Reset only sidebar filters (keep peace process selection)."""
        year_min, year_max = pp_year_range()
        date_min, date_max = pp_date_range()

        # DO NOT reset the peace process
        # Keep current selection for selected_peace_process

        # Reset secondary filters only
        ui.update_selectize("pp_agt_type", selected=[])
        ui.update_selectize("pp_stage", selected=[])
        ui.update_slider("pp_year_range", value=[year_min, year_max])
        if date_min and date_max:
            ui.update_date_range("pp_date_range", start=date_min, end=date_max)
    
    # =========================================================================
    # SUMMARY STATISTICS
    # =========================================================================
    
    @render.ui
    def pp_summary_stats():
        """Display summary statistics for selected peace process"""
        selected_pp = input.selected_peace_process()
        
        if not selected_pp:
            return ui.div("Select a peace process to see summary", 
                        style="color: #6c757d; font-style: italic;")
        
        data = filtered_pp_data()
        df = data["pax"]
        
        if df.empty:
            return ui.div("No data available", style="color: #6c757d;")
        
        # Calculate summary stats
        num_agreements = df["AgtId"].nunique()
        
        # Get date range
        dates = pd.to_datetime(df['Dat'], errors='coerce', dayfirst=True).dropna()
        if not dates.empty:
            first_date = dates.min().strftime('%d-%m-%Y')
            last_date = dates.max().strftime('%d-%m-%Y')
            date_range = f"{first_date} to {last_date}"
        else:
            date_range = "No dates available"
        
        return ui.div(
            ui.div(
               # ui.tags.img(src="static/logos/agreements_icon.png", 
                #          style="width: 20px; height: 20px; margin-right: 8px; vertical-align: middle;"),
                f"{num_agreements} agreements", 
                style="font-weight: bold; margin-bottom: 5px; display: flex; align-items: center; justify-content: center;"
            ),
            ui.div(
                #ui.tags.img(src="static/logos/calendar.png", 
                          #style="width: 18px; height: 18px; margin-right: 8px; vertical-align: middle;"),
                f"{date_range}", 
                style="font-size: 0.9em; color: #666; display: flex; align-items: center; justify-content: center;"
            ),
            style="text-align: center;"
        )
    
    @render.ui
    def pp_database_link():
        """Display link to PA-X database for selected peace process"""
        selected_pp = input.selected_peace_process()
        
        if not selected_pp:
            return ui.div()
        
        data = load_pax_data()
        matching_rows = data["pax"][data["pax"]["PPName"] == selected_pp]
        if matching_rows.empty:
            return ui.div()
        
        # Get the PP value for the URL
        selected_pp_id = matching_rows["PP"].iloc[0]
        
        # Create the database search URL
        base_url = "https://www.peaceagreements.org/agreements/search/?search_type=basic-search&show_timeline=1&match_any_issues=True"
        search_url = f"{base_url}&process={selected_pp_id}#timeline"
        
        return ui.div(
            ui.tags.a(
                #ui.tags.img(src="static/logos/Pax_white.png", style="width: 28px; height: 28px; margin-right: 8px; vertical-align: middle;"),
                "View Agreements on PA-X",
                href=search_url,
                target="_blank",
                class_="btn btn-primary",
                style="text-decoration: none; display: flex; align-items: center; justify-content: center;"
            ),
            style="text-align: center;"
        )

    # Messy timeline iframe
    @render.ui
    def external_viz_iframe():
        selected_pp_name = input.selected_peace_process()
        
        if not selected_pp_name:
            return ui.div("Please select a peace process to view the visualization.")
        
        # Get the PP value for the selected PPName
        data = load_pax_data()
        if data is None:
            return ui.div("Data not available.")
        
        # Find the PP value corresponding to the selected PPName
        matching_rows = data["pax"][data["pax"]["PPName"] == selected_pp_name]
        if matching_rows.empty:
            return ui.div("No matching peace process found.")
        
        # Get the first PP value (they should all be the same for a given PPName)
        selected_pp_id = matching_rows["PP"].iloc[0]
        
        # Replace with your actual base URL
        base_url = "https://peacerep.github.io/v7_messy_timeline/"
        full_url = f"{base_url}?subset={selected_pp_id}"
        
        return ui.tags.iframe(
            src=full_url,
            width="100%",
            height="100%",
            style="border: 1px solid #ddd; border-radius: 4px;"
        )
    
    # Agreements over time (month-year aggregation) - matching home page style
    @reactive.calc
    def pp_agreements_time_data():
        data = filtered_pp_data()
        df = data["pax"]
        
        if df.empty:
            return pd.DataFrame()
        
        # Convert date to datetime
        df['date'] = pd.to_datetime(df['Dat'], errors='coerce', dayfirst=True)
        df = df.dropna(subset=['date'])
        
        granularity = input.pp_time_granularity()
        
        # Create time period based on granularity (removed day option)
        if granularity == "year":
            df['time_period'] = df['date'].dt.year
        else:  # month (default)
            df['time_period'] = df['date'].dt.strftime('%Y-%m')
        
        # Group by time period and stage
        time_data = df.groupby(['time_period', 'stage_label'])['AgtId'].nunique().reset_index(name='count')
        
        # Create complete time range
        if not time_data.empty:
            if granularity == "month":
                # Create month range
                min_date = df['date'].min()
                max_date = df['date'].max()
                all_periods = pd.date_range(start=min_date.replace(day=1), 
                                        end=max_date, freq='MS').strftime('%Y-%m')
            else:  # year
                min_year = df['date'].dt.year.min()
                max_year = df['date'].dt.year.max()
                all_periods = range(min_year, max_year + 1)
            
            # Get all stages from stage_order
            all_stages = stage_order
            
            # Create complete grid
            complete_grid = []
            for period in all_periods:
                for stage in all_stages:
                    complete_grid.append({'time_period': period, 'stage_label': stage})
            
            complete_df = pd.DataFrame(complete_grid)
            time_data = complete_df.merge(time_data, on=['time_period', 'stage_label'], how='left').fillna(0)
            time_data['count'] = time_data['count'].astype(int)
        
        return time_data
    
    def make_pp_agreements_over_time_figure():
        time_data = pp_agreements_time_data()
        granularity = input.pp_time_granularity()
        fig, ax = plt.subplots(figsize=(12, 8))  # Same as home.py
        
        if time_data.empty:
            ax.text(0.5, 0.5, 'No data available for selected peace process', 
                ha='center', va='center', transform=ax.transAxes, fontsize=14)
            ax.set_xticks([])
            ax.set_yticks([])
            return fig
        
        # Create pivot table for stacked bar chart
        pivot_df = time_data.pivot(index='time_period', columns='stage_label', values='count').fillna(0)
        
        # Order stages according to stage_order
        available_stages = [stage for stage in stage_order if stage in pivot_df.columns]
        other_stages = [stage for stage in pivot_df.columns if stage not in stage_order]
        pivot_df = pivot_df[available_stages + other_stages]
        
        # Use your existing color scheme for stages
        colors = get_colors_for_grouping("Stage", pivot_df.columns)
        
        # Create stacked bar chart with custom colors
        pivot_df.plot(kind='bar', stacked=True, ax=ax, color=colors, width=0.8)
        
        # Set y-axis limit to max value + margin (same as home.py)
        year_totals = pivot_df.sum(axis=1)
        max_total = year_totals.max()
        ax.set_ylim(0, max_total + 2)
        
        # Add data labels if enabled (same as home.py)
        if input.pp_show_labels():
            year_totals = pivot_df.sum(axis=1)
            for i, total in enumerate(year_totals):
                if total > 0:
                    ax.text(i, total + 0.25, f"{int(total)}", ha='center', fontsize=10, fontweight='bold')
            for container in ax.containers:
                ax.bar_label(container, fmt='%d', label_type='center', fontsize=8, color='white')
        
        ax.set_xlabel("Time Period", fontsize=12)
        ax.set_ylabel("Number of Agreements", fontsize=12)
        ax.set_title(f"Number of Agreements Over Time, by Stage of Process", fontsize=16, fontweight='bold', pad=20, y=1.145)
        
        # Format x-axis based on granularity
        ax.tick_params(axis='x', rotation=45)
        
        if granularity == "month" and len(pivot_df) > 12:
            # For months, show every 3rd month if more than 12
            n_ticks = max(1, len(pivot_df) // 6)
            tick_positions = list(range(0, len(pivot_df), n_ticks))
            ax.set_xticks(tick_positions)
            ax.set_xticklabels([pivot_df.index[i] for i in tick_positions])
        
        # Legend (same as home.py)
        ncol = len(pivot_df.columns) if len(pivot_df.columns) <= 4 else 4
        ax.legend(title="Stage", bbox_to_anchor=(0.5, 1), loc='lower center', fontsize=10, ncol=ncol)
        
        plt.tight_layout()
        
        return fig


    @render.plot
    def pp_agreements_over_time():
        return make_pp_agreements_over_time_figure()
    
    # Stage Analysis 
    @reactive.calc
    def pp_stage_analysis_data():
        data = filtered_pp_data()
        df = data["pax"]
        all_data = load_pax_data()
        
        if df.empty or all_data is None:
            return pd.DataFrame()
        
        # Calculate stage distributions for both filtered and all data
        filtered_stage_data = df.groupby("stage_label")["AgtId"].nunique().reset_index(name="filtered_count")
        all_stage_data = all_data["pax"].groupby("stage_label")["AgtId"].nunique().reset_index(name="all_count")
        
        total_filtered = df["AgtId"].nunique()
        total_all = all_data["pax"]["AgtId"].nunique()
        
        # Create a complete dataframe with all stages
        all_stages_df = pd.DataFrame({'stage_label': stage_order})
        
        # Merge with actual data
        stage_data = all_stages_df.merge(filtered_stage_data, on="stage_label", how="left").fillna(0)
        stage_data = stage_data.merge(all_stage_data, on="stage_label", how="left").fillna(0)
        
        stage_data["filtered_percentage"] = (stage_data["filtered_count"] / total_filtered * 100) if total_filtered > 0 else 0
        stage_data["all_percentage"] = (stage_data["all_count"] / total_all * 100) if total_all > 0 else 0
        
        return stage_data
    
    def make_stage_plot():
        stage_data = pp_stage_analysis_data()
        selected_pp_name = input.selected_peace_process()
        
        if stage_data.empty:
            fig, ax = plt.subplots(figsize=(12, 8))
            ax.text(0.5, 0.5, 'No stage data available', 
                ha='center', va='center', transform=ax.transAxes, fontsize=14)
            return fig
        
        fig, ax = plt.subplots(figsize=(12, 8))
        
        x = np.arange(len(stage_data))
        width = 0.35
        
        bars1 = ax.bar(x - width/2, stage_data["filtered_percentage"], width, 
                    label=f"{selected_pp_name}", color='#091f40')
        bars2 = ax.bar(x + width/2, stage_data["all_percentage"], width, 
                    label='All Agreements', color='#cccccc')
        
        if input.pp_show_labels():
            filtered_labels = stage_data["filtered_percentage"].round(0).astype(int).astype(str) + "%"
            all_labels = stage_data["all_percentage"].round(0).astype(int).astype(str) + "%"
            
            for bars, labels in [(bars1, filtered_labels), (bars2, all_labels)]:
                for bar, label in zip(bars, labels):
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2, height + 1, label, 
                        ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        ax.set_xticks(x)
        ax.set_xticklabels(stage_data["stage_label"])
        ax.set_xlabel("Stage", fontsize=12)
        ax.set_ylabel("Percentage of Agreements", fontsize=12)
        ax.set_title("Percentage of Agreements per Stage of Process", fontsize=16, fontweight='bold', pad=20, y=1.15)
        ax.spines[['top', 'right']].set_visible(False)
        
        y_max = max(bars1.datavalues.max(), bars2.datavalues.max())
        ax.set_ylim(0, y_max + 10)
        
        ax.legend(bbox_to_anchor=(0.5, 1), loc='lower center', ncol=2, fontsize=12)
        
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        return fig

    @render.plot
    def pp_stage_analysis():
        return make_stage_plot()
        
    # Signatories data
    @reactive.calc
    def pp_signatories_data():
        data = filtered_pp_data()
        signatories = data["signatories"]
        
        if signatories.empty:
            return {"party": pd.DataFrame(), "third_party": pd.DataFrame()}
        
        # Create signatory type based on practical_third column
        signatories = signatories.copy()
        signatories['signatory_type'] = signatories['practical_third'].apply(
            lambda x: 'third party' if x == 1 else 'party'
        )
        
        # Split by signatory type
        party_signatories = signatories[signatories["signatory_type"] == "party"]
        third_party_signatories = signatories[signatories["signatory_type"] == "third party"]
        
        # Count agreements per actor using actor_name column
        party_counts = party_signatories.groupby("actor_name")["AgtId"].nunique().reset_index(name="count") if not party_signatories.empty else pd.DataFrame(columns=["actor_name", "count"])
        third_party_counts = third_party_signatories.groupby("actor_name")["AgtId"].nunique().reset_index(name="count") if not third_party_signatories.empty else pd.DataFrame(columns=["actor_name", "count"])
        
        # Calculate percentages
        total_agreements = data["pax"]["AgtId"].nunique()
        if total_agreements > 0:
            if not party_counts.empty:
                party_counts["percentage"] = party_counts["count"] / total_agreements * 100
            else:
                party_counts["percentage"] = []
            if not third_party_counts.empty:
                third_party_counts["percentage"] = third_party_counts["count"] / total_agreements * 100
            else:
                third_party_counts["percentage"] = []
        
        return {"party": party_counts, "third_party": third_party_counts}
    
    # UPDATED: Separate plots for party and third party signatories
    def make_party_sigs_plot():
        sig_data = pp_signatories_data()
        party_data = sig_data["party"]
        
        if party_data.empty:
            fig, ax = plt.subplots(figsize=(12, 8))
            ax.text(0.5, 0.5, 'No party signatory data available',
                    ha='center', va='center', transform=ax.transAxes)
            return fig
        
        # Sort and limit to top 15
        party_data = party_data.sort_values("count", ascending=True).tail(15)
        
        fig, ax = plt.subplots(figsize=(16, 8))
        plt.subplots_adjust(left=0.35, right=0.95)

        mode = input.pp_signatory_mode()
        if mode == "percentage":
            y_vals = party_data["percentage"]
            xlabel = "Percentage of Agreements"
        else:
            y_vals = party_data["count"]
            xlabel = "Number of Agreements"
        
        bars = ax.barh(party_data["actor_name"], y_vals, color="#091f40")
        
        ax.set_xlabel(xlabel, fontsize=12)
        ax.set_ylabel("Party Actors", fontsize=12)
        ax.set_title("Party Signatories", fontsize=14, fontweight='bold')

        # --- Add xlim for extra space on right side ---
        max_val = max(y_vals)
        ax.set_xlim(0, max_val * 1.15)  # add breathing room for labels

        # --- Data labels ---
        for bar in bars:
            width = bar.get_width()
            if mode == "percentage":
                label = f'{width:.0f}%' if width >= 1 else f'{width:.1f}%'
            else:
                label = f'{int(width)}'
            ax.text(width + max_val * 0.01, bar.get_y() + bar.get_height()/2,
                    label, ha='left', va='center', fontsize=9)
        
        plt.tight_layout(rect=[0, 0, 0.95, 1])
        return fig


    @render.plot
    def pp_party_signatories():
        return make_party_sigs_plot()


    def make_third_party_sigs_plot():
        sig_data = pp_signatories_data()
        third_party_data = sig_data["third_party"]
        
        if third_party_data.empty:
            fig, ax = plt.subplots(figsize=(14, 8))
            ax.text(0.5, 0.5, 'No third party signatory data available',
                    ha='center', va='center', transform=ax.transAxes)
            return fig
        
        # Sort and limit to top 15
        third_party_data = third_party_data.sort_values("count", ascending=True).tail(15)
        
        fig, ax = plt.subplots(figsize=(16, 8))
        plt.subplots_adjust(left=0.35, right=0.95)

        mode = input.pp_signatory_mode()
        if mode == "percentage":
            y_vals = third_party_data["percentage"]
            xlabel = "Percentage of Agreements"
        else:
            y_vals = third_party_data["count"]
            xlabel = "Number of Agreements"
        
        bars = ax.barh(third_party_data["actor_name"], y_vals, color="#df1f36")
        
        ax.set_xlabel(xlabel, fontsize=12)
        ax.set_ylabel("Third Party Actors", fontsize=12)
        ax.set_title("Third Party Signatories", fontsize=14, fontweight='bold')

        # --- Add xlim for extra space on right side ---
        max_val = max(y_vals)
        ax.set_xlim(0, max_val * 1.15)

        # --- Data labels ---
        for bar in bars:
            width = bar.get_width()
            if mode == "percentage":
                label = f'{width:.0f}%' if width >= 1 else f'{width:.1f}%'
            else:
                label = f'{int(width)}'
            ax.text(width + max_val * 0.01, bar.get_y() + bar.get_height()/2,
                    label, ha='left', va='center', fontsize=9)
        
        plt.tight_layout(rect=[0, 0, 0.95, 1])
        return fig


    @render.plot
    def pp_third_party_signatories():
        return make_third_party_sigs_plot()

        
    # --- UpSet (actor co-occurrence) ---
    def make_pp_upset_figure():
        data = filtered_pp_data()
        signatories = data["signatories"]

        fig_height = 8
        inactive_color = (0.75, 0.75, 0.75, 1.0)
        party_color = '#091f40'
        third_party_color = '#df1f36'

        if signatories.empty:
            fig, ax = plt.subplots(figsize=(15, fig_height))
            ax.text(0.5, 0.5, 'No signatory data available', ha='center', va='center', transform=ax.transAxes)
            ax.axis('off')
            return fig

        try:
            min_cooccurrence = input.pp_upset_min_cooccurrence()

            unique_combinations = signatories.drop_duplicates(['AgtId', 'actor_name'])
            actor_agreement_matrix = unique_combinations.pivot_table(
                index='AgtId',
                columns='actor_name',
                values='practical_third',
                aggfunc=lambda x: True,
                fill_value=False
            ).astype(bool)

            # keep only actors with >= min_cooccurrence agreements
            actor_counts = actor_agreement_matrix.sum()
            frequent_actors = actor_counts[actor_counts >= min_cooccurrence].index.tolist()

            if len(frequent_actors) < 2:
                fig, ax = plt.subplots(figsize=(15, fig_height))
                ax.text(
                    0.5, 0.5,
                    f'Insufficient data for UpSet plot\n(Need at least 2 actors with {min_cooccurrence}+ agreements)',
                    ha='center', va='center', transform=ax.transAxes
                )
                ax.axis('off')
                return fig

            # preserve this order in the UpSet rows
            actor_order = list(frequent_actors)
            actor_agreement_matrix = actor_agreement_matrix[actor_order]

            # actor type (party vs third party)
            actor_type_map = {}
            for actor in actor_order:
                is_third_party = signatories[signatories['actor_name'] == actor]['practical_third'].max() == 1
                actor_type_map[actor] = 'third_party' if is_third_party else 'party'

            # Build memberships for agreements that have 2+ actors
            from upsetplot import from_memberships, UpSet

            actor_lists = []
            for _, row in actor_agreement_matrix.iterrows():
                members = [a for a, present in row.items() if present]
                if len(members) > 1:
                    actor_lists.append(members)

            if len(actor_lists) == 0:
                fig, ax = plt.subplots(figsize=(15, fig_height))
                ax.text(0.5, 0.5, 'No agreements with multiple actors found', ha='center', va='center', transform=ax.transAxes)
                ax.axis('off')
                return fig

            upset_series = from_memberships(actor_lists)

            # Ensure UpSet uses exactly our row (category) order and keeps subset order
            try:
                upset_series = upset_series.reorder_levels(actor_order)
            except Exception:
                pass

            # IMPORTANT: keep both subset and category orders stable so our (x,y) mapping matches
            upset = UpSet(
                upset_series,
                subset_size='count',
                show_counts=True,
                sort_by=None,              # do not reorder subsets (x)
                sort_categories_by=None    # do not reorder categories/sets (y)
            )
            upset.plot()
            fig = plt.gcf()

            # ----- find the axis with the actor y tick labels to map y -> actor index
            actor_axis = None
            for ax in fig.axes:
                labels = [lab.get_text() for lab in ax.get_yticklabels()]
                if labels and set(actor_order).intersection(labels):
                    actor_axis = ax
                    break

            if actor_axis is not None:
                ytick_labels = actor_axis.get_yticklabels()
                ytick_positions = actor_axis.get_yticks().tolist()

                # color the membership matrix dots: only color real memberships, keep non-members grey
                for ax in fig.axes:
                    for coll in getattr(ax, "collections", []):
                        offsets = getattr(coll, "get_offsets", lambda: None)()
                        if offsets is None or len(offsets) == 0:
                            continue

                        colors = []
                        for (x, y) in offsets:
                            # map y to the nearest actor row index
                            if not ytick_positions:
                                colors.append(inactive_color)
                                continue

                            idx = int(np.argmin([abs(y - yp) for yp in ytick_positions]))

                            # map x (subset column) to integer safely (UpSet uses discrete integer col positions)
                            x_int = int(round(x))
                            cell_active = False
                            if 0 <= x_int < len(upset_series.index):
                                try:
                                    # upset_series.index[x_int] is a tuple of booleans (one per actor in actor_order)
                                    cell_active = bool(upset_series.index[x_int][idx])
                                except Exception:
                                    cell_active = False

                            if not cell_active:
                                colors.append(inactive_color)
                            else:
                                actor_name = ytick_labels[idx].get_text()
                                if actor_type_map.get(actor_name) == 'third_party':
                                    colors.append(third_party_color)
                                else:
                                    colors.append(party_color)

                        try:
                            coll.set_facecolor(colors)
                            coll.set_edgecolor(colors)
                        except Exception:
                            # some collections (e.g. lines) won't accept facecolor; ignore
                            pass

            # ----- Title and legend
            from matplotlib.patches import Patch
            legend_elements = [
                Patch(facecolor=party_color, label='Party Actors'),
                Patch(facecolor=third_party_color, label='Third Party Actors'),
                Patch(facecolor=inactive_color, label='No membership')
            ]

            # Put the legend above the plot so it doesn't overlap
            fig.legend(
                handles=legend_elements,
                loc='upper center',
                bbox_to_anchor=(0.5, 0.985),
                ncol=3,
                frameon=False,
                fontsize=10
            )

            fig.suptitle(
                f'Actor Co-occurrence Analysis\n(Minimum {min_cooccurrence} agreement{"s" if min_cooccurrence != 1 else ""} per actor)',
                fontsize=14, fontweight='bold', y=0.955
            )

            # ----- Layout: give more room for long y labels, scale width/height sensibly
            max_label_len = max(len(str(n)) for n in actor_order) if actor_order else 10
            left_pad = min(0.60, 0.22 + max_label_len * 0.010)  # dynamic left margin
            right_pad = 0.88
            top_pad = 0.90     # leave space for legend and title
            bottom_pad = 0.12

            # scale figure size by actors (rows) and number of subsets (columns)
            n_sets = len(actor_order)
            n_subsets = len(upset_series.index)
            width = min(24, max(12, 0.030 * n_subsets + 10))
            height = min(14, max(7, 0.40 * (n_sets if n_sets > 0 else 10)))

            fig.set_size_inches(width, height)
            plt.tight_layout()
            plt.subplots_adjust(left=left_pad, right=right_pad, top=top_pad, bottom=bottom_pad)

            return fig

        except Exception as e:
            fig, ax = plt.subplots(figsize=(15, fig_height))
            ax.text(0.5, 0.5, f'Error creating UpSet plot:\n{str(e)}',
                    ha='center', va='center', transform=ax.transAxes, fontsize=10)
            ax.axis('off')
            return fig


    @render.plot
    def pp_upset_plot():
        return make_pp_upset_figure()

    
    @render.plot
    def pp_upset_plot():
        return make_pp_upset_figure()

    
    # UPDATED: Topics analysis with categories and sub-issues
    @reactive.calc
    def pp_topics_category_data():
        data = filtered_pp_data()
        topics = data["pax_topics"]
        
        if topics.empty:
            return pd.DataFrame()
        
        # Filter for topics with value > 0
        topics_filtered = topics[topics['value'] > 0]
        
        # Count UNIQUE agreements per topic category
        topic_counts = topics_filtered.groupby('category')['AgtId'].nunique().reset_index(name='count')
        
        return topic_counts
    
    @reactive.calc
    def pp_topics_subissue_data():
        data = filtered_pp_data()
        topics = data["pax_topics"]
        
        if topics.empty:
            return pd.DataFrame()
        
        # Filter for topics with value > 0 and valid sub-issues
        topics_filtered = topics[
            (topics['value'] > 0) & 
            (topics['subissue_label'].notna()) & 
            (topics['subissue_label'] != '')
        ]
        
        # Count UNIQUE agreements per sub-issue and include category for coloring
        subissue_counts = topics_filtered.groupby(['subissue_label', 'category'])['AgtId'].nunique().reset_index(name='count')
        
        return subissue_counts

    @reactive.calc
    def pp_topics_issue_data():
        data = filtered_pp_data()
        topics = data["pax_topics"]
        
        if topics.empty:
            return pd.DataFrame()
        
        # Filter for topics with value > 0 and valid issues
        topics_filtered = topics[
            (topics['value'] > 0) & 
            (topics['issue_label'].notna()) & 
            (topics['issue_label'] != '')
        ]
        
        # Get all issues (no limit)
        issue_counts = topics_filtered.groupby(['issue_label', 'category'])['AgtId'].nunique().reset_index(name='count')
        
        return issue_counts
    
    @render.plot
    def pp_topics_categories_chart():
        topics_data = pp_topics_category_data()
        
        if topics_data.empty:
            fig, ax = plt.subplots(figsize=(12, 8))
            ax.text(0.5, 0.5, 'No topic categories data available', 
                   ha='center', va='center', transform=ax.transAxes)
            return fig
        
        chart_type = input.pp_topic_chart_type()
        
        if chart_type == "bar":
            fig, ax = plt.subplots(figsize=(14, 8))
            topics_sorted = topics_data.sort_values('count', ascending=True)
            bars = ax.barh(topics_sorted['category'], topics_sorted['count'], color='#091f40')
            ax.set_xlabel('Number of Agreements', fontsize=12)
            ax.set_ylabel('Topic Category', fontsize=12)
            ax.set_title('Topic Categories in Peace Process', fontsize=14, fontweight='bold')
            
            # Add value labels
            for bar in bars:
                width = bar.get_width()
                ax.text(width + max(topics_sorted['count']) * 0.01, 
                       bar.get_y() + bar.get_height()/2, 
                       f'{int(width)}', ha='left', va='center', fontsize=9)
            
        elif chart_type == "pie":
            fig, ax = plt.subplots(figsize=(12, 8))
            colors = plt.cm.Set3(np.linspace(0, 1, len(topics_data)))
            wedges, texts, autotexts = ax.pie(topics_data['count'], labels=topics_data['category'], 
                                             autopct='%1.1f%%', colors=colors)
            ax.set_title('Topic Categories Distribution', fontsize=14, fontweight='bold')
            
        elif chart_type == "radar":
            fig, ax = plt.subplots(figsize=(10, 8), subplot_kw=dict(projection='polar'))
            
            # Normalize data for radar chart
            topics_data['normalized'] = topics_data['count'] / topics_data['count'].max()
            
            # Calculate angles
            angles = np.linspace(0, 2 * np.pi, len(topics_data), endpoint=False)
            
            # Close the plot
            values = topics_data['normalized'].tolist()
            values += values[:1]
            angles = np.concatenate((angles, [angles[0]]))
            
            ax.plot(angles, values, 'o-', linewidth=2, color='#091f40')
            ax.fill(angles, values, alpha=0.25, color='#091f40')
            
            # Add labels
            ax.set_xticks(angles[:-1])
            ax.set_xticklabels(topics_data['category'], fontsize=10)
            ax.set_title('Topic Categories Radar Chart', fontsize=14, fontweight='bold', pad=20)
            
            # Set y-axis limits
            ax.set_ylim(0, 1)
        
        plt.tight_layout()
        return fig
    
    def make_pp_topics_issues_figure():
        issue_data = pp_topics_issue_data()

        if issue_data.empty:
            fig, ax = plt.subplots(figsize=(14, 12))
            ax.text(
                0.5, 0.5, "No issue data available",
                ha="center", va="center", transform=ax.transAxes
            )
            return fig

        # Sort by count
        issue_sorted = issue_data.sort_values("count", ascending=True)
        fig_height = min(12, max(6, len(issue_sorted) * 0.35))
        fig, ax = plt.subplots(figsize=(14, fig_height))

        # === Show stage breakdown if enabled ===
        if input.pp_topics_show_stage_legend():
            pax_df = filtered_pp_data()["pax"]
            topics_df = filtered_pp_data()["pax_topics"]

            if not pax_df.empty and not topics_df.empty:
                issue_stage_data = []
                for _, issue_row in issue_sorted.iterrows():
                    issue_name = issue_row["issue_label"]
                    issue_agreements = topics_df[
                        (topics_df["issue_label"] == issue_name)
                        & (topics_df["value"] > 0)
                    ]["AgtId"].unique()
                    issue_pax = pax_df[pax_df["AgtId"].isin(issue_agreements)]
                    stage_counts = issue_pax["stage_label"].value_counts()

                    for stage in stage_order:
                        issue_stage_data.append({
                            "issue_label": issue_name,
                            "stage_label": stage,
                            "count": stage_counts.get(stage, 0),
                        })

                stage_df = pd.DataFrame(issue_stage_data)
                stage_pivot = stage_df.pivot(
                    index="issue_label", columns="stage_label", values="count"
                ).fillna(0)
                available_stages = [s for s in stage_order if s in stage_pivot.columns]
                stage_pivot = stage_pivot[available_stages]
                stage_pivot = stage_pivot.reindex(issue_sorted["issue_label"])

                colors = [stage_color_map.get(s, "#cccccc") for s in stage_pivot.columns]
                stage_pivot.plot(kind="barh", stacked=True, ax=ax, color=colors, width=0.8)

                # Labels on segments (>0 only)
                if input.pp_show_labels():
                    for container in ax.containers:
                        for bar in container:
                            w = bar.get_width()
                            if w > 0:
                                ax.text(
                                    bar.get_x() + w / 2,
                                    bar.get_y() + bar.get_height() / 2,
                                    f"{int(w)}",
                                    ha="center", va="center",
                                    fontsize=8, color="white",
                                )

                    totals = stage_pivot.sum(axis=1)
                    for i, total in enumerate(totals):
                        if total > 0:
                            ax.text(
                                total + (totals.max() * 0.01),
                                i,
                                f"{int(total)}",
                                ha="left", va="center",
                                fontsize=9, fontweight="bold", color="#333333",
                            )

                # Legend styling to match “Stage Over Time”
                ncol = len(stage_pivot.columns) if len(stage_pivot.columns) <= 4 else 4
                ax.legend(
                    title="Stage",
                    bbox_to_anchor=(0.5, 1.02),
                    loc="lower center",
                    ncol=ncol,
                    fontsize=10,
                )
        else:
            # === Standard navy bars (no breakdown) ===
            bars = ax.barh(issue_sorted["issue_label"], issue_sorted["count"], color="#091f40")

            if input.pp_show_labels():
                for bar in bars:
                    width = bar.get_width()
                    if width > 0:
                        ax.text(
                            width + max(issue_sorted["count"]) * 0.01,
                            bar.get_y() + bar.get_height() / 2,
                            f"{int(width)}",
                            ha="left", va="center", fontsize=9,
                        )

        # === Common styling ===
        ax.set_xlabel("Number of Agreements", fontsize=12)
        ax.set_ylabel("Issue", fontsize=12)
        ax.margins(y=0.02)

        # Dynamic title placement (to clear legend)
        if input.pp_topics_show_stage_legend():
            ax.set_title(
                "Issues in Peace Process",
                fontsize=14,
                fontweight="bold",
                pad=20,
                y=1.08,
            )
        else:
            ax.set_title(
                "Issues in Peace Process",
                fontsize=14,
                fontweight="bold",
                pad=12,
                y=1.02,
            )

        plt.tight_layout()
        return fig

    @render.plot
    def pp_topics_issues_chart():
        return make_pp_topics_issues_figure()
        
    # -------------------------------------------------------------------------
    # DIFFUSION ANALYSIS — Actors or Topics appearing over time
    # -------------------------------------------------------------------------

    @reactive.calc
    def pp_diffusion_data():
        """Prepare diffusion data for actors and topics, respecting radio button selections."""
        data = filtered_pp_data()
        pax_df = data["pax"]

        if pax_df.empty:
            return {"agreements": [], "actors": [], "topics": []}

        # Sort agreements by date
        pax_sorted = pax_df.copy()
        pax_sorted["date"] = pd.to_datetime(pax_sorted["Dat"], errors="coerce", dayfirst=True)
        pax_sorted = pax_sorted.dropna(subset=["date"]).sort_values("date")

        agreements = pax_sorted[["AgtId", "Agt", "date", "stage_label"]].to_dict("records")

        # === ACTORS ===
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
                            "actor_type": "third_party"
                            if sig["practical_third"] == 1
                            else "party",
                            "date": agt["date"],
                        }
                    )

        # === TOPICS ===
        topics_data = []
        topics_df = data["pax_topics"]
        if not topics_df.empty:
            # Use new radio button input
            diffusion_topic_level = input.pp_diffusion_topic_level() or "issues"

            if diffusion_topic_level == "subissues":
                topics_filtered = topics_df[
                    (topics_df["value"] > 0)
                    & (topics_df["subissue_label"].notna())
                    & (topics_df["subissue_label"] != "")
                    & (topics_df["issue_label"].notna())
                    & (topics_df["issue_label"] != "")
                ]
                for _, agt in pax_sorted.iterrows():
                    agt_topics = topics_filtered[
                        topics_filtered["AgtId"] == agt["AgtId"]
                    ]
                    for _, topic in agt_topics.iterrows():
                        combined_name = (
                            f"{topic['issue_label']} > {topic['subissue_label']}"
                        )
                        topics_data.append(
                            {
                                "AgtId": agt["AgtId"],
                                "topic_label": combined_name,
                                "category": topic["category"],
                                "date": agt["date"],
                            }
                        )
            else:
                topics_filtered = topics_df[
                    (topics_df["value"] > 0)
                    & (topics_df["issue_label"].notna())
                    & (topics_df["issue_label"] != "")
                ]
                for _, agt in pax_sorted.iterrows():
                    agt_topics = topics_filtered[
                        topics_filtered["AgtId"] == agt["AgtId"]
                    ]
                    for _, topic in agt_topics.iterrows():
                        topics_data.append(
                            {
                                "AgtId": agt["AgtId"],
                                "topic_label": topic["issue_label"],
                                "category": topic["category"],
                                "date": agt["date"],
                            }
                        )

        return {"agreements": agreements, "actors": actors_data, "topics": topics_data}



    def make_pp_diffusion_figure():
        """Build the diffusion chart depending on user selections."""
        diffusion_type = input.pp_diffusion_type() or "actors"          # 'actors' or 'topics'
        diffusion_topic_level = input.pp_diffusion_topic_level() or "issues"  # 'issues' or 'subissues'
        x_axis_mode = input.pp_diffusion_x_axis_mode() or "order"       # 'order' or 'date'

        diffusion_data = pp_diffusion_data()
        agreements = diffusion_data["agreements"]

        fig, ax = plt.subplots(figsize=(20, 12))

        if not agreements:
            ax.text(
                0.5, 0.5, "No data available for diffusion chart",
                ha="center", va="center", transform=ax.transAxes,
            )
            return fig

        # === ACTOR MODE ===
        if diffusion_type == "actors":
            actors_data = diffusion_data["actors"]
            if not actors_data:
                ax.text(
                    0.5, 0.5, "No actor data available",
                    ha="center", va="center", transform=ax.transAxes,
                )
                return fig

            actors_df = pd.DataFrame(actors_data)
            actor_first_appearance = (
                actors_df.groupby("actor_name")["date"].min().sort_values(ascending=False)
            )
            sorted_actors = actor_first_appearance.index.tolist()
            agreement_ids = [a["AgtId"] for a in agreements]

            for i, actor in enumerate(sorted_actors):
                actor_agreements = actors_df[
                    actors_df["actor_name"] == actor
                ]["AgtId"].tolist()
                x_positions = [
                    j for j, agt_id in enumerate(agreement_ids) if agt_id in actor_agreements
                ]
                y_positions = [i] * len(x_positions)
                actor_type = actors_df[
                    actors_df["actor_name"] == actor
                ]["actor_type"].iloc[0]
                color = "#df1f36" if actor_type == "third_party" else "#091f40"
                if x_positions:
                    ax.scatter(x_positions, y_positions, alpha=0.9, s=20, color=color)
                    ax.plot(x_positions, y_positions, alpha=0.7, linewidth=1, color=color)

            ax.set_yticks(range(len(sorted_actors)))
            ax.set_yticklabels(sorted_actors, fontsize=10)
            ax.set_ylabel("Actors (in order of first appearance)", fontsize=12)
            ax.set_title(
                f"{diffusion_type.capitalize()} Diffusion Over Time",
                fontsize=16, fontweight="bold", y=1.05,
            )

            from matplotlib.patches import Patch
            legend_elements = [
                Patch(facecolor="#091f40", label="Party Actors"),
                Patch(facecolor="#df1f36", label="Third Party Actors"),
            ]
            ax.legend(
                handles=legend_elements,
                bbox_to_anchor=(0.5, 1),
                loc="lower center",
                ncol=2,
                fontsize=12,
            )
           

        # === TOPIC MODE ===
        else:
            topics_data = diffusion_data["topics"]
            if not topics_data:
                ax.text(
                    0.5, 0.5, "No topic data available",
                    ha="center", va="center", transform=ax.transAxes,
                )
                return fig

            topics_df = pd.DataFrame(topics_data)
            topic_first_appearance = (
                topics_df.groupby("topic_label")["date"].min().sort_values(ascending=True)
            )
            sorted_topics = topic_first_appearance.index.tolist()

            if len(sorted_topics) > 30:
                topic_counts = topics_df["topic_label"].value_counts()
                sorted_topics = topic_counts.head(30).index.tolist()
                sorted_topics.sort(
                    key=lambda x: topic_first_appearance.get(x, pd.Timestamp.max)
                )

            agreement_ids = [a["AgtId"] for a in agreements]
            topic_categories = []
            for i, topic in enumerate(sorted_topics):
                topic_agreements = topics_df[
                    topics_df["topic_label"] == topic
                ]["AgtId"].tolist()
                topic_category = topics_df[
                    topics_df["topic_label"] == topic
                ]["category"].iloc[0]
                topic_categories.append(topic_category)
                x_positions = [
                    j for j, agt_id in enumerate(agreement_ids) if agt_id in topic_agreements
                ]
                y_positions = [i] * len(x_positions)
                unique_categories = list(set(topic_categories))
                # --- Define color-blind friendly palette (Okabe–Ito) ---
                okabe_ito_colors = [
                    "#E69F00",  # orange
                    "#56B4E9",  # sky blue
                    "#009E73",  # bluish green
                    "#F0E442",  # yellow
                    "#0072B2",  # blue
                    "#D55E00",  # vermilion
                    "#CC79A7",  # reddish purple
                    "#999999",  # grey (optional extra)
                ]

                # Cycle or repeat if more categories than colors
                category_colors = [okabe_ito_colors[i % len(okabe_ito_colors)] for i in range(len(unique_categories))]
                color_map = dict(zip(unique_categories, category_colors))
                color = color_map[topic_category]
                if x_positions:
                    ax.scatter(x_positions, y_positions, alpha=0.9, s=20, color=color)
                    ax.plot(x_positions, y_positions, alpha=0.7, linewidth=1, color=color)

            ax.set_yticks(range(len(sorted_topics)))
            ax.set_yticklabels(sorted_topics, fontsize=9)
            ylabel = (
                "Issues (in order of first appearance)"
                if diffusion_topic_level == "issues"
                else "Sub-issues (in order of first appearance)"
            )
            ax.set_ylabel(ylabel, fontsize=12)
            ax.set_title(
                f"{diffusion_type.capitalize()} Diffusion Over Time",
                fontsize=16, fontweight="bold", y=1.15,
            )

            unique_categories = list(set(topic_categories))
            category_colors = plt.cm.Set3(np.linspace(0, 1, len(unique_categories)))
            color_map = dict(zip(unique_categories, category_colors))
            legend_elements = [
                plt.Line2D(
                    [0], [0],
                    marker="o", color="w",
                    markerfacecolor=color_map[cat],
                    markersize=8, label=cat,
                )
                for cat in unique_categories
            ]
            ax.legend(
                handles=legend_elements,
                title="Topic Category",
                bbox_to_anchor=(0.5, 1),
                loc="lower center",
                ncol=5,
                fontsize=11,
            )
            

        # === X-AXIS (date or order) ===
        if x_axis_mode == "date":
            dates = [a["date"] for a in agreements]
            if len(dates) > 1:
                date_range = pd.date_range(start=min(dates), end=max(dates), freq="MS")
                idx_map = {}
                for i, agt_date in enumerate(dates):
                    closest_month = min(date_range, key=lambda x: abs((x - agt_date).days))
                    month_pos = list(date_range).index(closest_month)
                    idx_map[i] = month_pos

                for line in ax.lines:
                    x_data = line.get_xdata()
                    new_x_data = [idx_map.get(int(x), x) for x in x_data]
                    line.set_xdata(new_x_data)
                for coll in ax.collections:
                    offsets = coll.get_offsets()
                    if len(offsets) > 0:
                        new_offsets = [(idx_map.get(int(x), x), y) for x, y in offsets]
                        coll.set_offsets(new_offsets)

                step = max(1, len(date_range) // 12)
                tick_positions = list(range(0, len(date_range), step))
                tick_labels = [date_range[i].strftime("%Y-%m") for i in tick_positions]
                ax.set_xticks(tick_positions)
                ax.set_xticklabels(tick_labels, rotation=45, fontsize=8)
                ax.set_xlabel("Agreement Date", fontsize=12)
            else:
                ax.set_xlabel("Agreement Date", fontsize=12)
        else:
            agt_names = [
                a["Agt"][:50] + "..." if len(a["Agt"]) > 50 else a["Agt"] for a in agreements
            ]
            ax.set_xticks(range(len(agt_names)))
            ax.set_xticklabels(agt_names, rotation=90, fontsize=8)
            ax.set_xlabel("Agreements in Time Order", fontsize=12)

        
        ax.grid(alpha=0.2)
        # === Add padding to x-axis for better spacing ===
        xmin, xmax = ax.get_xlim()
        x_padding = (xmax - xmin) * 0.02  # 2% of range as padding
        ax.set_xlim(xmin - x_padding, xmax + x_padding)
        plt.tight_layout()
        return fig



    @render.plot
    def pp_diffusion_chart():
        """Render diffusion chart (actors or topics over time)."""
        return make_pp_diffusion_figure()

    # # ADDED: Peace Process Similarity Feature
    # @reactive.calc
    # def similar_processes():
    #     selected_pp = input.selected_peace_process()
    #     if not selected_pp:
    #         return []
        
    #     data = load_data()
    #     if data is None:
    #         return []
        
    #     # Simple topic-based similarity
    #     target_agreements = filtered_pp_data()["pax"]["AgtId"].unique()
    #     target_topics = data["pax_topics"][
    #         (data["pax_topics"]["AgtId"].isin(target_agreements)) & 
    #         (data["pax_topics"]["value"] > 0)
    #     ]
    #     target_topic_set = set(target_topics["category"].unique())
        
    #     if not target_topic_set:
    #         return []
        
    #     similarities = []
    #     for other_pp in data["pax"]["PPName"].dropna().unique():
    #         if other_pp == selected_pp:
    #             continue
                
    #         other_agreements = data["pax"][data["pax"]["PPName"] == other_pp]["AgtId"].unique()
    #         other_topics = data["pax_topics"][
    #             (data["pax_topics"]["AgtId"].isin(other_agreements)) & 
    #             (data["pax_topics"]["value"] > 0)
    #         ]
    #         other_topic_set = set(other_topics["category"].unique())
            
    #         if not other_topic_set:
    #             continue
                
    #         # Jaccard similarity
    #         intersection = len(target_topic_set & other_topic_set)
    #         union = len(target_topic_set | other_topic_set)
    #         similarity = intersection / union if union > 0 else 0
            
    #         if similarity > 0.1:  # Only show if >10% similar
    #             similarities.append({
    #                 'process': other_pp,
    #                 'similarity': similarity,
    #                 'common_topics': list(target_topic_set & other_topic_set)[:3]
    #             })
        
    #     return sorted(similarities, key=lambda x: x['similarity'], reverse=True)[:3]

    # @render.ui
    # def pp_similar_processes():
    #     similar = similar_processes()
        
    #     if not similar:
    #         return ui.div(
    #             ui.p("No similar processes found", class_="text-muted"),
    #             style="padding: 10px;"
    #         )
        
    #     items = []
    #     for sim in similar:
    #         items.append(
    #             ui.div(
    #                 ui.strong(sim['process']),
    #                 ui.br(),
    #                 ui.small(f"{sim['similarity']*100:.0f}% similar", class_="text-muted"),
    #                 ui.br(),
    #                 ui.small(f"Common topics: {', '.join(sim['common_topics'])}", class_="text-info"),
    #                 class_="mb-2 p-2 border-start border-primary border-3",
    #                 style="background-color: #f8f9fa;"
    #             )
    #         )
        
    #     return ui.div(
    #         ui.h6("Similar Processes", class_="text-primary mb-3"),
    #         *items
    #     )

    #===========================
    # EXPORTS
    #===========================
    
    # Export functions - Updated for new structure
    @output
    @render.download(filename="pp_agreements_time.png")
    def pp_export_time_png():
        return export_with_branding(
            make_pp_agreements_over_time_figure,
            filter_text_fn=get_filter_text_for_png,
            data_version_fn=get_data_version,
            load_data_fn=load_data,
            filter_text_position=(0.5, 0.0025),
        )


    @output
    @render.download(filename="pp_agreements_time.csv")
    def pp_export_time_csv():
        try:
            df = pp_agreements_time_data()
            csv_string = df.to_csv(index=False)
            return io.BytesIO(csv_string.encode('utf-8'))
        except Exception as e:
            print(f"Error in CSV export: {e}")
            return io.BytesIO(b"Error,Message\nExport Failed,Please try again")
    
    #stage exports
    @output
    @render.download(filename="pp_stage_analysis.png")
    def pp_export_stage_png():
        return export_with_branding(
            make_stage_plot,
            filter_text_fn=get_filter_text_for_png,
            data_version_fn=get_data_version,
            load_data_fn=load_data,
            filter_text_position=(0.5, 0.98)
        )

    @output
    @render.download(filename="pp_stage_analysis.csv")
    def pp_export_stage_csv():
        try:
            df = pp_stage_analysis_data()
            csv_string = df.to_csv(index=False)
            return io.BytesIO(csv_string.encode('utf-8'))
        except Exception as e:
            return io.BytesIO(b"Error,Message\nExport Failed,Please try again")

    
    # Signatories exports - Updated for consistent button styling
    @output
    @render.download(filename="pp_party_signatories.png")
    def pp_export_party_sig_png():
        return export_with_branding(
            make_party_sigs_plot,
            filter_text_fn=get_filter_text_for_png,
            data_version_fn=get_data_version,
            load_data_fn=load_data,
            logo_position=(0.98, 0.98, 0.075, 0.075),
            filter_text_position=(0.5, 1.02),
            version_position=(0.98, 0.015),
        )
        
    @output
    @render.download(filename="pp_third_party_signatories.png")
    def pp_export_third_party_sig_png():
        return export_with_branding(
            make_third_party_sigs_plot,
            filter_text_fn=get_filter_text_for_png,
            data_version_fn=get_data_version,
            load_data_fn=load_data,
            filter_text_position=(0.5, 1.02),
            logo_position=(0.98, 0.98, 0.075, 0.075),
            version_position=(0.98, 0.015),
        )
        

    @output
    @render.download(filename="pp_signatories.csv")
    def pp_export_sig_csv():
        try:
            sig_data = pp_signatories_data()
            # Combine party and third party data
            party_df = sig_data["party"].copy()
            third_party_df = sig_data["third_party"].copy()
            
            if not party_df.empty:
                party_df["signatory_type"] = "party"
            if not third_party_df.empty:
                third_party_df["signatory_type"] = "third_party"
            
            combined_df = pd.concat([party_df, third_party_df], ignore_index=True)
            csv_string = combined_df.to_csv(index=False)
            return io.BytesIO(csv_string.encode('utf-8'))
        except Exception as e:
            print(f"Error in CSV export: {e}")
            return io.BytesIO(b"Error,Message\nExport Failed,Please try again")
    
    #third party signatories csv export   
    @output
    @render.download(filename="pp_third_party_signatories.csv")
    def pp_export_third_party_sig_csv():
        try:
            sig_data = pp_signatories_data()
            third_party_df = sig_data["third_party"].copy()
            
            if not third_party_df.empty:
                third_party_df["signatory_type"] = "third_party"
            
            csv_string = third_party_df.to_csv(index=False)
            return io.BytesIO(csv_string.encode('utf-8'))
        except Exception as e:
            return io.BytesIO(b"Error,Message\nExport Failed,Please try again")

    # Topics exports - Updated for new structure
    @output
    @render.download(filename="pp_topic_categories.csv")
    def pp_export_topic_categories_csv():
        try:
            df = pp_topics_category_data()
            csv_string = df.to_csv(index=False)
            return io.BytesIO(csv_string.encode('utf-8'))
        except Exception as e:
            print(f"Error in CSV export: {e}")
            return io.BytesIO(b"Error,Message\nExport Failed,Please try again")

    @output
    @render.download(filename="pp_topic_subissues.csv")
    def pp_export_topic_subissues_csv():
        try:
            df = pp_topics_subissue_data()
            csv_string = df.to_csv(index=False)
            return io.BytesIO(csv_string.encode('utf-8'))
        except Exception as e:
            print(f"Error in CSV export: {e}")
            return io.BytesIO(b"Error,Message\nExport Failed,Please try again")


    @output
    @render.download(filename="pp_topic_issues.csv")
    def pp_export_topic_issues_csv():
        try:
            df = pp_topics_issue_data()
            csv_string = df.to_csv(index=False)
            return io.BytesIO(csv_string.encode('utf-8'))
        except Exception as e:
            return io.BytesIO(b"Error,Message\nExport Failed,Please try again")

    @output
    @render.download(filename="pp_topic_issues.png")
    def pp_export_topic_issues_png():
        return export_with_branding(
            make_pp_topics_issues_figure,
            filter_text_fn=get_filter_text_for_png,
            data_version_fn=get_data_version,
            load_data_fn=load_data,
            # Optional per-chart branding overrides:
            logo_position=(0.97, 0.97, 0.075, 0.075),
            filter_text_position=(0.1, 0.00375),
            version_position=(0.99, 0.00375),
        )

    
    
    # UpSet exports - Updated for consistent styling
    @output
    @render.download(filename="pp_upset.csv")
    def pp_export_upset_csv():
        try:
            data = filtered_pp_data()
            signatories = data["signatories"]
            
            if signatories.empty:
                return io.BytesIO(b"No signatory data available")
            
            # Export the actor-agreement relationships
            unique_actor_agreements = signatories.drop_duplicates(['AgtId', 'actor_name'])
            export_data = unique_actor_agreements[['AgtId', 'actor_name']].copy()
            csv_string = export_data.to_csv(index=False)
            return io.BytesIO(csv_string.encode('utf-8'))
        except Exception as e:
            print(f"Error in CSV export: {e}")
            return io.BytesIO(b"Error,Message\nExport Failed,Please try again")

    @output
    @render.download(filename="pp_upset.png")
    def pp_export_upset_png():
        return export_with_branding(
            make_pp_upset_figure,
            filter_text_fn=get_filter_text_for_png,
            data_version_fn=get_data_version,
            load_data_fn=load_data,
            logo_position=(0.99, 0.99, 0.075, 0.075),
            filter_text_position=(0.1, 0.0035),
            version_position=(0.98, 0.015),
        )

    # Diffusion chart exports
    @output
    @render.download(filename="pp_diffusion_chart.png")
    def pp_export_diffusion_png():
        return export_with_branding(
            make_pp_diffusion_figure,
            filter_text_fn=get_filter_text_for_png,
            data_version_fn=get_data_version,
            load_data_fn=load_data,
            filter_text_position=(0.1, 0.0035),
            version_position=(0.99, 0.0035),
        )

    @output
    @render.download(filename="pp_diffusion_data.csv")
    def pp_export_diffusion_csv():
        try:
            diffusion_data = pp_diffusion_data()
            diffusion_type = input.pp_diffusion_type()
            
            if diffusion_type == "actors":
                df = pd.DataFrame(diffusion_data["actors"])
            else:
                df = pd.DataFrame(diffusion_data["topics"])
            
            csv_string = df.to_csv(index=False)
            return io.BytesIO(csv_string.encode('utf-8'))
        except Exception as e:
            print(f"Error in CSV export: {e}")
            return io.BytesIO(b"Error,Message\nExport Failed,Please try again")
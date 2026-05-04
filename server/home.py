# Complete fixed server/home.py code

import io
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from shiny import reactive, render, ui
from utils.export_handlers import make_png_download, make_csv_download
import matplotlib.font_manager as fm

from utils.data_loader import load_pax_data

data = load_pax_data()
pax = data["pax"]
pax_id_to_con = data["pax_id_to_con"]
pax_topics = data["pax_topics"]


#DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# Load data
# pax = pd.read_csv(DATA_DIR / "pax.csv")
# pax_id_to_con = pd.read_csv(DATA_DIR / "pax_id_to_con_info.csv")
# pax_topics = pd.read_csv(DATA_DIR / "all_pax_topics_no_imp.csv")

# Define stage order
stage_order = [
    'Pre-negotiation/process', 'Ceasefire', 'Framework-substantive, partial',
    'Framework-substantive, comprehensive', 'Implementation', 'Renewal', 'Other'
]

# Color maps for different groupings
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
    'Intrastate': '#0b5740',
    'Local': '#ac4399',
    'Interstate/mixed': '#df1f36',
    'Interstate': '#f28b20'
}

def server(input, output, session):
    input.show_labels = reactive.value(True)
    # Helper function to get colors for grouping
    def get_colors_for_grouping(group_mode, categories):
        if group_mode == "Stage":
            return [stage_color_map.get(cat, '#cccccc') for cat in categories]
        else:  # Agreement Type
            return [type_color_map.get(cat, '#cccccc') for cat in categories]

    # Filter choices calculations
    @reactive.calc
    def country_choices():
        return sorted(pax_id_to_con["name"].dropna().unique().tolist())

    @reactive.calc  
    def agt_type_choices():
        return sorted(pax["agt_type"].dropna().unique().tolist())
    
    @reactive.calc
    def region_choices():
        return sorted(pax["Reg"].dropna().unique().tolist())
    
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

    # Populate all dropdowns dynamically
    @reactive.effect
    def _():
        countries = country_choices()
        agt_types = agt_type_choices()
        regions = region_choices()
        peace_processes = peace_process_choices()
        stages = stage_choices()
        year_min, year_max = year_range()

        if input.exclude_local_analysis():
            agt_types = [t for t in agt_types if t != "Local"]

        with reactive.isolate():
            selected_country = input.country() or []
            if isinstance(selected_country, str):
                selected_country = [selected_country]
            selected_country = [x for x in selected_country if x in countries]

            selected_agt_type = input.agt_type() or []
            if isinstance(selected_agt_type, str):
                selected_agt_type = [selected_agt_type]
            selected_agt_type = [x for x in selected_agt_type if x in agt_types]

            selected_region = input.region() or []
            if isinstance(selected_region, str):
                selected_region = [selected_region]
            selected_region = [x for x in selected_region if x in regions]

            selected_peace_process = input.peace_process() or []
            if isinstance(selected_peace_process, str):
                selected_peace_process = [selected_peace_process]
            selected_peace_process = [x for x in selected_peace_process if x in peace_processes]

            selected_stage = input.stage() or []
            if isinstance(selected_stage, str):
                selected_stage = [selected_stage]
            selected_stage = [x for x in selected_stage if x in stages]

            current_year_range = input.year_range() or [year_min, year_max]
            current_year_range = [
                max(year_min, current_year_range[0]),
                min(year_max, current_year_range[1]),
            ]

        ui.update_selectize("country", choices=countries, selected=selected_country)
        ui.update_selectize("agt_type", choices=agt_types, selected=selected_agt_type)
        ui.update_selectize("region", choices=regions, selected=selected_region)
        ui.update_selectize("peace_process", choices=peace_processes, selected=selected_peace_process)
        ui.update_selectize("stage", choices=stages, selected=selected_stage)
        ui.update_slider("year_range", min=year_min, max=year_max, value=current_year_range)

    # Enhanced filtered_data function
    @reactive.calc
    def filtered_data():
        df = pax.copy()
        
        # Filter by country
        selected_countries = input.country()
        if selected_countries and len(selected_countries) > 0:
            if isinstance(selected_countries, str):
                selected_countries = [selected_countries]
            agt_ids = pax_id_to_con[pax_id_to_con["name"].isin(selected_countries)]["AgtId"].unique()
            df = df[df["AgtId"].isin(agt_ids)]
        
        # Filter by agreement type
        selected_types = input.agt_type()
        if selected_types and len(selected_types) > 0:
            if isinstance(selected_types, str):
                selected_types = [selected_types]
            df = df[df["agt_type"].isin(selected_types)]
        
        if input.exclude_local_analysis():
            df = df[df["agt_type"] != "Local"]
        
        # Filter by year range
        year_range_vals = input.year_range()
        if year_range_vals and len(year_range_vals) == 2:
            df = df[(df["year"] >= year_range_vals[0]) & (df["year"] <= year_range_vals[1])]
        
        # Filter by region (Reg)
        selected_regions = input.region()
        if selected_regions and len(selected_regions) > 0:
            if isinstance(selected_regions, str):
                selected_regions = [selected_regions]
            df = df[df["Reg"].isin(selected_regions)]
        
        # Filter by peace process (PPName)
        selected_peace_processes = input.peace_process()
        if selected_peace_processes and len(selected_peace_processes) > 0:
            if isinstance(selected_peace_processes, str):
                selected_peace_processes = [selected_peace_processes]
            df = df[df["PPName"].isin(selected_peace_processes)]
        
        # Filter by stage
        selected_stages = input.stage()
        if selected_stages and len(selected_stages) > 0:
            if isinstance(selected_stages, str):
                selected_stages = [selected_stages]
            df = df[df["stage_label"].isin(selected_stages)]
        
        return df

    # Function to get applied filters summary (SIDEBAR VERSION)
    @reactive.calc
    def get_applied_filters():
        filters = []

        # Countries
        countries = input.country()
        print("get_applied_filters recalculated, countries =", countries)  # DEBUG
        if countries:
            text = f"Countries: {', '.join(countries)}"
            if len(countries) > 3:
                text = f"Countries: {', '.join(countries[:3])} + {len(countries)-3} more"
            filters.append(text)

        # Agreement Types
        types = input.agt_type()
        if types:
            text = f"Agreement Type: {', '.join(types)}"
            if len(types) > 2:
                text = f"Agreement Type: {', '.join(types[:2])} + {len(types)-2} more"
            filters.append(text)

        # Year Range
        year_range_vals = input.year_range()
        year_min, year_max = year_range()
        if year_range_vals and len(year_range_vals) == 2:
            if year_range_vals[0] != year_min or year_range_vals[1] != year_max:
                filters.append(f"Years: {year_range_vals[0]}-{year_range_vals[1]}")

        # Regions
        regions = input.region()
        if regions:
            text = f"Regions: {', '.join(regions)}"
            if len(regions) > 3:
                text = f"Regions: {', '.join(regions[:3])} + {len(regions)-3} more"
            filters.append(text)

        # Peace Processes
        peace_processes = input.peace_process()
        if peace_processes:
            text = f"Peace Processes: {', '.join(peace_processes)}"
            if len(peace_processes) > 2:
                text = f"Peace Processes: {', '.join(peace_processes[:2])} + {len(peace_processes)-2} more"
            filters.append(text)

        # Stages
        stages = input.stage()
        if stages:
            text = f"Stages: {', '.join(stages)}"
            if len(stages) > 3:
                text = f"Stages: {', '.join(stages[:3])} + {len(stages)-3} more"
            filters.append(text)
        
        if input.exclude_local_analysis():
            filters.append("Excludes Local agreements")

        return filters

    # Function to get applied filters for PNG (FULL VERSION - no truncation)
    @reactive.calc
    def get_applied_filters_full():
        filters = []
        
        # Countries - show all
        countries = input.country()
        if countries and len(countries) > 0:
            filters.append(f"Countries = {', '.join(countries)}")
        
        # Agreement Types - show all
        types = input.agt_type()
        if types and len(types) > 0:
            filters.append(f"Agreement Type = {', '.join(types)}")
        
        # Year Range
        year_range_vals = input.year_range()
        if year_range_vals and len(year_range_vals) == 2:
            year_min, year_max = year_range()
            if year_range_vals[0] != year_min or year_range_vals[1] != year_max:
                filters.append(f"Years = {year_range_vals[0]}-{year_range_vals[1]}")
        
        # Regions - show all
        regions = input.region()
        if regions and len(regions) > 0:
            filters.append(f"Regions = {', '.join(regions)}")
        
        # Peace Processes - show all
        peace_processes = input.peace_process()
        if peace_processes and len(peace_processes) > 0:
            filters.append(f"Peace Processes = {', '.join(peace_processes)}")
        
        # Stages - show all
        stages = input.stage()
        if stages and len(stages) > 0:
            filters.append(f"Stages = {', '.join(stages)}")
        
        if input.exclude_local_analysis():
            filters.append("Excludes Local agreements")
        
        return filters
    
    # Display applied filters
    @render.ui
    def applied_filters_display():
        filters = get_applied_filters()
        
        if not filters:
            return ui.div(
                ui.tags.i(class_="fas fa-info-circle me-2"),
                "No general filters applied",
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

    # Display filter summary stats
    # Display filter summary stats (matches PNG logic)
    @render.ui
    def filter_summary():
        filtered_df = filtered_data()

        baseline = pax.copy()
        if input.exclude_local_analysis():
            baseline = baseline[baseline["agt_type"] != "Local"]

        total_agreements = baseline["AgtId"].nunique()
        filtered_agreements = filtered_df["AgtId"].nunique()
        percentage = (filtered_agreements / total_agreements * 100) if total_agreements > 0 else 0

        # Year range display
        year_range_vals = input.year_range()
        year_min, year_max = year_range()
        if year_range_vals[0] == year_min and year_range_vals[1] == year_max:
            year_span = ""  # full range selected
        else:
            year_span = f" ({year_range_vals[0]}-{year_range_vals[1]})"

        return ui.div(
            f"General filters: {filtered_agreements:,} of {total_agreements:,} agreements ({percentage:.1f}%){year_span}",
            style="font-weight: 500;"
        )

    # Enhanced reset filters functionality
    @reactive.effect
    @reactive.event(input.reset_filters)
    def _():
        year_min, year_max = year_range()
        
        ui.update_selectize("country", selected=[])
        ui.update_selectize("agt_type", selected=[])
        ui.update_selectize("region", selected=[])
        ui.update_selectize("peace_process", selected=[])
        ui.update_selectize("stage", selected=[])
        ui.update_slider("year_range", value=[year_min, year_max])
        ui.update_checkbox("exclude_local_analysis", value=False)

    # Function to get filter text for PNG annotations (FULL VERSION)
    @reactive.calc
    def get_filter_text_for_png():
        filters = get_applied_filters_full()
        if not filters:
            return "Showing all data"
        
        # Join all filters with " | " separator - show everything
        return f"Filters applied: {' | '.join(filters)}"
    
    #-------------------------------------------------------------------
    # START OF PLOTS
    #-------------------------------------------------------------------

    # AGREEMENTS OVER TIME
    @reactive.calc
    def agreements_over_time_data():
        df = filtered_data()

        year_range_vals = input.year_range()
        start_year, end_year = year_range_vals[0], year_range_vals[1]

        year_frame = pd.DataFrame({
            "year": list(range(start_year, end_year + 1))
        })

        yearly = (
            df.groupby("year")["AgtId"]
            .nunique()
            .reset_index(name="agreements")
        )
        baseline = pax.copy()
        if input.exclude_local_analysis():
            baseline = baseline[baseline["agt_type"] != "Local"]

        all_yearly = (
            baseline[(baseline["year"] >= start_year) & (baseline["year"] <= end_year)]
            .groupby("year")["AgtId"]
            .nunique()
            .reset_index(name="total")
        )

        merged = year_frame.merge(all_yearly, on="year", how="left")
        merged = merged.merge(yearly, on="year", how="left")
        merged = merged.fillna({"total": 0, "agreements": 0})
        merged["total"] = merged["total"].astype(int)
        merged["agreements"] = merged["agreements"].astype(int)

        if input.over_time_mode() == "Percentage":
            merged["percentage"] = np.where(
                merged["total"] > 0,
                merged["agreements"] / merged["total"] * 100,
                0
            )
            return merged[["year", "agreements", "total", "percentage"]]
        else:
            return merged[["year", "agreements", "total"]]

    @render.plot
    def agreements_over_time():
        merged = agreements_over_time_data()
        
        fig, ax = plt.subplots(figsize=(16, 12))
        
        if input.over_time_mode() == "Percentage":
            y_title = "Percentage of All Agreements"
            color = "#7b8ad6"
            y_values = merged["percentage"]
            labels = merged["percentage"].round(1).astype(str) + "%"
        else:
            y_title = "Number of Agreements"
            color = "#091f40"
            y_values = merged["agreements"]
            labels = merged["agreements"].astype(int).astype(str)
        
        ax.plot(merged["year"], y_values, marker='o', color=color, linewidth=2, markersize=6)
        
        if input.show_labels():
            for x, y, label in zip(merged["year"], y_values, labels):
                if y > 0:
                    ax.text(x, y + max(y_values) * 0.02, label, ha='center', va='bottom', fontsize=8)
        
        ax.set_xlabel("Year", fontsize=12)
        ax.set_ylabel(y_title, fontsize=12)
        ax.set_title("Agreements Signed per Year", fontsize=16, fontweight='bold', pad=20)
        ax.grid(True, alpha=0.3)
        
        # Set proper margins and limits
        plt.ylim(0, y_values.max() * 1.15)
        
        return fig

    # AGREEMENTS BY STAGE/TYPE OVER TIME
    @reactive.calc
    def grouped_over_time_data():
        df = filtered_data()
        group_col = "stage_label" if input.group_mode() == "Stage" else "agt_type"

        year_range_vals = input.year_range()
        start_year, end_year = year_range_vals[0], year_range_vals[1]
        all_years = list(range(start_year, end_year + 1))

        if input.group_mode() == "Stage":
            all_groups = stage_order
        else:
            all_groups = sorted(pax["agt_type"].dropna().unique().tolist())
            if input.exclude_local_analysis():
                all_groups = [g for g in all_groups if g != "Local"]

        year_group_grid = []
        for year in all_years:
            for group in all_groups:
                year_group_grid.append({"year": year, group_col: group})

        complete_grid_df = pd.DataFrame(year_group_grid)

        grouped = df.groupby(["year", group_col])["AgtId"].nunique().reset_index(name="count")

        result = complete_grid_df.merge(grouped, on=["year", group_col], how="left").fillna(0)
        result["count"] = result["count"].astype(int)

        pivot_df = result.pivot(index="year", columns=group_col, values="count").fillna(0)
        pivot_df = pivot_df.astype(int)

        if input.group_mode() == "Stage":
            available_stages = [stage for stage in stage_order if stage in pivot_df.columns]
            other_stages = [stage for stage in pivot_df.columns if stage not in stage_order]
            pivot_df = pivot_df[available_stages + other_stages]

        return pivot_df.reset_index()
    # Updated render plot function with fixed legend and positioning
    @render.plot
    def grouped_over_time():
        grouped = grouped_over_time_data()
        group_col = "stage_label" if input.group_mode() == "Stage" else "agt_type"
        
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Create pivot table for stacked bar chart
        #pivot_df = grouped.pivot(index="year", columns=group_col, values="count").fillna(0)
        pivot_df = grouped.set_index('year')
        
        # Order stages if grouping by stage
        if input.group_mode() == "Stage":
            # Reorder columns according to stage_order
            available_stages = [stage for stage in stage_order if stage in pivot_df.columns]
            other_stages = [stage for stage in pivot_df.columns if stage not in stage_order]
            pivot_df = pivot_df[available_stages + other_stages]
        
       # Get colors for the current grouping
        colors = get_colors_for_grouping(input.group_mode(), pivot_df.columns)

        # Create stacked bar chart with custom colors
        pivot_df.plot(kind='bar', stacked=True, ax=ax, width=0.8, color=colors)

        # Set y-axis limit to max value + margin
        year_totals = pivot_df.sum(axis=1)
        max_total = year_totals.max()
        ax.set_ylim(0, max_total + 8)
        
        # Add data labels if enabled
        if input.show_labels():
            year_totals = pivot_df.sum(axis=1)  # Sum across all stages per year
            for i, total in enumerate(year_totals):
                if total > 0:  # Only show label if there are agreements
                    ax.text(i, total + 0.5, f"{int(total)}", ha='center', fontsize=10, fontweight='bold')
            for container in ax.containers:
                ax.bar_label(container, fmt='%d', label_type='center', fontsize=8, color='white')
        
        ax.set_xlabel("Year", fontsize=12)
        ax.set_ylabel("Number of Agreements", fontsize=12)
        ax.set_title(f"Number of Agreements per Year, by Agreement {input.group_mode()}", fontsize=16, fontweight='bold', pad=20, y=1.15)
        
        # FIXED: Legend with proper column count
        ncol = len(pivot_df.columns) if len(pivot_df.columns) <= 4 else 4  # Use actual number of columns, max 7
        ax.legend(title=input.group_mode(), bbox_to_anchor=(0.5, 1), loc='lower center', fontsize=10, ncol=ncol)
        
        plt.xticks(rotation=45)
        
        return fig

    # AGREEMENTS BY STAGE DATA
    @reactive.calc
    def agreements_by_stage_data():
        df = filtered_data()
        
        if input.stage_mode() == "Count":
            stage_data = df.groupby("stage_label")["AgtId"].nunique().reset_index(name="count")
            # Order stages
            stage_data['stage_label'] = pd.Categorical(stage_data['stage_label'], categories=stage_order, ordered=True)
            stage_data = stage_data.sort_values('stage_label')
            # Return only relevant columns
            return stage_data[["stage_label", "count"]]
        else:
            # Calculate percentages for both filtered and all data
            filtered_stage_data = df.groupby("stage_label")["AgtId"].nunique().reset_index(name="filtered_count")
            baseline = pax.copy()
            if input.exclude_local_analysis():
                baseline = baseline[baseline["agt_type"] != "Local"]

            all_stage_data = baseline.groupby("stage_label")["AgtId"].nunique().reset_index(name="all_count")
            total_all = baseline["AgtId"].nunique()                     
            total_filtered = df["AgtId"].nunique()
          
            
            # Create a complete dataframe with all stages
            all_stages_df = pd.DataFrame({'stage_label': stage_order})
            
            # Merge with actual data
            stage_data = all_stages_df.merge(filtered_stage_data, on="stage_label", how="left").fillna(0)
            stage_data = stage_data.merge(all_stage_data, on="stage_label", how="left").fillna(0)
            
            stage_data["filtered_percentage"] = (stage_data["filtered_count"] / total_filtered * 100) if total_filtered > 0 else 0
            stage_data["all_percentage"] = (stage_data["all_count"] / total_all * 100) if total_all > 0 else 0
            
            # Return only relevant columns
            return stage_data[["stage_label", "filtered_count", "all_count", "filtered_percentage", "all_percentage"]]

    @render.plot
    def agreements_by_stage():
        stage_data = agreements_by_stage_data()
        
        fig, ax = plt.subplots(figsize=(16, 12))
        
        if input.stage_mode() == "Count":
            y_vals = stage_data["count"]
            color = "#091f40"
            y_title = "Number of Agreements"
            labels = stage_data["count"].astype(str)
            
            bars = ax.bar(stage_data["stage_label"], y_vals, color=color)
            
            if input.show_labels():
                for bar, label in zip(bars, labels):
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2, height + max(y_vals) * 0.01, 
                        label, ha='center', va='bottom', fontsize=9)
        else:
            x = np.arange(len(stage_data))
            width = 0.35
            
            bars1 = ax.bar(x - width/2, stage_data["filtered_percentage"], width, 
                        label='Selected Agreements', color='#091f40')
            bars2 = ax.bar(x + width/2, stage_data["all_percentage"], width, 
                        label='All Agreements', color='#cccccc')
            
            if input.show_labels():
                filtered_labels = stage_data["filtered_percentage"].round(0).astype(int).astype(str) + "%"
                all_labels = stage_data["all_percentage"].round(0).astype(int).astype(str) + "%"
                
                for bars, labels in [(bars1, filtered_labels), (bars2, all_labels)]:
                    for bar, label in zip(bars, labels):
                        height = bar.get_height()
                        ax.text(bar.get_x() + bar.get_width()/2, height + 1, label, 
                            ha='center', va='bottom', fontsize=10, fontweight='bold')
            
            ax.set_xticks(x)
            ax.set_xticklabels(stage_data["stage_label"])
            y_title = "Percentage of Agreements"
            
            y_max = max(bars1.datavalues.max(), bars2.datavalues.max())
            ax.set_ylim(0, y_max + 10)
            
            ax.legend(bbox_to_anchor=(0.5, 1), loc='lower center', ncol=2, fontsize=12)
        
        ax.set_xlabel("Stage", fontsize=12)
        ax.set_ylabel(y_title, fontsize=12)
        ax.set_title("Agreements by Stage of Process", fontsize=16, fontweight='bold', pad=20, y=1.1)
        ax.spines[['top', 'right']].set_visible(False)
        
        plt.xticks(rotation=45, ha='right')
        
        return fig

    # AGREEMENTS BY TOPIC CATEGORY
    @reactive.calc
    def topic_category_data():
        df = filtered_data()
        topic_counts = pax_topics[(pax_topics['value'] > 0) & (pax_topics['ID'] != 'ImSrc')]
        topic_counts = topic_counts[topic_counts["AgtId"].isin(df["AgtId"])]
        by_cat = topic_counts.groupby("category")["AgtId"].nunique().reset_index(name="count")
        return by_cat

    @render.plot
    def topic_category_counts():
        by_cat = topic_category_data()
        
        fig, ax = plt.subplots(figsize=(16, 12))
        
        # Sort and create horizontal bar chart
        by_cat_sorted = by_cat.sort_values("count")
        bars = ax.barh(by_cat_sorted["category"], by_cat_sorted["count"], color="#091f40")
        
        if input.show_labels():
            for bar in bars:
                width = bar.get_width()
                ax.text(width + max(by_cat_sorted["count"]) * 0.01, bar.get_y() + bar.get_height()/2, 
                       f'{int(width)}', ha='left', va='center', fontsize=9)
        
        # Fix x-axis limit to accommodate labels
        max_val = max(by_cat_sorted["count"])
        ax.set_xlim(0, max_val * 1.15)
        
        ax.set_xlabel("Number of Agreements", fontsize=12)
        ax.set_ylabel("Topic Category", fontsize=12)
        ax.set_title("Agreements by Topic Category", fontsize=16, fontweight='bold', pad=20)
        
        return fig

    # Test PNG export
    @output
    @render.download(filename="test_plot.png")
    def test_png_export():
        try:
            # Create a simple test plot
            fig, ax = plt.subplots(figsize=(8, 6))
            ax.plot([1, 2, 3, 4], [1, 4, 2, 3], 'bo-')
            ax.set_title("Test Plot")
            ax.set_xlabel("X")
            ax.set_ylabel("Y")
            
            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=300, facecolor='white')
            buf.seek(0)
            plt.close(fig)
            
            print(f"Test PNG size: {len(buf.getvalue())} bytes")
            return buf
        except Exception as e:
            print(f"Test PNG error: {e}")
            return io.BytesIO()

    # Helper function for CSV exports
    def export_csv_data(data_func):
        try:
            df = data_func()
            csv_string = df.to_csv(index=False)
            return io.BytesIO(csv_string.encode('utf-8'))
        except Exception as e:
            print(f"Error in CSV export: {e}")
            return io.BytesIO(b"Error,Message\nExport Failed,Please try again")

    # PNG DOWNLOAD HANDLERS WITH FULL FILTER DISPLAY
    
    # Agreements Over Time Downloads
    @output
    @render.download(filename="agreements_over_time.png")
    def home_export_over_time_png():
        try:
            # Get data directly (preserves reactive context)
            merged = agreements_over_time_data()
            
            # Create figure inline
            fig, ax = plt.subplots(figsize=(14, 8))
            
            if input.over_time_mode() == "Percentage":
                y_title = "Percentage of All Agreements"
                color = "#7b8ad6"
            else:
                y_title = "Number of Agreements"
                color = "#091f40"

            if input.over_time_mode() == "Percentage":
                y_values = merged["percentage"]
                labels = merged["percentage"].round(1).astype(str) + "%"
            else:
                y_values = merged["agreements"]
                labels = merged["agreements"].astype(int).astype(str)

            ax.plot(merged["year"], y_values, marker='o', color=color, linewidth=2, markersize=6)

            if input.show_labels():
                for x, y, label in zip(merged["year"], y_values, labels):
                    if y > 0:  # <-- Include this condition
                        ax.text(x, y + max(y_values) * 0.03, label, ha='center', va='bottom', fontsize=8)
            
            ax.set_xlabel("Year", fontsize=12)
            ax.set_ylabel(y_title, fontsize=12)
            ax.set_title("Agreements Signed per Year", fontsize=16, fontweight='bold', pad=20)
            ax.grid(True, alpha=0.3)
            plt.ylim(0, y_values.max() * 1.15)
            
            # Get filter text and add as subtitle
            filter_text = get_filter_text_for_png()
            ax.text(0.5, 0.025, filter_text, transform=fig.transFigure, 
                    ha='center', va='bottom', fontsize=8, style='italic', color='#666666')

            # Add data version instead of timestamp
            data_version = pax["Ver"].max() if "Ver" in pax.columns else "Unknown"
            ax.text(0.98, 0.02, f"PA-X Database v{data_version}", transform=fig.transFigure, 
                    ha='right', va='bottom', fontsize=7, color='#999999')
            plt.tight_layout()
            
            # Add logo if available
            logo_path = "static/logos/Pax.png"
            if os.path.exists(logo_path):
                try:
                    logo_img = plt.imread(logo_path)
                    logo_ax = fig.add_axes([0.92, 0.94, 0.078, 0.078])
                    logo_ax.imshow(logo_img, alpha=0.8)
                    logo_ax.axis('off')
                except Exception as e:
                    print(f"Warning: Could not add logo: {e}")
            
            buf = io.BytesIO()
            fig.savefig(buf, format="png", bbox_inches="tight", dpi=300, 
                       facecolor='white', edgecolor='none')
            buf.seek(0)
            plt.close(fig)
            return buf
            
        except Exception as e:
            print(f"Error in PNG export: {e}")
            return io.BytesIO()

    @output
    @render.download(filename="agreements_over_time.csv")
    def home_export_over_time_csv():
        return export_csv_data(agreements_over_time_data)

    # Grouped Over Time Downloads (FIXED VERSION)
    @output
    @render.download(filename="grouped_over_time.png")
    def home_export_grouped_over_time_png():
        try:
            # Get data directly
            grouped = grouped_over_time_data()
            group_col = "stage_label" if input.group_mode() == "Stage" else "agt_type"
            
            # Create figure inline with more height for filter text
            fig, ax = plt.subplots(figsize=(14, 8))  # Increased height
            
            # Create pivot table for stacked bar chart
            #pivot_df = grouped.pivot(index="year", columns=group_col, values="count").fillna(0)
            pivot_df = grouped.set_index('year')
            
            # Order stages if grouping by stage
            if input.group_mode() == "Stage":
                available_stages = [stage for stage in stage_order if stage in pivot_df.columns]
                other_stages = [stage for stage in pivot_df.columns if stage not in stage_order]
                pivot_df = pivot_df[available_stages + other_stages]
            
            # Get colors for the current grouping
            colors = get_colors_for_grouping(input.group_mode(), pivot_df.columns)

            # Create stacked bar chart with custom colors
            pivot_df.plot(kind='bar', stacked=True, ax=ax, width=0.8, color=colors)
            
            # Set y-axis limit
            year_totals = pivot_df.sum(axis=1)
            max_total = year_totals.max()
            ax.set_ylim(0, max_total + 8)
            
            # Add data labels if enabled
            if input.show_labels():
                # Add total labels on top
                for i, total in enumerate(year_totals):
                    if total > 0:  # Only show label if there are agreements
                        ax.text(i, total + 0.8, f"{int(total)}", ha='center', fontsize=10, fontweight='bold')
                # Add labels inside segments
                for container in ax.containers:
                    ax.bar_label(container, fmt='%d', label_type='center', fontsize=8, color='white')
            
            ax.set_xlabel("Year", fontsize=12)
            ax.set_ylabel("Number of Agreements", fontsize=12)
            ax.set_title(f"Agreements by {input.group_mode()} Over Time", fontsize=16, fontweight='bold', pad=25, y=1.08)
            
            # FIXED: Legend with proper column count
            ncol = len(pivot_df.columns) if len(pivot_df.columns) <= 7 else 7
            ax.legend(title=input.group_mode(), bbox_to_anchor=(0.5, 1.01), 
                     loc='lower center', ncol=ncol, fontsize=9)
            
            plt.xticks(rotation=45)
            
            # FIXED: Filter text positioning - moved higher to avoid axis overlap
            filter_text = get_filter_text_for_png()
            ax.text(0.5, 0.0035, filter_text, transform=fig.transFigure, 
                    ha='center', va='bottom', fontsize=8, style='italic', color='#666666')

            # Add data version - moved higher too
            data_version = pax["Ver"].max() if "Ver" in pax.columns else "Unknown"
            ax.text(0.98, 0.02, f"PA-X Database v{data_version}", transform=fig.transFigure, 
                    ha='right', va='bottom', fontsize=7, color='#999999')
            
            plt.tight_layout()
            
            # Add logo - adjusted position
            logo_path = "static/logos/Pax.png"
            if os.path.exists(logo_path):
                try:
                    logo_img = plt.imread(logo_path)
                    logo_ax = fig.add_axes([0.92, 0.94, 0.078, 0.078])  # Moved slightly down
                    logo_ax.imshow(logo_img, alpha=0.8)
                    logo_ax.axis('off')
                except Exception as e:
                    print(f"Warning: Could not add logo: {e}")
            
            buf = io.BytesIO()
            fig.savefig(buf, format="png", bbox_inches="tight", dpi=300, 
                       facecolor='white', edgecolor='none')
            buf.seek(0)
            plt.close(fig)
            return buf
            
        except Exception as e:
            print(f"Error in PNG export: {e}")
            return io.BytesIO()

    @output
    @render.download(filename="grouped_over_time.csv")
    def home_export_grouped_over_time_csv():
        return export_csv_data(grouped_over_time_data)

    # Agreements by Stage Downloads
    @output
    @render.download(filename="agreements_by_stage.png")
    def home_export_stage_png():
        try:
            # Get data directly
            stage_data = agreements_by_stage_data()
            
            # Create figure inline
            fig, ax = plt.subplots(figsize=(14, 8))
            
            if input.stage_mode() == "Count":
                y_vals = stage_data["count"]
                color = "#091f40"
                y_title = "Number of Agreements"
                labels = stage_data["count"].astype(str)
                
                bars = ax.bar(stage_data["stage_label"], y_vals, color=color)
                
                if input.show_labels():
                    for bar, label in zip(bars, labels):
                        height = bar.get_height()
                        ax.text(bar.get_x() + bar.get_width()/2, height + max(y_vals) * 0.01, 
                            label, ha='center', va='bottom', fontsize=9)
            else:
                x = np.arange(len(stage_data))
                width = 0.35
                
                bars1 = ax.bar(x - width/2, stage_data["filtered_percentage"], width, 
                            label='Selected Agreements', color='#091f40')
                bars2 = ax.bar(x + width/2, stage_data["all_percentage"], width, 
                            label='All Agreements', color='#cccccc')
                
                if input.show_labels():
                    filtered_labels = stage_data["filtered_percentage"].round(0).astype(int).astype(str) + "%"
                    all_labels = stage_data["all_percentage"].round(0).astype(int).astype(str) + "%"
                    
                    for bars, labels in [(bars1, filtered_labels), (bars2, all_labels)]:
                        for bar, label in zip(bars, labels):
                            height = bar.get_height()
                            ax.text(bar.get_x() + bar.get_width()/2, height + 1, label, 
                                ha='center', va='bottom', fontsize=10, fontweight='bold')
                
                ax.set_xticks(x)
                ax.set_xticklabels(stage_data["stage_label"])
                y_title = "Percentage of Agreements"
                
                y_max = max(bars1.datavalues.max(), bars2.datavalues.max())
                ax.set_ylim(0, y_max + 10)
                
                ax.legend(bbox_to_anchor=(0.5, 1), loc='lower center', ncol=2)
            
            ax.set_xlabel("Stage", fontsize=12)
            ax.set_ylabel(y_title, fontsize=12)
            ax.set_title("Agreements by Stage of Process", fontsize=16, fontweight='bold', pad=20, y=1.1)
            ax.spines[['top', 'right']].set_visible(False)
            
            plt.xticks(rotation=45, ha='right')
            
            # Get filter text and add as subtitle
            filter_text = get_filter_text_for_png()
            ax.text(0.5, 0.0025, filter_text, transform=fig.transFigure, 
                    ha='center', va='bottom', fontsize=8, style='italic', color='#666666')

            # Add data version
            data_version = pax["Ver"].max() if "Ver" in pax.columns else "Unknown"
            ax.text(0.98, 0.02, f"PA-X Database v{data_version}", transform=fig.transFigure, 
                    ha='right', va='bottom', fontsize=7, color='#999999')
            
            plt.tight_layout()
            
            # Add logo
            logo_path = "static/logos/Pax.png"
            if os.path.exists(logo_path):
                try:
                    logo_img = plt.imread(logo_path)
                    logo_ax = fig.add_axes([0.92, 0.94, 0.078, 0.078])
                    logo_ax.imshow(logo_img, alpha=0.8)
                    logo_ax.axis('off')
                except Exception as e:
                    print(f"Warning: Could not add logo: {e}")
            
            buf = io.BytesIO()
            fig.savefig(buf, format="png", bbox_inches="tight", dpi=300, 
                    facecolor='white', edgecolor='none')
            buf.seek(0)
            plt.close(fig)
            return buf
            
        except Exception as e:
            print(f"Error in PNG export: {e}")
            return io.BytesIO()

    @output
    @render.download(filename="agreements_by_stage.csv")
    def home_export_stage_csv():
        return export_csv_data(agreements_by_stage_data)

    # Topic Category Downloads
    @output
    @render.download(filename="topic_category.png")
    def home_export_topic_cat_png():
        try:
            # Get data directly
            by_cat = topic_category_data()
            
            # Create figure inline
            fig, ax = plt.subplots(figsize=(14, 8))
            
            # Sort and create horizontal bar chart
            by_cat_sorted = by_cat.sort_values("count")
            bars = ax.barh(by_cat_sorted["category"], by_cat_sorted["count"], color="#091f40")
            
            if input.show_labels():
                for bar in bars:
                    width = bar.get_width()
                    ax.text(width + max(by_cat_sorted["count"]) * 0.01, bar.get_y() + bar.get_height()/2, 
                           f'{int(width)}', ha='left', va='center', fontsize=9)
            
            # Fix x-axis limit to accommodate labels
            max_val = max(by_cat_sorted["count"])
            ax.set_xlim(0, max_val * 1.15)
            
            ax.set_xlabel("Number of Agreements", fontsize=12)
            ax.set_ylabel("Topic Category", fontsize=12)
            ax.set_title("Agreements by Topic Category", fontsize=16, fontweight='bold', pad=20)
            
            # Get filter text and add as subtitle
            filter_text = get_filter_text_for_png()
            ax.text(0.5, 0.025, filter_text, transform=fig.transFigure, 
                    ha='center', va='bottom', fontsize=8, style='italic', color='#666666')

            # Add data version
            data_version = pax["Ver"].max() if "Ver" in pax.columns else "Unknown"
            ax.text(0.98, 0.02, f"PA-X Database v{data_version}", transform=fig.transFigure, 
                    ha='right', va='bottom', fontsize=7, color='#999999')
            
            plt.tight_layout()
            
            # Add logo
            logo_path = "static/logos/Pax.png"
            if os.path.exists(logo_path):
                try:
                    logo_img = plt.imread(logo_path)
                    logo_ax = fig.add_axes([0.92, 0.94, 0.078, 0.078])
                    logo_ax.imshow(logo_img, alpha=0.8)
                    logo_ax.axis('off')
                except Exception as e:
                    print(f"Warning: Could not add logo: {e}")
            
            buf = io.BytesIO()
            fig.savefig(buf, format="png", bbox_inches="tight", dpi=300, 
                       facecolor='white', edgecolor='none')
            buf.seek(0)
            plt.close(fig)
            return buf
            
        except Exception as e:
            print(f"Error in PNG export: {e}")
            return io.BytesIO()

    @output
    @render.download(filename="topic_category.csv")
    def home_export_topic_cat_csv():
        return export_csv_data(topic_category_data)
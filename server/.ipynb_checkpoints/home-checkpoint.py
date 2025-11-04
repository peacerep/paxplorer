# Complete fixed server/home.py code

import io
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from shiny import reactive, render, ui
from utils.export_handlers import make_csv_download, make_png_download

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# Load data
pax = pd.read_csv(DATA_DIR / "pax.csv")
pax_id_to_con = pd.read_csv(DATA_DIR / "pax_id_to_con_info_v9.csv")
pax_topics = pd.read_csv(DATA_DIR / "pax_topics.csv")


# Define stage order at the top of your file (after imports)
stage_order = [
    'Pre-negotiation/process', 'Ceasefire', 'Framework-substantive, partial',
    'Framework-substantive, comprehensive', 'Implementation', 'Renewal', 'Other'
]

def server(input, output, session):

    # Store choices for comparison
    @reactive.calc
    def country_choices():
        return sorted(pax_id_to_con["name"].dropna().unique().tolist())

    @reactive.calc  
    def agt_type_choices():
        return sorted(pax["agt_type"].dropna().unique().tolist())

    # Populate dropdowns dynamically
    @reactive.effect
    def _():
        countries = country_choices()
        agt_types = agt_type_choices()
        
        ui.update_selectize("country", choices=countries, selected=[])
        ui.update_selectize("agt_type", choices=agt_types, selected=[])

    @reactive.calc
    def filtered_data():
        df = pax.copy()
        
        # Filter by country - if any countries are selected, filter to those
        selected_countries = input.country()
        if selected_countries and len(selected_countries) > 0:
            # Ensure it's a list even if single selection
            if isinstance(selected_countries, str):
                selected_countries = [selected_countries]
            agt_ids = pax_id_to_con[pax_id_to_con["name"].isin(selected_countries)]["AgtId"].unique()
            df = df[df["AgtId"].isin(agt_ids)]
        
        # Filter by agent type - if any types are selected, filter to those
        selected_types = input.agt_type()
        if selected_types and len(selected_types) > 0:
            # Ensure it's a list even if single selection
            if isinstance(selected_types, str):
                selected_types = [selected_types]
            df = df[df["agt_type"].isin(selected_types)]
        
        return df

    # Reset filters functionality
    @reactive.effect
    @reactive.event(input.reset_filters)
    def _():
        ui.update_selectize("country", selected=[])
        ui.update_selectize("agt_type", selected=[])

    @render.download(filename="test.txt")
    def test_download():
        return "This is a test file"

    # AGREEMENTS OVER TIME
    @reactive.calc
    def agreements_over_time_data():
        df = filtered_data()
        yearly = df.groupby("year")["AgtId"].nunique().reset_index(name="agreements")
        all_yearly = pax.groupby("year")["AgtId"].nunique().reset_index(name="total")
        merged = all_yearly.merge(yearly, on="year", how="left").fillna(0)
        
        if input.over_time_mode() == "Percentage":
            # Calculate percentage of agreements signed that year (filtered / total for that year)
            merged["value"] = merged["agreements"] / merged["total"] * 100
            merged["value"] = merged["value"].fillna(0)
            merged["label"] = merged["value"].round(1).astype(str) + "%"
        else:
            merged["value"] = merged["agreements"]
            merged["label"] = merged["value"].astype(int).astype(str)
        
        return merged

    @render.plot
    def agreements_over_time():
        merged = agreements_over_time_data()
        
        fig, ax = plt.subplots(figsize=(14, 8))
        
        if input.over_time_mode() == "Percentage":
            y_title = "Percentage of All Agreements"
            color = "#7b8ad6"
        else:
            y_title = "Number of Agreements"
            color = "#091f40"
        
        ax.plot(merged["year"], merged["value"], marker='o', color=color, linewidth=2, markersize=6)
        
        if input.show_labels():
            for x, y, label in zip(merged["year"], merged["value"], merged["label"]):
                if y > 0:
                    ax.text(x, y + max(merged["value"]) * 0.03, label, ha='center', va='bottom', fontsize=8)
        
        ax.set_xlabel("Year", fontsize=12)
        ax.set_ylabel(y_title, fontsize=12)
        ax.set_title("Agreements Signed per Year", fontsize=16, fontweight='bold', pad=20)
        ax.grid(True, alpha=0.3)
        
        # Set proper margins and limits
        plt.ylim(0, merged['value'].max() * 1.15)
        plt.tight_layout(rect=[0, 0, 1, 0.97])
        
        return fig

    # AGREEMENTS BY STAGE/TYPE OVER TIME
    @reactive.calc
    def grouped_over_time_data():
        df = filtered_data()
        group_col = "stage_label" if input.group_mode() == "Stage" else "agt_type"
        grouped = df.groupby(["year", group_col])["AgtId"].nunique().reset_index(name="count")
        return grouped

    @render.plot
    def grouped_over_time():
        grouped = grouped_over_time_data()
        group_col = "stage_label" if input.group_mode() == "Stage" else "agt_type"
        
        fig, ax = plt.subplots(figsize=(16, 9))
        
        # Create pivot table for stacked bar chart
        pivot_df = grouped.pivot(index="year", columns=group_col, values="count").fillna(0)
        
        # Order stages if grouping by stage
        if input.group_mode() == "Stage":
            # Reorder columns according to stage_order
            available_stages = [stage for stage in stage_order if stage in pivot_df.columns]
            other_stages = [stage for stage in pivot_df.columns if stage not in stage_order]
            pivot_df = pivot_df[available_stages + other_stages]
        
        # Create stacked bar chart
        pivot_df.plot(kind='bar', stacked=True, ax=ax, width=0.8)

        # Set y-axis limit to max value + 5
        year_totals = pivot_df.sum(axis=1)
        max_total = year_totals.max()
        ax.set_ylim(0, max_total + 5)
        
        # Add data labels if enabled
        if input.show_labels():
            year_totals = pivot_df.sum(axis=1)  # Sum across all stages per year
            for i, total in enumerate(year_totals):
                ax.text(i, total + 1, f"{int(total)}", ha='center', fontsize=10, fontweight='bold')
            for container in ax.containers:
                ax.bar_label(container, fmt='%d', label_type='center', fontsize=8, color='white')
        
        ax.set_xlabel("Year", fontsize=12)
        ax.set_ylabel("Number of Agreements", fontsize=12)
        #ax.suptitle(f"Agreements by {input.group_mode()} Over Time", fontsize=18, fontweight='bold', y=1)
        ax.set_title(f"Agreements by {input.group_mode()} Over Time", fontsize=16, fontweight='bold', pad=20)
        
        # Legend at top, horizontal
        #ncol = min(len(pivot_df.columns), 4)  # Limit columns to prevent overflow
        ax.legend(title=input.group_mode(), bbox_to_anchor=(0.5, 1.02), loc='lower center', fontsize=10, ncol=len(stage_order))
        
        plt.xticks(rotation=45)
        plt.tight_layout(rect=[0, 0, 1, 0.97])
        
        return fig

    # AGREEMENTS BY STAGE
    # AGREEMENTS BY STAGE DATA
    @reactive.calc
    def agreements_by_stage_data():
        df = filtered_data()
        
        if input.stage_mode() == "Count":
            stage_data = df.groupby("stage_label")["AgtId"].nunique().reset_index(name="count")
            # Order stages
            stage_data['stage_label'] = pd.Categorical(stage_data['stage_label'], categories=stage_order, ordered=True)
            stage_data = stage_data.sort_values('stage_label')
            stage_data["label"] = stage_data["count"].astype(str)
            stage_data["value"] = stage_data["count"]
        else:
            # Calculate percentages for both filtered and all data
            filtered_stage_data = df.groupby("stage_label")["AgtId"].nunique().reset_index(name="count")
            all_stage_data = pax.groupby("stage_label")["AgtId"].nunique().reset_index(name="all_count")
            
            total_filtered = df["AgtId"].nunique()
            total_all = pax["AgtId"].nunique()
            
            # Create a complete dataframe with all stages
            all_stages_df = pd.DataFrame({'stage_label': stage_order})
            
            # Merge with actual data
            stage_data = all_stages_df.merge(filtered_stage_data, on="stage_label", how="left").fillna(0)
            stage_data = stage_data.merge(all_stage_data, on="stage_label", how="left").fillna(0)
            
            stage_data["filtered_percentage"] = stage_data["count"] / total_filtered if total_filtered > 0 else 0
            stage_data["all_percentage"] = stage_data["all_count"] / total_all if total_all > 0 else 0
            
            stage_data["filtered_label"] = (stage_data["filtered_percentage"] * 100).round(0).astype(int).astype(str) + "%"
            stage_data["all_label"] = (stage_data["all_percentage"] * 100).round(0).astype(int).astype(str) + "%"
        
        return stage_data
   


    @render.plot
    def agreements_by_stage():
        stage_data = agreements_by_stage_data()
        
        fig, ax = plt.subplots(figsize=(14, 8))
        
        if input.stage_mode() == "Count":
            y_vals = stage_data["count"]
            color = "#091f40"
            y_title = "Number of Agreements"
            
            bars = ax.bar(stage_data["stage_label"], y_vals, color=color)
            
            if input.show_labels():
                for bar, label in zip(bars, stage_data["label"]):
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2, height + max(y_vals) * 0.01, 
                           label, ha='center', va='bottom', fontsize=9)
        else:
            x = np.arange(len(stage_data))
            width = 0.35
            
            bars1 = ax.bar(x - width/2, stage_data["filtered_percentage"] * 100, width, 
                          label='Selected Agreements', color='#091f40')
            bars2 = ax.bar(x + width/2, stage_data["all_percentage"] * 100, width, 
                          label='All Agreements', color='#cccccc')
            
            if input.show_labels():
                for bars, labels in [(bars1, stage_data["filtered_label"]), (bars2, stage_data["all_label"])]:
                    for bar, label in zip(bars, labels):
                        height = bar.get_height()
                        ax.text(bar.get_x() + bar.get_width()/2, height + 1, label, 
                               ha='center', va='bottom', fontsize=10, fontweight='bold')
            
            ax.set_xticks(x)
            ax.set_xticklabels(stage_data["stage_label"])
            y_title = "Percentage of Agreements"
            
            # Fix legend positioning
            ax.legend(bbox_to_anchor=(0.5, 1.02), loc='lower center', ncol=2, fontsize=12)
        
        ax.set_xlabel("Stage", fontsize=12)
        ax.set_ylabel(y_title, fontsize=12)
        ax.set_title("Agreements by Stage of Process", fontsize=16, fontweight='bold', pad=20)
        ax.grid(axis='y', linestyle='--', alpha=0.3)
        ax.spines[['top', 'right']].set_visible(False)
        
        plt.xticks(rotation=45, ha='right')
        #plt.tight_layout(rect=[0, 0, 1, 0.97])
        plt.tight_layout()
        #fig.subplots_adjust(top=0.88, bottom=0.15)
        
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
        
        plt.tight_layout(rect=[0, 0, 1, 0.97])
        
        return fig

    # TOPIC x STAGE STACKED BAR
    @reactive.calc
    def topic_stage_data():
        df = filtered_data()
        topics = pax_topics[(pax_topics['value'] > 0) & (pax_topics['ID'] != 'ImSrc')]
        topics = topics[topics["AgtId"].isin(df["AgtId"])]
        merged = topics.merge(df[["AgtId", "stage_label"]], on="AgtId")
        grouped = merged.groupby(["category", "stage_label"])["AgtId"].nunique().reset_index(name="count")
        return grouped

    @render.plot
    def topic_stage_stack():
        grouped = topic_stage_data()
        
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # Create pivot table for stacked bar chart
        pivot_df = grouped.pivot(index="category", columns="stage_label", values="count").fillna(0)
        
        # Order stages if they exist in the data
        available_stages = [stage for stage in stage_order if stage in pivot_df.columns]
        other_stages = [stage for stage in pivot_df.columns if stage not in stage_order]
        pivot_df = pivot_df[available_stages + other_stages]
        
        # Create horizontal stacked bar chart
        pivot_df.plot(kind='barh', stacked=True, ax=ax, width=0.8)
        
        if input.show_labels():
            for container in ax.containers:
                ax.bar_label(container, label_type='center', fontsize=8)
        
        ax.set_xlabel("Number of Agreements", fontsize=12)
        ax.set_ylabel("Topic Category", fontsize=12)
        ax.set_title("Agreements by Topic Category and Stage of Process", fontsize=16, fontweight='bold', pad=20)
        
        # Fix legend positioning - move it outside the plot area
        ax.legend(title="Stage", bbox_to_anchor=(1.05, 1), loc='upper center', fontsize=10)
        
        plt.tight_layout(rect=[0, 0, 1, 0.97])
        
        return fig

    # HELPER FUNCTIONS FOR EXPORTS
    def get_agreements_over_time_fig():
        merged = agreements_over_time_data()
        
        fig, ax = plt.subplots(figsize=(14, 8))
        
        if input.over_time_mode() == "Percentage":
            y_title = "% of Agreements Signed That Year"
            color = "#7b8ad6"
        else:
            y_title = "Number of Agreements"
            color = "#091f40"

        ax.plot(merged["year"], merged["value"], marker='o', color=color, linewidth=2, markersize=6)
        
        if input.show_labels():
            for x, y, label in zip(merged["year"], merged["value"], merged["label"]):
                if y > 0:
                    ax.text(x, y + max(merged["value"]) * 0.02, label, ha='center', va='bottom', fontsize=8)
        
        ax.set_xlabel("Year", fontsize=12)
        ax.set_ylabel(y_title, fontsize=12)
        ax.set_title("Agreements Over Time", fontsize=14, pad=20)
        ax.grid(True, alpha=0.3)
        
        # Add logo if available
        try:
            from PIL import Image
            logo_path = Path(__file__).resolve().parent.parent / "static" / "logos" / "Pax.png"
            if logo_path.exists():
                logo = Image.open(logo_path)
                fig.figimage(logo, xo=fig.bbox.xmax-200, yo=fig.bbox.ymax-100, alpha=0.6, zorder=10)
        except ImportError:
            pass
        
        plt.tight_layout()
        return fig

    def get_grouped_over_time_fig():
        grouped = grouped_over_time_data()
        group_col = "stage_label" if input.group_mode() == "Stage" else "agt_type"
        
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # Create pivot table for stacked bar chart
        pivot_df = grouped.pivot(index="year", columns=group_col, values="count").fillna(0)
        
        # Order stages if grouping by stage
        if input.group_mode() == "Stage":
            available_stages = [stage for stage in stage_order if stage in pivot_df.columns]
            other_stages = [stage for stage in pivot_df.columns if stage not in stage_order]
            pivot_df = pivot_df[available_stages + other_stages]
        
        # Create stacked bar chart
        pivot_df.plot(kind='bar', stacked=True, ax=ax, width=0.8)
        
        # Add data labels if enabled
        if input.show_labels():
            for container in ax.containers:
                ax.bar_label(container, label_type='center', fontsize=8)
        
        ax.set_xlabel("Year", fontsize=12)
        ax.set_ylabel("Number of Agreements", fontsize=12)
        ax.set_title(f"Agreements by {input.group_mode()} Over Time", fontsize=14, pad=20)
        ax.legend(title=input.group_mode(), bbox_to_anchor=(0.5, 1.02), loc='lower center', ncol=len(pivot_df.columns))
        
        plt.xticks(rotation=45)
        plt.tight_layout()
        return fig

    def get_agreements_by_stage_fig():
        stage_data = agreements_by_stage_data()
        
        fig, ax = plt.subplots(figsize=(14, 8))
        
        if input.stage_mode() == "Count":
            y_vals = stage_data["count"]
            color = "#091f40"
            y_title = "Number of Agreements"
            
            bars = ax.bar(stage_data["stage_label"], y_vals, color=color)
            
            # Add value labels on bars
            if input.show_labels():
                for bar, label in zip(bars, stage_data["label"]):
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2, height + max(y_vals) * 0.01, 
                           label, ha='center', va='bottom', fontsize=9)
        else:
            # Two bars comparison
            x = np.arange(len(stage_data))
            width = 0.35
            
            bars1 = ax.bar(x - width/2, stage_data["filtered_percentage"] * 100, width, 
                          label='Filtered Agreements', color='#091f40')
            bars2 = ax.bar(x + width/2, stage_data["all_percentage"] * 100, width, 
                          label='All Agreements', color='#cccccc')
            
            # Add data labels if enabled
            if input.show_labels():
                for bars, labels in [(bars1, stage_data["filtered_label"]), (bars2, stage_data["all_label"])]:
                    for bar, label in zip(bars, labels):
                        height = bar.get_height()
                        ax.text(bar.get_x() + bar.get_width()/2, height + 1, label, 
                               ha='center', va='bottom', fontsize=10, fontweight='bold')
            
            ax.set_xticks(x)
            ax.set_xticklabels(stage_data["stage_label"])
            y_title = "Percentage of Agreements"
            
            # Legend at top, horizontal
            ax.legend(bbox_to_anchor=(0.5, 1.02), loc='lower center', ncol=2)
        
        ax.set_xlabel("Stage", fontsize=12)
        ax.set_ylabel(y_title, fontsize=12)
        ax.set_title("Agreements by Stage", fontsize=14, pad=20)
        ax.grid(axis='y', linestyle='--', alpha=0.3)
        ax.spines[['top', 'right']].set_visible(False)
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        return fig

    def get_topic_category_fig():
        by_cat = topic_category_data()
        
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # Sort and create horizontal bar chart
        by_cat_sorted = by_cat.sort_values("count")
        bars = ax.barh(by_cat_sorted["category"], by_cat_sorted["count"], color="#091f40")
        
        # Add value labels if enabled
        if input.show_labels():
            for bar in bars:
                width = bar.get_width()
                ax.text(width + max(by_cat_sorted["count"]) * 0.01, bar.get_y() + bar.get_height()/2, 
                       f'{int(width)}', ha='left', va='center', fontsize=9)
        
        ax.set_xlabel("Number of Agreements", fontsize=12)
        ax.set_ylabel("Topic Category", fontsize=12)
        ax.set_title("Agreements by Topic Category", fontsize=14, pad=20)
        plt.tight_layout()
        return fig

    def get_topic_stage_fig():
        grouped = topic_stage_data()
        
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # Create pivot table for stacked bar chart
        pivot_df = grouped.pivot(index="category", columns="stage_label", values="count").fillna(0)
        
        # Order stages if they exist in the data
        available_stages = [stage for stage in stage_order if stage in pivot_df.columns]
        other_stages = [stage for stage in pivot_df.columns if stage not in stage_order]
        pivot_df = pivot_df[available_stages + other_stages]
        
        # Create horizontal stacked bar chart
        pivot_df.plot(kind='barh', stacked=True, ax=ax, width=0.8)
        
        # Add data labels if enabled
        if input.show_labels():
            for container in ax.containers:
                ax.bar_label(container, label_type='center', fontsize=8)
        
        ax.set_xlabel("Number of Agreements", fontsize=12)
        ax.set_ylabel("Topic Category", fontsize=12)
        ax.set_title("Agreements by Topic and Stage", fontsize=14, pad=20)
        ax.legend(title="Stage", bbox_to_anchor=(0.5, 1.02), loc='lower center', ncol=len(pivot_df.columns))
        plt.tight_layout()
        return fig

    # EXPORT HANDLERS USING YOUR UTILITY FUNCTIONS
    # PNG exports
    # home_export_over_time_png = make_png_download(get_agreements_over_time_fig, "agreements_over_time.png")
    # home_export_grouped_over_time_png = make_png_download(get_grouped_over_time_fig, "grouped_over_time.png")
    # home_export_stage_png = make_png_download(get_agreements_by_stage_fig, "agreements_by_stage.png")
    # home_export_topic_cat_png = make_png_download(get_topic_category_fig, "topic_category.png")
    # home_export_topic_stage_png = make_png_download(get_topic_stage_fig, "topic_stage.png")
    
    # # CSV exports
    # home_export_over_time_csv = make_csv_download(agreements_over_time_data, "agreements_over_time.csv")
    # home_export_grouped_over_time_csv = make_csv_download(grouped_over_time_data, "grouped_over_time.csv")
    # home_export_stage_csv = make_csv_download(agreements_by_stage_data, "agreements_by_stage.csv")
    # home_export_topic_cat_csv = make_csv_download(topic_category_data, "topic_category.csv")
    # home_export_topic_stage_csv = make_csv_download(topic_stage_data, "topic_stage.csv")
    # Agreements Over Time
    output.home_export_over_time_png = make_png_download(
        get_agreements_over_time_fig, "agreements_over_time.png"
    )
    output.home_export_over_time_csv = make_csv_download(
        agreements_over_time_data, "agreements_over_time.csv"
    )
    
    # Grouped Over Time
    output.home_export_grouped_over_time_png = make_png_download(
        get_grouped_over_time_fig, "grouped_over_time.png"
    )
    output.home_export_grouped_over_time_csv = make_csv_download(
        grouped_over_time_data, "grouped_over_time.csv"
    )
    
    # Agreements by Stage
    output.home_export_stage_png = make_png_download(
        get_agreements_by_stage_fig, "agreements_by_stage.png"
    )
    output.home_export_stage_csv = make_csv_download(
        agreements_by_stage_data, "agreements_by_stage.csv"
    )
    
    # Topic Category
    output.home_export_topic_cat_png = make_png_download(
        get_topic_category_fig, "topic_category.png"
    )
    output.home_export_topic_cat_csv = make_csv_download(
        topic_category_data, "topic_category.csv"
    )
    
    # Topic Stage
    output.home_export_topic_stage_png = make_png_download(
        get_topic_stage_fig, "topic_stage.png"
    )
    output.home_export_topic_stage_csv = make_csv_download(
        topic_stage_data, "topic_stage.csv"
    )

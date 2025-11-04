# server/topics.py
from shiny import reactive, render, ui
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import io

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# Load data
pax = pd.read_csv(DATA_DIR / "pax.csv")
pax_topics = pd.read_csv(DATA_DIR / "pax_topics.csv")

def server(input, output, session):
    @reactive.effect
    def _():
        pp_choices = ["All"] + sorted(pax["PPName"].dropna().unique().tolist())
        ui.update_select("selected_pp", choices=pp_choices, selected="All")

    @reactive.calc
    def filtered_agreements():
        df = pax.copy()
        if input.selected_pp() and input.selected_pp() != "All":
            df = df[df["PPName"] == input.selected_pp()]
        return df

    @reactive.calc
    def filtered_topics():
        df = filtered_agreements()
        topics = pax_topics[pax_topics["value"] > 0]
        return topics[topics["AgtId"].isin(df["AgtId"])]

    @reactive.calc
    def topics_bar_data():
        df = filtered_topics()
        level = input.topic_level().lower()
        topic_col = {
            "category": "category",
            "issue": "issue",
            "sub-issue": "subissue"
        }[level]
        topic_counts = df.groupby(topic_col)["AgtId"].nunique().reset_index(name="count")
        topic_counts = topic_counts.sort_values("count")
        return topic_counts, topic_col

    @reactive.calc
    def topics_stage_data():
        df_agts = filtered_agreements()
        df_topics = filtered_topics()
        topic_col = {
            "category": "category",
            "issue": "issue",
            "sub-issue": "subissue"
        }[input.topic_level().lower()]
        
        merged = df_topics.merge(df_agts[["AgtId", "stage_label"]], on="AgtId")
        grouped = merged.groupby([topic_col, "stage_label"])["AgtId"].nunique().reset_index(name="count")
        return grouped, topic_col

    @reactive.calc
    def treemap_data():
        df = filtered_topics()
        topic_col = {
            "category": "category",
            "issue": "issue",
            "sub-issue": "subissue"
        }[input.topic_level().lower()]
        treemap_data = df.groupby(topic_col)["AgtId"].nunique().reset_index(name="count")
        return treemap_data, topic_col

    @reactive.calc
    def radial_data():
        df = filtered_topics()
        topic_col = {
            "category": "category",
            "issue": "issue",
            "sub-issue": "subissue"
        }[input.topic_level().lower()]
        grouped = df.groupby(topic_col)["AgtId"].nunique().reset_index(name="count")
        grouped = grouped.sort_values("count", ascending=False)
        return grouped, topic_col

    @render.text
    def pp_topic_summary():
        df = filtered_agreements()
        pp_name = input.selected_pp() if input.selected_pp() != "All" else "all peace processes"
        return f"{df['AgtId'].nunique()} agreements selected for: {pp_name}"

    @render.plot
    def topics_bar_chart():
        topic_counts, topic_col = topics_bar_data()
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Create horizontal bar chart
        bars = ax.barh(topic_counts[topic_col], topic_counts["count"], color="#091f40")
        
        # Add value labels if requested
        if input.show_data_labels():
            for bar in bars:
                width = bar.get_width()
                ax.text(width + max(topic_counts["count"]) * 0.01, 
                       bar.get_y() + bar.get_height()/2, 
                       f'{int(width)}', ha='left', va='center', fontsize=9)
        
        ax.set_xlabel("Number of Agreements")
        ax.set_ylabel(topic_col.title())
        ax.set_title(f"Agreements per {topic_col.title()}")
        plt.tight_layout()
        
        return fig

    @render.plot
    def topics_by_stage():
        grouped, topic_col = topics_stage_data()
        
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Create pivot table for stacked bar chart
        pivot_df = grouped.pivot(index=topic_col, columns="stage_label", values="count").fillna(0)
        
        # Create horizontal stacked bar chart
        pivot_df.plot(kind='barh', stacked=True, ax=ax, width=0.8)
        
        ax.set_xlabel("Number of Agreements")
        ax.set_ylabel(topic_col.title())
        ax.set_title(f"{topic_col.title()} by Stage")
        ax.legend(title="Stage", bbox_to_anchor=(1.05, 1), loc='upper left')
        
        plt.tight_layout()
        return fig

    @render.plot
    def topic_treemap():
        treemap_df, topic_col = treemap_data()
        
        # For matplotlib, we'll create a simple bar chart instead of treemap
        # (treemaps are complex in matplotlib)
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Sort by count and create vertical bar chart
        treemap_df_sorted = treemap_df.sort_values("count", ascending=True)
        
        bars = ax.barh(treemap_df_sorted[topic_col], treemap_df_sorted["count"], 
                      color=plt.cm.Blues(np.linspace(0.4, 0.8, len(treemap_df_sorted))))
        
        # Add value labels
        for bar in bars:
            width = bar.get_width()
            ax.text(width + max(treemap_df_sorted["count"]) * 0.01, 
                   bar.get_y() + bar.get_height()/2, 
                   f'{int(width)}', ha='left', va='center', fontsize=9)
        
        ax.set_xlabel("Number of Agreements")
        ax.set_ylabel(topic_col.title())
        ax.set_title(f"{topic_col.title()} Distribution")
        plt.tight_layout()
        
        return fig

    @render.plot
    def topic_radial_chart():
        grouped, topic_col = radial_data()
        
        # Create pie chart instead of radial chart
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Create pie chart
        wedges, texts, autotexts = ax.pie(grouped["count"], labels=grouped[topic_col], 
                                         autopct='%1.1f%%', startangle=90)
        
        ax.set_title(f"{topic_col.title()} Distribution")
        
        return fig

    # Export handlers with topics_ prefix
    @render.download(filename="topics_bar_chart.png")
    def topics_export_bar_png():
        fig = topics_bar_chart()
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=300, bbox_inches="tight")
        buf.seek(0)
        return buf

    @render.download(filename="topics_bar_chart.csv")
    def topics_export_bar_csv():
        topic_counts, _ = topics_bar_data()
        return topic_counts.to_csv(index=False)

    @render.download(filename="topics_by_stage.png")
    def topics_export_stage_png():
        fig = topics_by_stage()
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=300, bbox_inches="tight")
        buf.seek(0)
        return buf

    @render.download(filename="topics_by_stage.csv")
    def topics_export_stage_csv():
        grouped, _ = topics_stage_data()
        return grouped.to_csv(index=False)

    @render.download(filename="topic_treemap.png")
    def topics_export_treemap_png():
        fig = topic_treemap()
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=300, bbox_inches="tight")
        buf.seek(0)
        return buf

    @render.download(filename="topic_radial_chart.png")
    def topics_export_radial_png():
        fig = topic_radial_chart()
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=300, bbox_inches="tight")
        buf.seek(0)
        return buf
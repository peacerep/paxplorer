# server/actors.py
from shiny import reactive, render, ui
from shinywidgets import output_widget, render_widget
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
from pathlib import Path
import base64

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# Load data
sigs = pd.read_csv(DATA_DIR / "paax_signatory_v0.1_internal.csv")
actors = pd.read_csv(DATA_DIR / "paax_actors_v0.1_internal.csv")
paax = pd.read_csv(DATA_DIR / "paax_signatory_v0.1_internal.csv")
con_ent = pd.read_csv(DATA_DIR / "country_entity_geo_v9.csv")
pax = pd.read_csv(DATA_DIR / "pax_v9.csv")

stage_order = [
    'Pre-negotiation', 'Ceasefire', 'Framework-substantive, partial',
    'Framework-substantive, comprehensive', 'Implementation', 'Renewal', 'Other'
]

color_map = {
    'Intrastate': '#0b5740',
    'Interstate/mixed': '#ac4399',
    'Interstate': '#f28b20'
}

def server(input, output, session):
    # Populate dropdown
    @reactive.effect
    def _():
        actor_choices = sorted(sigs["actor_name"].dropna().unique().tolist())
        ui.update_select("selected_actor", choices=actor_choices)

    @reactive.calc
    def actor_filtered():
        actor = input.selected_actor()
        if not actor:
            return pd.DataFrame()
        
        actor_agts = sigs[sigs["actor_name"] == actor]["AgtId"].unique()
        df = paax[paax["AgtId"].isin(actor_agts)]
        
        if input.filter_practical_third():
            df = df[df["practical_third"] == 1]
        
        return df.drop_duplicates(subset="AgtId")

    @reactive.calc
    def agreement_types_data():
        df = actor_filtered()
        if df.empty:
            return pd.DataFrame()
        
        counts = df["agt_type"].value_counts().reset_index()
        counts.columns = ["Agreement Type", "Count"]
        counts["Color"] = counts["Agreement Type"].map(color_map).fillna("#999999")
        return counts

    @reactive.calc
    def temporal_data():
        actor = input.selected_actor()
        if not actor:
            return pd.DataFrame()
        
        df = actor_filtered()
        year_range = range(1990, 2024)
        actor_agts = df.groupby("year")["AgtId"].nunique().reindex(year_range, fill_value=0)
        
        data = pd.DataFrame({
            "Year": list(year_range),
            f"{actor} Agreements": actor_agts.values
        })
        return data

    @reactive.calc
    def stage_analysis_data():
        df = actor_filtered()
        if df.empty:
            return pd.DataFrame()
        
        stage_counts = df["stage_process"].value_counts().reindex(stage_order).fillna(0).reset_index()
        stage_counts.columns = ["Stage", "Count"]
        return stage_counts

    @reactive.calc
    def pp_counts_data():
        df = actor_filtered()
        if df.empty:
            return pd.DataFrame()
        
        counts = df["PPName"].value_counts().reset_index()
        counts.columns = ["Peace Process", "Number of Agreements"]
        return counts

    @reactive.calc
    def map_data():
        df = actor_filtered()
        if df.empty:
            return pd.DataFrame()
        
        iso_long = pd.melt(df, id_vars=["AgtId"], value_vars=["Loc1ISO", "Loc2ISO"]).dropna()
        iso_grouped = iso_long.groupby("value")["AgtId"].nunique().reset_index(name="Number of Agreements")
        geo = iso_grouped.merge(con_ent, left_on="value", right_on="iso_code", how="left").dropna(
            subset=["central_latitude", "central_longitude"]
        )
        return geo

    @reactive.calc
    def cosigning_matrix_data():
        df = actor_filtered()
        actor = input.selected_actor()
        if not actor or df.empty:
            return pd.DataFrame()
        
        actor_agts = sigs[sigs["actor_name"] == actor]["AgtId"].unique()
        co_df = sigs[sigs["AgtId"].isin(actor_agts)]
        
        co_counts = co_df[co_df["actor_name"] != actor].groupby("actor_name")["AgtId"].nunique()
        top_actors = co_counts.sort_values(ascending=False).head(input.top_n_cosigners()).index.tolist()
        
        matrix_df = co_df[co_df["actor_name"].isin(top_actors + [actor])]
        matrix = matrix_df.pivot_table(index="AgtId", columns="actor_name", aggfunc="size", fill_value=0)
        co_matrix = matrix.T @ matrix
        
        return co_matrix

    @render.text
    def actor_agreement_count():
        df = actor_filtered()
        actor_name = input.selected_actor() or "No actor selected"
        return f"Number of unique agreements for {actor_name}: {df['AgtId'].nunique()}"

    @render.plot
    def actor_agreement_types():
        counts = agreement_types_data()
        if counts.empty:
            fig, ax = plt.subplots()
            ax.text(0.5, 0.5, 'No data available', ha='center', va='center', transform=ax.transAxes)
            return fig
        
        fig, ax = plt.subplots()
        wedges, _ = ax.pie(
            counts["Count"],
            colors=counts["Color"],
            startangle=90,
            wedgeprops=dict(width=0.5)
        )
        ax.axis("equal")
        ax.legend(
            wedges,
            [f"{row['Agreement Type']} ({row['Count']})" for _, row in counts.iterrows()],
            title="Agreement Type",
            loc="center left",
            bbox_to_anchor=(1, 0.5)
        )
        return fig

    @render.plot
    def actor_agreements_over_time():
        data = temporal_data()
        actor = input.selected_actor()
        if data.empty or not actor:
            fig, ax = plt.subplots()
            ax.text(0.5, 0.5, 'No data available', ha='center', va='center', transform=ax.transAxes)
            return fig
        
        fig, ax = plt.subplots()
        ax.plot(data["Year"], data[f"{actor} Agreements"], marker='o', color="#091f40")
        
        for x, y in zip(data["Year"], data[f"{actor} Agreements"]):
            if y > 0:
                ax.text(x, y + 0.2, str(y), ha='center', va='bottom', fontsize=8)
        
        ax.set_ylim(0, data[f"{actor} Agreements"].max() + 2)
        ax.set_title(f"Number of Agreements Signed by {actor} per Year")
        ax.set_xlabel("Year")
        ax.set_ylabel("Number of Agreements")
        return fig

    @render.plot
    def actor_stage_analysis():
        stage_counts = stage_analysis_data()
        if stage_counts.empty:
            fig, ax = plt.subplots()
            ax.text(0.5, 0.5, 'No data available', ha='center', va='center', transform=ax.transAxes)
            return fig
        
        fig, ax = plt.subplots()
        bars = ax.bar(stage_counts["Stage"], stage_counts["Count"], color="#091f40")
        
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, height + 0.3, str(int(height)), ha='center', fontsize=8)
        
        ax.set_ylabel("Number of Agreements")
        ax.set_title("Agreements by Stage")
        plt.xticks(rotation=45, ha='right')
        return fig

    @render.plot
    def actor_pp_counts():
        counts = pp_counts_data()
        if counts.empty:
            fig, ax = plt.subplots()
            ax.text(0.5, 0.5, 'No data available', ha='center', va='center', transform=ax.transAxes)
            return fig
        
        fig, ax = plt.subplots()
        counts.sort_values("Number of Agreements").plot(
            kind="barh", x="Peace Process", y="Number of Agreements", color="#091f40", ax=ax
        )
        return fig

    @render_widget
    def actor_agreement_map():
        geo = map_data()
        if geo.empty:
            # Return empty plotly figure
            import plotly.graph_objects as go
            fig = go.Figure()
            fig.add_annotation(text="No geographic data available", 
                             xref="paper", yref="paper", 
                             x=0.5, y=0.5, showarrow=False)
            return fig
        
        fig = px.scatter_geo(
            geo,
            lat="central_latitude",
            lon="central_longitude",
            size="Number of Agreements",
            color_discrete_sequence=["#091f40"],
            projection="natural earth"
        )
        fig.update_layout(height=500)
        return fig

    @render.plot
    def actor_cosigning_matrix():
        co_matrix = cosigning_matrix_data()
        if co_matrix.empty:
            fig, ax = plt.subplots()
            ax.text(0.5, 0.5, 'No co-signing data available', ha='center', va='center', transform=ax.transAxes)
            return fig
        
        fig, ax = plt.subplots(figsize=(10, 8))
        sns.heatmap(co_matrix, annot=True, fmt="d", cmap="Blues", ax=ax)
        ax.set_title(f"Co-signing Matrix: {input.selected_actor()}")
        return fig

    @render.ui
    def actor_agreement_table():
        df = actor_filtered()
        if df.empty:
            return ui.p("No agreements found for selected actor.")
        
        df_table = df[["AgtId", "Con", "PPName", "agt_name", "PAX_Hyperlink", "PDF_Hyperlink"]].drop_duplicates()
        
        def linkify(val):
            if pd.isna(val) or val == "":
                return "N/A"
            return f'<a href="{val}" target="_blank">Link</a>'
        
        df_table["PAX_Hyperlink"] = df_table["PAX_Hyperlink"].apply(linkify)
        df_table["PDF_Hyperlink"] = df_table["PDF_Hyperlink"].apply(linkify)
        
        return ui.HTML(df_table.to_html(escape=False, index=False))

    # Export handlers with actors_ prefix
    @render.download(filename="actor_agreement_types.png")
    def actors_export_types_png():
        fig = actor_agreement_types()
        buf = BytesIO()
        fig.savefig(buf, format="png", dpi=300, bbox_inches="tight")
        buf.seek(0)
        return buf

    @render.download(filename="actor_agreement_types.csv")
    def actors_export_types_csv():
        data = agreement_types_data()
        return data.to_csv(index=False)

    @render.download(filename="actor_agreements_over_time.png")
    def actors_export_temporal_png():
        fig = actor_agreements_over_time()
        buf = BytesIO()
        fig.savefig(buf, format="png", dpi=300, bbox_inches="tight")
        buf.seek(0)
        return buf

    @render.download(filename="actor_agreements_over_time.csv")
    def actors_export_temporal_csv():
        data = temporal_data()
        return data.to_csv(index=False)

    @render.download(filename="actor_stage_analysis.png")
    def actors_export_stage_png():
        fig = actor_stage_analysis()
        buf = BytesIO()
        fig.savefig(buf, format="png", dpi=300, bbox_inches="tight")
        buf.seek(0)
        return buf

    @render.download(filename="actor_stage_analysis.csv")
    def actors_export_stage_csv():
        data = stage_analysis_data()
        return data.to_csv(index=False)

    @render.download(filename="peace_process_counts.png")
    def actors_export_pp_png():
        fig = actor_pp_counts()
        buf = BytesIO()
        fig.savefig(buf, format="png", dpi=300, bbox_inches="tight")
        buf.seek(0)
        return buf

    @render.download(filename="peace_process_counts.csv")
    def actors_export_pp_csv():
        data = pp_counts_data()
        return data.to_csv(index=False)

    @render.download(filename="map_data.csv")
    def actors_export_map_csv():
        data = map_data()
        return data.to_csv(index=False)

    @render.download(filename="cosigning_matrix.png")
    def actors_export_matrix_png():
        fig = actor_cosigning_matrix()
        buf = BytesIO()
        fig.savefig(buf, format="png", dpi=300, bbox_inches="tight")
        buf.seek(0)
        return buf

    @render.download(filename="cosigning_matrix.csv")
    def actors_export_matrix_csv():
        data = cosigning_matrix_data()
        return data.to_csv(index=False)
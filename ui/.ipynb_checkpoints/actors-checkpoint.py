# ui/actors.py
from shiny import ui

layout = ui.nav_panel(
    "Actors",
    ui.layout_sidebar(
        ui.sidebar(
            ui.h4("Filters"),
            ui.input_select("selected_actor", "Select an Actor", choices=[]),
            ui.input_checkbox("filter_practical_third", "Only show Practical Third", value=False),
            ui.input_slider("top_n_cosigners", "Top N Co-signers to Show", 3, 20, 10),
        ),
        # Main content section
        ui.div(
            ui.output_text("actor_agreement_count"),
            
            ui.h2("Agreement Types"),
            ui.output_plot("actor_agreement_types"),
            ui.div(
                ui.download_button("actors_export_types_png", "Export PNG", class_="btn btn-outline-primary btn-sm"),
                ui.download_button("actors_export_types_csv", "Export CSV", class_="btn btn-outline-secondary btn-sm"),
                class_="mb-3"
            ),
            ui.hr(),
            
            ui.h2("Agreements Over Time"),
            ui.output_plot("actor_agreements_over_time"),
            ui.div(
                ui.download_button("actors_export_temporal_png", "Export PNG", class_="btn btn-outline-primary btn-sm"),
                ui.download_button("actors_export_temporal_csv", "Export CSV", class_="btn btn-outline-secondary btn-sm"),
                class_="mb-3"
            ),
            ui.hr(),
            
            ui.h2("Stage Analysis"),
            ui.output_plot("actor_stage_analysis"),
            ui.div(
                ui.download_button("actors_export_stage_png", "Export PNG", class_="btn btn-outline-primary btn-sm"),
                ui.download_button("actors_export_stage_csv", "Export CSV", class_="btn btn-outline-secondary btn-sm"),
                class_="mb-3"
            ),
            ui.hr(),
            
            ui.h2("Agreements by Peace Process"),
            ui.output_plot("actor_pp_counts"),
            ui.div(
                ui.download_button("actors_export_pp_png", "Export PNG", class_="btn btn-outline-primary btn-sm"),
                ui.download_button("actors_export_pp_csv", "Export CSV", class_="btn btn-outline-secondary btn-sm"),
                class_="mb-3"
            ),
            ui.hr(),
            
            ui.h2("Agreement Locations"),
            ui.output_plot("actor_agreement_map"),
            ui.div(
                ui.download_button("actors_export_map_csv", "Export CSV", class_="btn btn-outline-secondary btn-sm"),
                class_="mb-3"
            ),
            ui.hr(),
            
            ui.h2("Co-signing Matrix"),
            ui.output_plot("actor_cosigning_matrix"),
            ui.div(
                ui.download_button("actors_export_matrix_png", "Export PNG", class_="btn btn-outline-primary btn-sm"),
                ui.download_button("actors_export_matrix_csv", "Export CSV", class_="btn btn-outline-secondary btn-sm"),
                class_="mb-3"
            ),
            ui.hr(),
            
            ui.h2("Agreements Signed by Actor"),
            ui.output_ui("actor_agreement_table")
        )
    )
)
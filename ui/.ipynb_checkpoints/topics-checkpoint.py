# ui/topics.py
from shiny import ui

layout = ui.nav_panel(
    "Topics",
    ui.layout_sidebar(
        ui.sidebar(
            ui.h4("Filters"),
            ui.input_select("selected_pp", "Select a Peace Process", choices=[]),
            ui.input_select("topic_level", "Topic Level", choices=["Category", "Issue", "Sub-issue"], selected="Category"),
            ui.input_checkbox("show_data_labels", "Show Data Labels", True)
        ),
        # Main content section
        ui.div(
            ui.output_text("pp_topic_summary"),
            
            ui.h2("Agreements per Topic"),
            ui.output_plot("topics_bar_chart"),
            ui.div(
                ui.download_button("topics_export_bar_png", "Export PNG", class_="btn btn-outline-primary btn-sm"),
                ui.download_button("topics_export_bar_csv", "Export CSV", class_="btn btn-outline-secondary btn-sm"),
                class_="mb-3"
            ),
            ui.hr(),
            
            ui.h2("Topics by Stage"),
            ui.output_plot("topics_by_stage"),
            ui.div(
                ui.download_button("topics_export_stage_png", "Export PNG", class_="btn btn-outline-primary btn-sm"),
                ui.download_button("topics_export_stage_csv", "Export CSV", class_="btn btn-outline-secondary btn-sm"),
                class_="mb-3"
            ),
            ui.hr(),
            
            ui.h2("Topic Treemap"),
            ui.output_plot("topic_treemap"),
            ui.div(
                ui.download_button("topics_export_treemap_png", "Export PNG", class_="btn btn-outline-primary btn-sm"),
                class_="mb-3"
            ),
            ui.hr(),
            
            ui.h2("Topic Radial Chart"),
            ui.output_plot("topic_radial_chart"),
            ui.div(
                ui.download_button("topics_export_radial_png", "Export PNG", class_="btn btn-outline-primary btn-sm"),
                class_="mb-3"
            )
        )
    )
)
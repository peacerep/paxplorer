# ui/home.py
from shiny import ui

layout = ui.nav_panel(
    "Overview",
    ui.layout_sidebar(
        # Sidebar section
        ui.sidebar(
            ui.h4("Filters"),
            ui.input_selectize("country", "Select Country", choices=[], multiple=True),
            ui.input_selectize("agt_type", "Select Agreement Type", choices=[], multiple=True),
            ui.input_checkbox("show_labels", "Show Data Labels", True),
            ui.input_action_button("reset_filters", "Reset Filters", class_="btn btn-secondary")
        ),
        # Main content section
        # In one of your UI files, temporarily add:
        ui.h1("TEST - DELETE THIS", style="color: red; background: yellow;"),
        ui.div(
            # First chart section
            ui.div(
                ui.h2("Agreements Over Time", style="margin-bottom: 15px;"),
                ui.input_radio_buttons("over_time_mode", "Select Mode", ["Number", "Percentage"]),
                ui.div(
                    ui.output_plot("agreements_over_time"), 
                    style="height: 500px; width: 100%; margin-bottom: 15px; padding-top: 20px;"
                ),
                ui.div(
                    ui.download_button("home_export_over_time_png", "Export PNG", class_="btn btn-outline-primary btn-sm me-2"),
                    ui.download_button("home_export_over_time_csv", "Export CSV", class_="btn btn-outline-secondary btn-sm"),
                    class_="mb-4"
                ),
                #style="margin-bottom: 40px;"
            ),
            
            ui.hr(),
            
            # Second chart section
            ui.div(
                ui.h2("Agreements by Stage or Type Over Time", style="margin-bottom: 15px;"),
                ui.input_radio_buttons("group_mode", "Select Grouping", ["Stage", "Agreement Type"]),
                ui.div(
                    ui.output_plot("grouped_over_time"), 
                    style="height: 500px; width: 100%; margin-bottom: 15px;padding-top: 20px;"
                ),
                ui.div(
                    ui.download_button("home_export_grouped_over_time_png", "Export PNG", class_="btn btn-outline-primary btn-sm me-2"),
                    ui.download_button("home_export_grouped_over_time_csv", "Export CSV", class_="btn btn-outline-secondary btn-sm"),
                    class_="mb-4"
                ),
                #style="margin-bottom: 40px;"
            ),
            
            ui.hr(),
            
            # Third chart section
            ui.div(
                ui.h2("Agreements by Stage", style="margin-bottom: 15px;"),
                ui.input_radio_buttons("stage_mode", "Select Metric", ["Count", "Percentage"]),
                ui.div(
                    ui.output_plot("agreements_by_stage"), 
                    style="height: 500px; width: 100%; margin-bottom: 15px;padding-top: 20px;"
                ),
                ui.div(
                    ui.download_button("home_export_stage_png", "Export PNG", class_="btn btn-outline-primary btn-sm me-2"),
                    ui.download_button("home_export_stage_csv", "Export CSV", class_="btn btn-outline-secondary btn-sm"),
                    class_="mb-4"
                ),
                #style="margin-bottom: 40px;"
            ),
            
            ui.hr(),
            
            # Fourth chart section
            ui.div(
                ui.h2("Agreements by Topic Category", style="margin-bottom: 15px; padding-bottom: 15px;"),
                ui.div(
                    ui.output_plot("topic_category_counts"), 
                    style="height: 500px; width: 100%; margin-bottom: 15px;padding-top: 20px;"
                ),
                ui.div(
                    ui.download_button("home_export_topic_cat_png", "Export PNG", class_="btn btn-outline-primary btn-sm me-2"),
                    ui.download_button("home_export_topic_cat_csv", "Export CSV", class_="btn btn-outline-secondary btn-sm"),
                    class_="mb-4"
                ),
               # style="margin-bottom: 40px;"
            ),
            
            ui.hr(),
            
            # Fifth chart section
            ui.div(
                ui.h2("Agreements by Topic and Stage", style="margin-bottom: 15px;"),
                ui.div(
                    ui.output_plot("topic_stage_stack"), 
                    style="height: 500px; width: 100%; margin-bottom: 15px;padding-top: 20px;"
                ),
                ui.div(
                    ui.download_button("home_export_topic_stage_png", "Export PNG", class_="btn btn-outline-primary btn-sm me-2"),
                    class_="mb-4"
                )
            ),
            
            # Add some bottom padding
            style="padding: 20px; max-width: 100%; overflow-x: auto;"
        )
    )
)
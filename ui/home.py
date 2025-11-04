# ui/home.py
from shiny import ui

layout = ui.nav_panel(
    "Overview",
    ui.layout_sidebar(
        # Sidebar section
        ui.sidebar(
            ui.h4("Agreement Filters"),
            ui.input_selectize(
                "region", 
                "Select Region:", 
                choices=[], 
                multiple=True,
                options={"placeholder": "All regions"}
            ),
            ui.input_selectize(
                "country", 
                "Select Country:", 
                choices=[], 
                multiple=True,
                options={"placeholder": "All countries"}
            ),
            ui.input_slider(
                "year_range",
                "Year Range:",
                min=1990,
                max=2024,
                value=[1990, 2024],
                step=1,
                sep=""
            ),            
            ui.input_selectize(
                "peace_process", 
                "Select Peace Process:", 
                choices=[], 
                multiple=True,
                options={"placeholder": "All peace processes"}
            ),
            ui.input_selectize(
                "stage", 
                "Select Stages:", 
                choices=[], 
                multiple=True,
                options={"placeholder": "All stages"}
            ),
            ui.input_selectize(
                "agt_type", 
                "Select Agreement Type:", 
                choices=[], 
                multiple=True,
                options={"placeholder": "All agreement types"}
            ),
            #ui.input_checkbox("show_labels", "Show Data Labels", True),
            ui.input_action_button("reset_filters", "Reset Filters", class_="btn btn-secondary"),
            ui.hr(),
            ui.h4("Applied Filters", class_="mb-2"),
            ui.div(
                ui.output_ui("applied_filters_display"),
                class_="mb-3",
                style="font-size: 0.9em; background-color: #f8f9fa; padding: 10px; border-radius: 5px; border-left: 4px solid #007bff;"
            ),
            ui.div(
                ui.output_ui("filter_summary"),
                class_="mb-3",
                style="font-size: 0.85em; color: #666;"
            ),
            class_="sidebar"
        ),

        # === Main content section ===
        ui.div(
            # Intro block
            ui.div(
                ui.h2(
                    "PA-Xplorer: Explore Trends in PA-X Database",
                    style="color: #091f40; font-family: 'Montserrat', sans-serif; margin-bottom: 20px;"
                ),
                 ui.p(
                    "This application allows you to explore PA-X data and export relevant charts and summarised data for re-use. Explore global trends in peace agreements, agreements by peace processes, topics in agreements and the actors who sign agreements as parties and third parties. " ,
                    style="margin-bottom: 10px; font-size: 1em; color: #333;"
                ),
                ui.p(
                    "On this page you can look at trends in peace agreements since 1990. "
                    "The default view of charts show all agreements from version 9 of the PA-X Peace Agreements Database. The agreements can be filtered using the filters in the sidebar. "
                    "Please cite the data as shown below, and we kindly ask if you do not remove our branding in the images when using exported charts:" ,
                    style="margin-bottom: 10px; font-size: 1em; color: #333;"
                ),
                ui.p(
                    "Bell, C., & Badanjak, S. (2019). Introducing PA-X: A new peace agreement database and dataset. Journal of Peace Research, 56(3), 452-466. Available at ",
                    ui.HTML(
                        '<a href="https://www.peaceagreements.org/" target="_blank">www.peaceagreements.org</a>.'
                    ),
                     style="font-style: italic; color: #555; font-size: 0.9em; margin-top: 8px;"
                ),
                style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 30px;"
            ),

            ui.hr(),

            # --- 1. Agreements over time ---
            ui.div(
                ui.h2("Agreements Over Time", style="margin-bottom: 15px;"),
                ui.p(
                    "This chart shows the number of agreements in PA-X per year. " \
                    "Use the filters in the sidebar to see the trends over time for particular countries/peace processes, or to see trends in different agreement types or stages over time. "
                    "If select any filters, view as percentage to see the proportion of agreements per year for the selection of data. "
                ),
                ui.p(
                    "Example use: select 'framework-substantive, comprehensive in the 'stage' filter to see how they have been declining in the 2010's. ", 
                     style="font-style: italic; color: #555; font-size: 0.9em; margin-top: 8px;"
                ),
                ui.input_radio_buttons("over_time_mode", "Show as :", ["Number", "Percentage"]),
                ui.output_plot("agreements_over_time", height="650px"),
                ui.div(
                    ui.download_button("home_export_over_time_png", "Export PNG", class_="btn btn-outline-primary btn-sm me-2"),
                    ui.download_button("home_export_over_time_csv", "Export CSV", class_="btn btn-outline-secondary btn-sm"),
                    class_="mb-4"
                ),
            ),

            ui.hr(),

            # --- 2. Agreements by Stage or Type Over Time ---
            ui.div(
                ui.h2("Agreements by Stage or Type Over Time", style="margin-bottom: 15px;"),
                ui.p(
                    "This chart shows the number of agreements in PA-X per year, by agreement type or stage. " \
                    "Use the filters in the sidebar to see the trends over time for particular countries or peace processes, with agreement types or stages over time. "
                ),
                ui.p(
                    "Example use: select to view by 'Agreement Type' to see how local agreements are more prevalent in recent years. Filter by region to see where these trends come from - Africa has many local agreements in PA-X Local. ", 
                     style="font-style: italic; color: #555; font-size: 0.9em; margin-top: 8px;"
                ),
                ui.input_radio_buttons("group_mode", "View agreements over time by:", ["Stage", "Agreement Type"]),
                ui.output_plot("grouped_over_time", height="650px"),
                ui.div(
                    ui.download_button("home_export_grouped_over_time_png", "Export PNG", class_="btn btn-outline-primary btn-sm me-2"),
                    ui.download_button("home_export_grouped_over_time_csv", "Export CSV", class_="btn btn-outline-secondary btn-sm"),
                    class_="mb-4"
                ),
            ),

            ui.hr(),

            # --- 3. Agreements by Stage ---
            ui.div(
                ui.h2("Agreements by Stage", style="margin-bottom: 15px;"),
                ui.p(
                    "This chart shows the number of agreements in PA-X per stage of process. " \
                    "Use the filters in the sidebar to see the trends in particular time-frames, regions or agreement types. See how the selected filters compare to proportions for all of PA-X. "
                ),
                ui.p(
                    "Example use: see how intrastate agreements are more commonly signed at the pre-negotiation stage and less common at ceasefire, compared to other agreement types. ", 
                     style="font-style: italic; color: #555; font-size: 0.9em; margin-top: 8px;"
                ),
                ui.input_radio_buttons("stage_mode", "Select Metric", ["Count", "Percentage"]),
                ui.output_plot("agreements_by_stage", height="650px"),
                ui.div(
                    ui.download_button("home_export_stage_png", "Export PNG", class_="btn btn-outline-primary btn-sm me-2"),
                    ui.download_button("home_export_stage_csv", "Export CSV", class_="btn btn-outline-secondary btn-sm"),
                    class_="mb-4"
                ),
            ),

            ui.hr(),

            # --- 4. Agreements by Topic Category ---
            ui.div(
                ui.h2("Agreements by Topic Category", style="margin-bottom: 15px; padding-bottom: 15px;"),
                ui.p(
                    "This chart shows the number of agreements in PA-X per topic category. " \
                    "Use the filters in the sidebar to see the trends in particular time-frames, regions or agreement types. Deep dive in to topics on the 'Topics' page at the top of the page. "
                ),
                ui.p(
                    "Example RQ: is Security Sector always the topic with the most agreements? ", 
                     style="font-style: italic; color: #555; font-size: 0.9em; margin-top: 8px;"
                ),
                ui.output_plot("topic_category_counts", height="650px"),
                ui.div(
                    ui.download_button("home_export_topic_cat_png", "Export PNG", class_="btn btn-outline-primary btn-sm me-2"),
                    ui.download_button("home_export_topic_cat_csv", "Export CSV", class_="btn btn-outline-secondary btn-sm"),
                    class_="mb-4"
                ),
            ),

            ui.hr(),
            style="padding: 20px; max-width: 100%; overflow-x: auto;"
        ),
    )
)

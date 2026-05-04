from shiny import ui
from shinywidgets import output_widget

layout = ui.nav_panel(
    "Topics",
    ui.layout_sidebar(
        ui.sidebar(
            ui.h4("Agreement Filters"),
            ui.input_checkbox(
                "topics_exclude_local_analysis",
                "Exclude Local agreements",
                False
            ),
            ui.input_selectize(
                "topics_region",
                "Select Region:",
                choices=[],
                multiple=True,
                options={"placeholder": "All regions"}
            ),
            ui.input_selectize(
                "topics_country",
                "Select Country:",
                choices=[],
                multiple=True,
                options={"placeholder": "All countries"}
            ),
            ui.input_selectize(
                "topics_agt_type",
                "Select Agreement Type:",
                choices=[],
                multiple=True,
                options={"placeholder": "All agreement types"}
            ),
            ui.input_slider(
                "topics_year_range",
                "Year Range:",
                min=1990,
                max=2025,
                value=[1990, 2025],
                step=1,
                sep=""
            ),
            ui.input_selectize(
                "topics_peace_process",
                "Select Peace Process:",
                choices=[],
                multiple=True,
                options={"placeholder": "All peace processes"}
            ),
            ui.input_selectize(
                "topics_stage",
                "Select Stages:",
                choices=[],
                multiple=True,
                options={"placeholder": "All stages"}
            ),
            ui.input_action_button(
                "topics_reset_filters_general",
                "Reset Filters",
                class_="btn btn-secondary"
            ),
            ui.hr(),
            ui.h4("Applied Filters", class_="mb-2"),
            ui.div(
                ui.output_ui("topics_applied_filters_display"),
                class_="mb-3",
                style="font-size: 0.9em; background-color: #f8f9fa; padding: 10px; border-radius: 5px; border-left: 4px solid #007bff;"
            ),
            class_="sidebar"
        ),
        ui.div(
            ui.div(
                ui.h2(
                    "Explore Topics in Peace Agreements",
                    style="color: #091f40; font-family: 'Montserrat', sans-serif; margin-bottom: 20px;"
                ),
                ui.p(
                    "On this page you can explore peace agreements by the topics that are included in the text. "
                    "The topics in PA-X are coded manually by an expert team at the University of Edinburgh. "
                    "The topics coded are outlined in the ",
                    ui.HTML(
                        '<a href="https://www.peaceagreements.org/cms/documents/3956/PA_X_codebook_v10.pdf" target="_blank">PA-X Codebook</a>.'
                    ),
                    style="margin-bottom: 10px; font-size: 1em; color: #333;"
                ),
                ui.hr(),
                ui.div(
                    ui.h5("Select Topics to Analyse:", style="margin-bottom: 10px;"),
                    ui.input_selectize(
                        "selected_topics",
                        None,
                        choices=[],
                        selected=[],
                        multiple=True,
                        options={
                            "placeholder": "Choose topic categories, issues, or sub-issues...",
                            "maxItems": 10
                        },
                        width="100%"
                    ),
                    ui.div(
                        ui.input_switch(
                            "topics_match_mode",
                            "Show agreements that contain ALL selected topics ('AND' logic)",
                            value=False
                        ),
                        ui.tags.span(
                            "When switch is off: agreements with ANY of the selected topics are shown ('OR' logic). When on: agreements must include ALL selected topics ('AND' logic).",
                            style="margin-left: 10px; font-size: 0.85em; color: #555;"
                        ),
                        style="margin-top: 10px; margin-bottom: 15px;"
                    ),
                    ui.div(
                        ui.input_action_button(
                            "topics_reset_filters",
                            "Reset Topic Filters",
                            class_="btn btn-outline-danger me-3"
                        ),
                        ui.div(
                            ui.output_ui("topics_summary_stats"),
                            style="display: inline-block; margin-left: 20px; font-size: 0.9em;"
                        ),
                        style="margin-top: 10px; display: flex; align-items: center;"
                    )
                ),
                style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 30px;"
            ),

            ui.div(
                ui.div(
                    ui.h2("Locations of Agreements", style="margin-bottom: 15px;"),
                    ui.p(
                        "This map shows the number of peace agreements that mention the selected topics by location. Hover over a circle to see the number of agreements and location name. "
                        "Please note, the location is the central point of the related conflict country and is not indicative of where exactly the agreement covers.",
                        class_="text-muted mb-4"
                    ),
                    ui.p(
                        "Example use: are there regional trends in certain topics addressed in peace agreements? ",
                        style="font-style: italic; color: #555; font-size: 0.9em; margin-top: 8px;"
                    ),
                    ui.div(
                        output_widget("topics_map"),
                        style="height: 500px; width: 100%; margin-bottom: 15px;"
                    ),
                    ui.div(
                        ui.download_button("topics_export_map_csv", "Export CSV", class_="btn btn-outline-secondary btn-sm"),
                        class_="mb-4"
                    ),
                    style="margin-bottom: 40px;"
                ),

                ui.hr(),

                ui.div(
                    ui.h2("Agreements Over Time", style="margin-bottom: 15px;"),
                    ui.p(
                        "This chart allows you to see trends in when this topic was addressed over time. View as a percentage of all agreements signed that year to see if there are certain years a high or low proportion of agreements included the issues. ",
                        class_="text-muted mb-4"
                    ),
                    ui.p(
                        "Example use: has there been more inclusion of Women, Girls and Gender since UNSCR 1325 in 2000? See more on this question through this scrollytelling visualization: ",
                        ui.HTML(
                            '<a href="https://www.peaceagreements.org/visualizations/gender-vis/" target="_blank">Insights from PA-X Gender</a>.'
                        ),
                        style="font-style: italic; color: #555; font-size: 0.9em; margin-top: 8px;"
                    ),
                    ui.input_radio_buttons("topics_time_mode", "Show as", ["Count", "Percentage"]),
                    ui.div(
                        ui.output_plot("topics_over_time", height="650px")
                    ),
                    ui.div(
                        ui.div(
                            ui.download_button("topics_export_time_png", "Export PNG", class_="btn btn-outline-primary btn-sm"),
                            ui.download_button("topics_export_time_csv", "Export CSV", class_="btn btn-outline-secondary btn-sm"),
                            style="display:flex; gap:10px; align-items:center;"
                        ),
                        ui.div(
                            ui.input_text(
                                "topics_custom_title_over_time",
                                None,
                                placeholder="Enter custom chart title…",
                                width="320px",
                            ),
                            style="margin-left:auto;"
                        ),
                        style="display:flex; align-items:center; gap:16px;",
                        class_="mb-4"
                    ),
                    style="margin-bottom: 40px;"
                ),

                ui.hr(),

                ui.div(
                    ui.h2("Agreements by Stage or Type Over Time", style="margin-bottom: 15px;"),
                    ui.p(
                        "This chart allows you to see the number of agreements with the selected topic per year, by the agreement stage or type. ",
                        class_="text-muted mb-4"
                    ),
                    ui.p(
                        "Example use: are there topics that are consistent in comprehensive agreements or has this changed over time? ",
                        style="font-style: italic; color: #555; font-size: 0.9em; margin-top: 8px;"
                    ),
                    ui.input_radio_buttons("topics_group_mode", "Show bars by:", ["Stage", "Agreement Type"]),
                    ui.div(
                        ui.output_plot("topics_grouped_over_time", height="650px"),
                    ),
                    ui.div(
                        ui.div(
                            ui.download_button("topics_export_grouped_time_png", "Export PNG", class_="btn btn-outline-primary btn-sm"),
                            ui.download_button("topics_export_grouped_time_csv", "Export CSV", class_="btn btn-outline-secondary btn-sm"),
                            style="display:flex; gap:10px; align-items:center;"
                        ),
                        ui.div(
                            ui.input_text(
                                "topics_custom_title_grouped",
                                None,
                                placeholder="Enter custom chart title…",
                                width="320px",
                            ),
                            style="margin-left:auto;"
                        ),
                        style="display:flex; align-items:center; gap:16px;",
                        class_="mb-4"
                    ),
                    style="margin-bottom: 40px;"
                ),

                ui.hr(),

                ui.div(
                    ui.h2("Agreements by Stage", style="margin-bottom: 15px;"),
                    ui.p(
                        "This chart allows you to see the number of agreements per stage for the selected topic(s). Show by percentage to compare to see if the topic is more commmonly addressed at particular stages of processes. ",
                        class_="text-muted mb-4"
                    ),
                    ui.p(
                        "Example use: are there topics more common at earlier stages in the process? ",
                        style="font-style: italic; color: #555; font-size: 0.9em; margin-top: 8px;"
                    ),
                    ui.input_radio_buttons("topics_stage_mode", "Select Metric", ["Count", "Percentage"]),
                    ui.div(
                        ui.output_plot("topics_by_stage", height="650px"),
                    ),
                    ui.div(
                        ui.div(
                            ui.download_button("topics_export_stage_png", "Export PNG", class_="btn btn-outline-primary btn-sm"),
                            ui.download_button("topics_export_stage_csv", "Export CSV", class_="btn btn-outline-secondary btn-sm"),
                            style="display:flex; gap:10px; align-items:center;"
                        ),
                        ui.div(
                            ui.input_text(
                                "topics_custom_title_stage",
                                None,
                                placeholder="Enter custom chart title…",
                                width="320px",
                            ),
                            style="margin-left:auto;"
                        ),
                        style="display:flex; align-items:center; gap:16px;",
                        class_="mb-4"
                    ),
                    style="margin-bottom: 40px;"
                ),

                ui.hr(),

                ui.div(
                    ui.h2("Peace Processes with Selected Topics", style="margin-bottom: 15px;"),
                    ui.p(
                        "This shows the top peace processes containing agreements with the selected topics, by number of agreements. Use the stage toggle to break the chart down by stage of process.",
                        class_="text-muted"
                    ),
                    ui.p(
                        "Example use: are there processes where these topics are concentrated in particular stages, or appear repeatedly across a process?",
                        style="font-style: italic; color: #555; font-size: 0.9em; margin-top: 8px;"
                    ),
                    ui.input_slider(
                        "topics_top_processes",
                        "Show Top N Peace Processes",
                        min=5,
                        max=50,
                        value=20,
                        step=1,
                        width="50%"
                    ),
                    ui.input_checkbox("topics_show_stage_legend", "Show by Stage of Process", False),
                    ui.div(
                        ui.output_plot("topics_by_peace_process", height="650px"),
                    ),
                    ui.div(
                        ui.div(
                            ui.download_button("topics_export_pp_png", "Export PNG", class_="btn btn-outline-primary btn-sm"),
                            ui.download_button("topics_export_pp_csv", "Export CSV", class_="btn btn-outline-secondary btn-sm"),
                            style="display:flex; gap:10px; align-items:center;"
                        ),
                        ui.div(
                            ui.input_text(
                                "topics_custom_title_pp",
                                None,
                                placeholder="Enter custom chart title…",
                                width="320px",
                            ),
                            style="margin-left:auto;"
                        ),
                        style="display:flex; align-items:center; gap:16px;",
                        class_="mb-4"
                    ),
                    style="margin-bottom: 40px;"
                ),

                ui.hr(),

                ui.div(
                    ui.h2("Signatories to Agreements with Selected Topics", style="margin-bottom: 15px;"),
                    ui.p(
                        "This shows the top party and third party signatories by number of agreements with the selected topics included. Use the slider to increase the number shown. ",
                        class_="text-muted mb-3"
                    ),
                    ui.p(
                        "Example use: are there particular actors that sign agreements with these selected topics? ",
                        style="font-style: italic; color: #555; font-size: 0.9em; margin-top: 8px;"
                    ),
                    ui.input_slider("topics_top_actors", "Show Top N Actors", min=5, max=30, value=15, step=1, width="50%"),
                    ui.div(
                        ui.h4("Party Signatories to Agreements", class_="mb-3"),
                        ui.output_plot("topics_party_actors", height="600px"),
                        ui.div(
                            ui.div(
                                ui.download_button("topics_export_party_actors_png", "Export PNG", class_="btn btn-outline-primary btn-sm"),
                                ui.download_button("topics_export_party_actors_csv", "Export CSV", class_="btn btn-outline-secondary btn-sm"),
                                style="display:flex; gap:10px; align-items:center;"
                            ),
                            ui.div(
                                ui.input_text(
                                    "topics_custom_title_party",
                                    None,
                                    placeholder="Enter custom chart title…",
                                    width="320px",
                                ),
                                style="margin-left:auto;"
                            ),
                            style="display:flex; align-items:center; gap:16px;",
                            class_="mb-4"
                        ),
                        class_="mb-4"
                    ),
                    ui.hr(),
                    ui.div(
                        ui.h4("Third-Party signatories to Agreements", class_="mb-3"),
                        ui.output_plot("topics_third_actors", height="600px"),
                        ui.div(
                            ui.div(
                                ui.download_button("topics_export_third_actors_png", "Export PNG", class_="btn btn-outline-primary btn-sm"),
                                ui.download_button("topics_export_third_actors_csv", "Export CSV", class_="btn btn-outline-secondary btn-sm"),
                                style="display:flex; gap:10px; align-items:center;"
                            ),
                            ui.div(
                                ui.input_text(
                                    "topics_custom_title_third",
                                    None,
                                    placeholder="Enter custom chart title…",
                                    width="320px",
                                ),
                                style="margin-left:auto;"
                            ),
                            style="display:flex; align-items:center; gap:16px;",
                            class_="mb-4"
                        ),
                        class_="mb-4"
                    ),
                    style="margin-bottom: 40px;"
                ),

                ui.hr(),

                ui.output_ui("single_topic_analysis_section"),

                ui.hr(),

                style="padding: 20px; max-width: 100%; overflow-x: auto;"
            )
        )
    )
)
from shiny import ui

layout = ui.nav_panel(
    "Peace Process",
    ui.layout_sidebar(
        # Sidebar section - matching home page structure
        ui.sidebar(
            ui.h4("Agreement Filters"),
            ui.input_date_range("pp_date_range", "Date Range:", start=None, end=None),
            ui.input_slider("pp_year_range", "Year Range:", min=1990, max=2024, value=[1990, 2024], step=1, sep=""),
            ui.input_selectize("pp_stage", "Select Stages:", choices=[], multiple=True, options={"placeholder": "All stages"}),
            ui.input_selectize("pp_agt_type", "Select Agreement Type:", choices=[], multiple=True, options={"placeholder": "All agreement types"}),
            ui.input_checkbox("pp_show_labels", "Show Data Labels", True),
            ui.input_action_button("pp_reset_filters", "Reset Filters", class_="btn btn-secondary"),
            ui.hr(),
            ui.h4("Applied Filters", class_="mb-2"),
            ui.div(
                ui.output_ui("pp_applied_filters"),
                class_="mb-3",
                style="font-size: 0.9em; background-color: #f8f9fa; padding: 10px; border-radius: 5px; border-left: 4px solid #007bff;"
            ),
            ui.div(
                ui.output_ui("pp_filter_summary"),
                class_="mb-3",
                style="font-size: 0.85em; color: #666;"
            ),
            class_="sidebar"
        ),

        # Main content area (no extra outer div wrapping this)
        ui.div(
            ui.h2("Explore a Peace Process", style="color: #091f40; margin-bottom: 20px;"),
            ui.p(
                "On this page you can select a peace process and explore the different dimensions of PA-X data. "
                "Use the filters in the sidebar to filter by date, stage or type of agreements in the selected process. The view on PA-X button will open the PA-X Search results for the selected peace process, where you can then access the agreement full text/pdfs.",
                style="margin-bottom: 10px; font-size: 1em; color: #333;"
            ),
            ui.p(" "),
            # Peace Process selection and summary row
            ui.row(
                ui.column(6,
                    ui.h5("Select Peace Process:", style="margin-bottom: 10px;"),
                    ui.input_selectize(
                        "selected_peace_process",
                        None,
                        choices=[],
                        selected=None,
                        multiple=False,
                        options={"placeholder": "Choose a peace process"},
                        width="100%"
                    )
                ),
                ui.column(3,
                    ui.div(
                        ui.output_ui("pp_summary_stats"),
                        style="padding-top: 25px;"
                    )
                ),
                ui.column(3,
                    ui.div(
                        ui.output_ui("pp_database_link"),
                        style="padding-top: 25px;"
                    )
                ),
            ),
            style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 30px;"
        ),

        # Agreements Over Time - matching home page layout
        ui.div(
            ui.h2("Agreements by Stage Over Time", style="margin-bottom: 15px;"),
            ui.div(
                ui.p(
                    "This chart shows the number of agreements in the selected process by stage over time. "
                    "Toggle between viewing by year or month to see temporal trends of agreement stages."
                ),
                ui.p(
                    "To look at: are there periods of back and forth in process stages over time? For example, after an implementation agreement is signed are there any subsequent pre-negotiation/process or ceasefire agreements?",
                    style="font-style: italic; color: #555; font-size: 0.9em; margin-top: 8px;"
                ),
                ui.input_radio_buttons(
                    "pp_time_granularity",
                    "Time Granularity:",
                    choices={"year": "Year", "month": "Month"},
                    selected="year",
                    inline=True
                ),
                style="margin-bottom: 15px;"
            ),
            ui.div(
                ui.output_plot("pp_agreements_over_time", height="725px")
            ),
            ui.div(
                ui.download_button("pp_export_time_png", "Export PNG", class_="btn btn-outline-primary btn-sm me-2", style="margin-right: 10px;"),
                ui.download_button("pp_export_time_csv", "Export CSV", class_="btn btn-outline-secondary btn-sm"),
                class_="mb-4"
            ),
        ),
        ui.hr(),
        ui.div(
            ui.h2("Agreement Stages in Process", style="color: #091f40; margin-bottom: 15px;"),
            ui.div(
                ui.p(
                    "This chart compares the proportion of agreements in the selected process signed at a particular stage, to the overall proportion of agreements in PA-X that are signed at that stage."
                ),
                ui.p(
                    "Example use: for this process which stage is more common than other processes to have agreements signed at?",
                    style="font-style: italic; color: #555; font-size: 0.9em; margin-top: 8px;"
                ),
                ui.div(
                    ui.div(
                        ui.output_plot("pp_stage_analysis", height="900px"),
                        style="margin-bottom: 20px;"
                    ),
                    ui.div(
                        ui.div(
                            ui.download_button("pp_export_stage_png", "Download PNG",
                                               class_="btn btn-outline-primary btn-sm me-2", style="margin-right: 10px;"),
                            ui.download_button("pp_export_stage_csv", "Download CSV",
                                               class_="btn btn-outline-secondary btn-sm"),
                            class_="mb-4"
                        )
                    )
                ),
            )
        ),
        ui.hr(),
        # Messy timeline iFrame
        ui.div(
            ui.h2("Messy Timeline", style="margin-bottom: 15px;"),
            ui.div(
                ui.p(
                    "This shows the trajectory of the peace process, if following the expected order of stages. "
                    "View the visualization in full screen and explore other processes: https://www.peaceagreements.org/visualizations/messy-peace-processes/"
                ),
                ui.p(
                    "Example use: explore to see if any process follows the 'ideal' trajectory of negotiations.",
                    style="font-style: italic; color: #555; font-size: 0.9em; margin-top: 8px;"
                ),
            ),
            ui.div(
                ui.output_ui("external_viz_iframe"),
                style="height: 750px; width: 100%; margin-bottom: 15px; border: 1px solid #ddd; border-radius: 4px;"
            ),
        ),
        ui.hr(),
        # Signatories Analysis
        ui.div(
            ui.h2("Signatories to Agreements", style="color: #091f40; margin-bottom: 15px;"),
            ui.p("The charts below outline the party and third party signatories to agreements in the selected peace process."),
            ui.p(
                "Example use: are there any party or third party signatories that sign all (i.e. 100%) of agreements in this process?",
                style="font-style: italic; color: #555; font-size: 0.9em; margin-top: 8px;"
            ),
            ui.div(
                ui.div(
                    ui.input_radio_buttons(
                        "pp_signatory_mode",
                        "Show data as:",
                        choices={"count": "Number of Agreements", "percentage": "Percentage of Agreements"},
                        selected="count",
                        inline=True
                    ),
                    style="margin-bottom: 15px;"
                ),
                ui.div(
                    ui.row(
                        ui.row(
                            ui.h5("Party Signatories", style="text-align: center; margin-bottom: 10px;"),
                            ui.p("Parties are those who directly sign the agreement - often parties to the conflict and their regional allies."),
                            ui.div(
                                ui.output_plot("pp_party_signatories", width="100%", height="800px"),
                                class_="plot-output"
                            ),
                            ui.div(
                                ui.download_button("pp_export_party_sig_png", "Download PNG",
                                                   class_="btn btn-outline-primary btn-sm me-2", style="margin-right: 10px;"),
                                ui.download_button("pp_export_sig_csv", "Download CSV",
                                                   class_="btn btn-outline-secondary btn-sm"),
                                style="margin-top: 15px;"
                            ),
                            style="margin-bottom: 15px;"
                        ),
                        ui.hr(),
                        ui.row(
                            ui.h5("Third Party Signatories", style="text-align: center; margin-bottom: 10px;"),
                            ui.p("Third parties directly sign the agreement, but are third party to the conflict and have roles as mediators, guarantors or witnesses."),
                            ui.div(
                                ui.output_plot("pp_third_party_signatories", width="1000px", height="800px"),
                                class_="plot-output"
                            ),
                            ui.div(
                                ui.download_button("pp_export_third_party_sig_png", "Download PNG",
                                                   class_="btn btn-outline-primary btn-sm me-2", style="margin-right: 10px;"),
                                ui.download_button("pp_export_third_party_sig_csv", "Download CSV",
                                                   class_="btn btn-outline-secondary btn-sm"),
                                style="margin-top: 15px;"
                            )
                        )
                    )
                )
            ),
        ),
        ui.hr(),
        # Topics Analysis
        ui.div(
            ui.h3("Topics Analysis", style="color: #091f40; margin-bottom: 15px;"),
            ui.p(
                "The charts below outline show the most common issues in agreements for the selected process. Click to show by stage to see the stages when these topics are most prevalent."
            ),
            ui.p(
                "Example Q: are ceasefire provisions only included in ceasefire agreements?",
                style="font-style: italic; color: #555; font-size: 0.9em; margin-top: 8px;"
            ),
            ui.div(
                ui.div(
                    ui.input_checkbox("pp_topics_show_stage_legend", "Show stage breakdown", False),
                    style="margin-bottom: 15px;"
                ),
                ui.div(
                    ui.output_plot("pp_topics_issues_chart", height="1400px"),
                    style="margin-bottom: 20px;"
                ),
                ui.div(
                    ui.div(
                        ui.download_button("pp_export_topic_issues_png", "Export PNG",
                                           class_="btn btn-outline-primary btn-sm me-2", style="margin-right: 10px;"),
                        ui.download_button("pp_export_topic_issues_csv", "Export CSV",
                                           class_="btn btn-outline-secondary btn-sm"),
                        class_="mb-4"
                    )
                )
            )
        ),
        ui.hr(),
        # Diffusion Analysis (updated with radio buttons)
        ui.div(
            ui.h3("Diffusion Analysis", style="color: #091f40; margin-bottom: 15px;"),
            ui.p(
                "This chart shows how actors or issues have appeared in the process in agreements over time. Toggle the chart between viewing actors or topics along the y axis. Switch the x axis to view agreements in order, or dates of agreements."
            ),
            ui.p(
                "Example use: are there topics that are persistent across the entire process, or are they addressed at later points? When do third party signatories get involved? Do they co-incide with any particular issues?",
                style="font-style: italic; color: #555; font-size: 0.9em; margin-top: 8px;"
            ),
            ui.div(
                # === Top Control Area ===
                ui.div(
                    ui.input_radio_buttons(
                        "pp_diffusion_type",
                        "View by:",
                        choices={"actors": "Actors", "topics": "Topics"},
                        selected="actors",
                        inline=True
                    ),
                    ui.panel_conditional(
                        "input.pp_diffusion_type == 'topics'",
                        ui.input_radio_buttons(
                            "pp_diffusion_topic_level",
                            "Topic Level:",
                            choices={"issues": "Issues", "subissues": "Sub-issues"},
                            selected="issues",
                            inline=True
                        ),
                        style="margin-left: 20px;"
                    ),
                    style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; margin-bottom: 15px;"
                ),
                # === Chart Area ===
                ui.div(
                    ui.output_plot("pp_diffusion_chart", height="1200px", width="100%"),
                    style="overflow-x:auto; padding-left:20px;"
                ),
                # === Bottom Control (X-axis mode) ===
                ui.div(
                    ui.input_radio_buttons(
                        "pp_diffusion_x_axis_mode",
                        "Show agreements by:",
                        choices={"order": "Agreements in Order", "date": "Actual Dates of Agreements"},
                        selected="date",
                        inline=True
                    ),
                    style="text-align: left; margin-top: 15px; margin-bottom: 30px;"
                ),
                # === Export buttons ===
                ui.div(
                    ui.download_button(
                        "pp_export_diffusion_png", "Export PNG",
                        class_="btn btn-outline-primary btn-sm me-2",
                        style="margin-right: 10px;"
                    ),
                    ui.download_button(
                        "pp_export_diffusion_csv", "Export CSV",
                        class_="btn btn-outline-secondary btn-sm"
                    ),
                    style="margin-top: 10px;"
                ),
            ),
            style="padding: 20px; max-width: 100%; overflow-x: auto;"
        )
    )
)

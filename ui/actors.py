# ui/actors.py
from shiny import ui
from shinywidgets import output_widget

layout = ui.nav_panel(
    "Actors",
    ui.layout_sidebar(
        # Sidebar filters
        ui.sidebar(
            ui.h4("Agreement Filters"),
            #ui.h5("Agreement Filters", style="color: #091f40; margin-bottom: 12px;"),

            ui.input_selectize(
                "actors_region",
                "Select Region:",
                choices=[],
                multiple=True,
                options={"placeholder": "All regions"},
            ),
            ui.input_selectize(
                "actors_country",
                "Select Country:",
                choices=[],
                multiple=True,
                options={"placeholder": "All countries"},
            ),
            ui.input_selectize(
                "actors_agt_type",
                "Select Agreement Type:",
                choices=[],
                multiple=True,
                options={"placeholder": "All agreement types"},
            ),
            ui.input_slider(
                "actors_year_range",
                "Year Range:",
                min=1990,
                max=2025,
                value=[1990, 2025],
                step=1,
                sep="",
            ),
            ui.input_selectize(
                "actors_peace_process",
                "Select Peace Process:",
                choices=[],
                multiple=True,
                options={"placeholder": "All peace processes"},
            ),
            ui.input_selectize(
                "actors_stage",
                "Select Stages:",
                choices=[],
                multiple=True,
                options={"placeholder": "All stages"},
            ),
            ui.input_action_button(
                "reset_agreement_filters",
                "Reset Filters",
                class_="btn btn-secondary",
                style="margin-top: 10px; font-weight: 500;"
            ),
            ui.hr(),
            class_="sidebar",
        ),

        # ---- MAIN PANEL ----
        ui.div(
            # Header + selection filters
            ui.div(
                # === Title and descriptive text ===
                ui.h2("Explore Peace Agreement Signatories", style="color: #091f40; font-family: 'Montserrat', sans-serif; margin-bottom: 20px;"),
                ui.p(
                    "On this page you can explore peace agreements signatories. "
                    "In this box you can select an overall actor type or attribute (for example, select 'Intergovernmental Organizations' that are 'Regional'). "
                    "Alternatively, you can select a particular actor from the dropdown on the right (for example, 'African Union').",
                    ui.br(), 
                    "Use the checkbox for third party signatories to limit the data to instances when the actor was a third party "
                    "(this may be required when interrogating states that may act as either across conflicts). ",
                    ui.br(), 
                    "The filters in the sidebar will filter the agreements actors can be signatories to. ",
                    ui.tags.strong("Please note, this data excludes local agreements in PA-X."),
                    ui.br(), ui.br(),
                    "Please cite the signatory data as:",
                    ui.br(),
                    style="margin-bottom: 10px; font-size: 1em; color: #333;"
                ),
                ui.p(
                    "Badanjak, Sanja; Henry, Niamh. (2025). Peace Agreement Actors Dataset (PAA-X), 1990-2023 [dataset]. "
                    "University of Edinburgh. School of Law. https://doi.org/10.7488/ds/7932.",
                    style="font-style: italic; color: #555; font-size: 0.9em; margin-top: 8px;"
                ),

                # --- Divider below ---
                ui.hr(),

                # === Dropdown row with aligned third-party checkbox ===
                ui.h4("Select an actor type or specific actors(s):"),
                ui.row(
                    ui.column(
                        6,
                        ui.input_selectize(
                            "actors_type_combo",
                            "Select actor type(s):",
                            choices=[],
                            multiple=True,
                            options={"placeholder": "Choose actor type(s)"},
                            width="100%",
                        ),
                    ),
                    ui.column(
                        6,
                        ui.input_selectize(
                            "actors_selected",
                            "Select actor(s):",
                            choices=[],
                            multiple=True,
                            options={"placeholder": "Choose one or more actors"},
                            width="100%",
                        ),
                    ),
                    style="align-items: end; margin-bottom: 10px;",
                ),

                # === Actor attribute checkboxes (single line) ===
                ui.row(
                    ui.column(
                        6,
                        ui.div(
                            ui.h5("Actor-level attributes:", style="margin-bottom: 6px;"),
                            ui.input_checkbox_group(
                                "actors_flags",
                                None,
                                choices={
                                    "international": "International",
                                    "regional": "Regional",
                                    "women": "Women",
                                },
                                selected=[],
                                inline=True,
                            ),
                        ),
                    ),
                    ui.column(
                        4,
                        ui.div(
                            ui.h5("Signatory-level filter:", style="margin-bottom: 6px;"),
                            ui.input_checkbox(
                                "actors_third_party_only",
                                "Only as third-party signatory",
                                False,
                            ),
                            style="margin-bottom: 15px;",
                        ),
                    ),
                ),

                # === Summary card and reset button (aligned bottom-right) ===
                ui.div(
                    ui.output_ui("actors_overview"),
                    ui.div(
                        ui.input_action_button(
                            "reset_actors",
                            "Reset Actor Filters",
                            class_="btn btn-outline-danger me-2",  # red outline style
                        ),
                        style="text-align: right;"
                    ),
                    style="margin-top: 5px;",
                ),

                # --- Outer styling for container ---
                style=(
                    "background-color: #f8f9fa; padding: 18px 25px; "
                    "border-radius: 8px; margin-bottom: 25px;"
                ),
            ),

            # Main content (charts etc.)
            ui.div(
                # Map
                ui.div(
                    ui.h2("Geographic Distribution", class_="mb-1"),
                    ui.p(
                        "Countries with agreements signed by the selected actors",
                        class_="text-muted mb-3",
                    ),
                    ui.p(
                        f"Example use: does the actor stick to agreements addressing one regional area or do they have wide geographic involvement? ", 
                        style="font-style: italic; color: #555; font-size: 0.9em; margin-top: 8px;"
                        ),
                    ui.div(
                        output_widget("actors_map"),
                        style="height: 500px; width: 100%; margin-bottom: 10px;",
                    ),
                    ui.div(
                        ui.download_button(
                            "actors_map_csv",
                            "Export CSV",
                            class_="btn btn-outline-secondary btn-sm",
                        ),
                        class_="mb-4",
                    ),
                    style="margin-bottom: 28px;",
                ),

                ui.hr(),

                # Over Time
                ui.div(
                    ui.h2("Agreements Over Time", class_="mb-2"),
                    ui.p(
                        "See trends in when agreements were signed by the selected actors over time. ",
                        class_="text-muted mb-3",
                    ),
                    ui.p(
                        "Example use: view as a percentage to see if the actor signs a large proportion of agreements signed in a year e.g. Russia signed one-third of all agreements in 1996. ", 
                        style="font-style: italic; color: #555; font-size: 0.9em; margin-top: 8px;"
                        ),
                    ui.input_radio_buttons(
                        "actors_time_mode",
                        "Select Mode",
                        ["Count", "Percentage"],
                        selected="Count",
                    ),
                    ui.output_plot("actors_over_time", height="650px", fill=False),
                    ui.div(
                        ui.download_button(
                            "actors_over_time_png",
                            "Export PNG",
                            class_="btn btn-outline-primary btn-sm me-2",
                        ),
                        ui.download_button(
                            "actors_over_time_csv",
                            "Export CSV",
                            class_="btn btn-outline-secondary btn-sm",
                        ),
                        class_="mb-4",
                    ),
                    style="margin-bottom: 28px;",
                ),

                ui.hr(),

                # Agreement types
                ui.div(
                    ui.h2("Agreement Type Breakdown", style="margin-bottom: 15px;"),
                    ui.p(
                    "This chart shows the proportion of the agreement types for all agreement signed. Agreements in this data can be interstate, intrastate or interstate/mixed - see ",
                    ui.HTML(
                        '<a href="https://www.peaceagreements.org/cms/documents/4202/Definitions_Main.pdf" target="_blank">PA-X Definitions</a>.'
                    ),
                    style="margin-bottom: 10px; font-size: 1em; color: #333;"
                ),

                    ui.output_plot("actors_agreement_type_pie"),
                    ui.div(
                        ui.download_button(
                            "actors_agreement_type_pie_png",
                            "Export PNG",
                            class_="btn btn-outline-primary btn-sm me-2",
                        ),
                        ui.download_button(
                            "actors_agreement_type_pie_csv",
                            "Export CSV",
                            class_="btn btn-outline-secondary btn-sm",
                        ),
                        class_="mb-4",
                    ),
                    style="margin-bottom: 40px;",
                ),

                ui.hr(),

                # Stage
                ui.div(
                    ui.h2("Agreements by Stage", class_="mb-2"),
                    ui.p(
                        "This chart shows the number of agreements signed per Stage of Process. View as a percentage to compare to the overall proportion of agreements signed at that stage. ",
                        class_="text-muted mb-3",
                    ),
                    ui.p(
                        "Example use: what stage do actors tend to sign at, compared with all agreements? Do the United States sign more frequently at comprehensive stages, rather than the ceasefire stage? ", 
                        style="font-style: italic; color: #555; font-size: 0.9em; margin-top: 8px;"
                        ),
                    ui.input_radio_buttons(
                        "actors_stage_mode",
                        "Select Metric",
                        ["Count", "Percentage"],
                        selected="Count",
                    ),
                    ui.output_plot("actors_by_stage", height="700px", fill=False),
                    ui.div(
                        ui.download_button(
                            "actors_by_stage_png",
                            "Export PNG",
                            class_="btn btn-outline-primary btn-sm me-2",
                        ),
                        ui.download_button(
                            "actors_by_stage_csv",
                            "Export CSV",
                            class_="btn btn-outline-secondary btn-sm",
                        ),
                        class_="mb-4",
                    ),
                    style="margin-bottom: 28px;",
                ),

                ui.hr(),

                # --- Peace Processes section ---
                ui.div(
                    ui.h2("Peace Processes for Selected Actors", class_="mb-2"),
                    ui.p(
                        "Top peace processes in which the selected actors have signed agreements. Showing 'Top N' - use slider to select how many to show. If the selection has been in less than 5 processes, the chart will show them all. View by percentage of all agreements in the process, or by stage of process. ",
                        class_="text-muted mb-3",
                    ),
                    ui.p(
                        f"Example use: are there actors who signed 100% of agreements in a peace process? ", 
                        style="font-style: italic; color: #555; font-size: 0.9em; margin-top: 8px;"
                        ),

                    ui.input_radio_buttons(
                        "actors_pp_view_mode",
                        "View Peace Processes by:",
                        choices={
                            "count": "Total Agreements (Count)",
                            "percentage": "Percentage of Total Agreements",
                            "stage": "By Stage of Process"
                        },
                        selected="count",
                        inline=True,
                    ),

                    ui.input_slider(
                        "actors_top_processes",
                        "Show Top N Peace Processes",
                        min=5,
                        max=30,
                        value=20,
                        step=1,
                        width="40%",
                    ),

                    # Conditional plot height - pick up here - cant have same name 
                    ui.div(
                        ui.output_plot("actors_by_peace_process", height="725px"),
                            style="overflow-y:auto; max-height:750px;"
                        ),
                     ),

                    ui.div(
                        ui.download_button(
                            "actors_peace_process_png",
                            "Export PNG",
                            class_="btn btn-outline-primary btn-sm me-2",
                        ),
                        ui.download_button(
                            "actors_peace_process_csv",
                            "Export CSV",
                            class_="btn btn-outline-secondary btn-sm",
                        ),
                        class_="mb-4",
                    ),
                    style="margin-bottom: 28px;",
                ),

                ui.hr(),

                # Co-sign partners
                ui.div(
                    ui.h2("Co-sign Partners", class_="mb-2"),
                     ui.p(
                        "The charts below show the 'Top N' number of co-signatories along with the selected actor, by number of agreements they have co-signed. See for both party and third party signatories. ",
                        class_="text-muted mb-3",
                    ),
                    ui.p(
                        f"Example use: has there been a constant co-signatory along with the selected actor(s)? ", 
                        style="font-style: italic; color: #555; font-size: 0.9em; margin-top: 8px;"
                        ),
                    ui.input_slider(
                        "actors_top_n",
                        "Show Top N Co-signatories",
                        min=5,
                        max=30,
                        value=15,
                        step=1,
                        width="40%",
                    ),
                    ui.div(
                        ui.h4("Party Co-signatories", class_="mb-2"),
                        ui.output_plot("actors_party_cosign", height="650px", fill=False),
                        class_="mb-3",
                    ),
                    ui.div(
                        ui.download_button(
                            "actors_party_cosign_png",
                            "Export Party PNG",
                            class_="btn btn-outline-primary btn-sm me-2",
                        ),
                        ui.download_button(
                            "actors_party_cosign_csv",
                            "Export Party CSV",
                            class_="btn btn-outline-secondary btn-sm me-3",
                        ),
                    ui.hr(),
                    ),
                    ui.div(
                        ui.h4("Third-Party Co-signatories", class_="mb-2"),
                        ui.output_plot("actors_third_cosign", height="650px"),
                        class_="mb-3",
                    ),
                    ui.div(
                        ui.download_button(
                            "actors_third_cosign_png",
                            "Export Third PNG",
                            class_="btn btn-outline-primary btn-sm me-2",
                        ),
                        ui.download_button(
                            "actors_third_cosign_csv",
                            "Export Third CSV",
                            class_="btn btn-outline-secondary btn-sm",
                        ),
                        class_="mb-4",
                    ),
                    style="margin-bottom: 28px;",
                ),

                ui.hr(),

                # Topics
                ui.div(
                    ui.h2("Topics in Selected Actors' Agreements", class_="mb-2"),
                    ui.p(
                        "These charts show the number of agreements per topic, for agreements signed by the selected actor(s). View by issue to see more granular topics. ",
                        class_="text-muted mb-3",
                    ),
                    ui.p(
                        f"Example use: are there topics which are dominant in agreements signed by the selected actor? ", 
                        style="font-style: italic; color: #555; font-size: 0.9em; margin-top: 8px;"
                        ),
                    ui.input_radio_buttons(
                        "actors_topics_level",
                        "View Topics By:",
                        ["Category", "Issue"],
                        selected="Category",
                        inline=True,
                    ),
                    ui.div(  # wrap output_plot and apply scroll styling here
                        #ui.output_plot("actors_topics_chart", height="700px", fill=False),
                        #ui.output_plot("actors_topics_chart", fill=True, height="1000px"),
                        ui.output_ui("actors_topics_plot_container"),
                        style=
                            "max-height: 1200px; "
                            "scroll-behavior:smooth; "
                            "margin: 0 auto; "
                            "display:block; "
                            "padding-top:5px; "
                            "padding-bottom:15px;"
                            "overflow-y: auto;"
                        ),
                    ui.div(
                        ui.download_button(
                            "actors_topics_png",
                            "Export PNG",
                            class_="btn btn-outline-primary btn-sm me-2",
                        ),
                        ui.download_button(
                            "actors_topics_csv",
                            "Export CSV",
                            class_="btn btn-outline-secondary btn-sm",
                        ),
                        class_="mb-4",
                    ),
                    ui.hr(),
                    ui.div(
                    ui.output_ui("actors_topics_radial_plot_container"),
                        style=
                            "overflow-y:auto; max-height:1200px; "
                            "scroll-behavior:smooth; margin:0 auto; display:block; "
                            "padding-top:5px; padding-bottom:15px;"
                        ),
                    ui.div(
                        ui.download_button(
                            "actors_topics_radial_png",
                            "Export PNG",
                            class_="btn btn-outline-primary btn-sm me-2",
                        ),
                        ui.download_button(
                            "actors_topics_radial_csv",
                            "Export CSV",
                            class_="btn btn-outline-secondary btn-sm",
                        ),
                        class_="mb-4",
                    ),
                    style="margin-bottom: 28px;",
                ),


                ui.hr(),

                # Bottom table
                ui.div(
                    ui.h2("Agreements Table", class_="mb-2"),
                      ui.p(
                        "This table provides an overview of all agreements signed by the selected actor(s) for the selected agreements. View the agreements using the PA-X link or export the table for re-use. ",
                        class_="text-muted mb-3",
                    ),
                    ui.div(
                    ui.download_button("actors_table_csv", "Export Table as CSV", class_="btn btn-outline-primary btn-sm me-2"),
                    ui.download_button("actors_table_docx", "Export Table as Word Doc", class_="btn btn-outline-secondary btn-sm"),
                    class_="mb-4",
                ),
                    ui.output_ui("actors_table"),
                    style="margin-bottom: 28px;",
                ),

                style="padding: 20px; max-width: 100%; overflow-x: auto;",
            ),
        ),
    )
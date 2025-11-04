from shiny import App, ui
from ui import home, peace_process, topics, actors
from server import home as home_server, peace_process as peace_process_server, topics as topics_server, actors as actors_server
from pathlib import Path

# --- Define a global footer ---
footer = ui.div(
    ui.div(
        ui.row(
            # === LEFT COLUMN: UoE logo ===
            ui.column(
                4,
                ui.div(
                    ui.tags.a(
                        ui.img(
                            src="https://peacerep.github.io/logos/img/uoe_white.png",
                            alt="University of Edinburgh logo",
                            style="height:45px; vertical-align:middle;"
                        ),
                        href="https://www.law.ed.ac.uk/news-events/news/research-spotlight-peacereps-pa-x-peace-agreements-database",
                        target="_blank",
                    ),
                    style="text-align:left;"
                ),
            ),

            # === MIDDLE COLUMN: text block ===
            ui.column(
                4,
                ui.div(
                    "© 2025 PeaceRep – PA-X Peace Agreements Database",
                    ui.br(),
                    "Application developed by Niamh Henry",
                    ui.br(),
                    "University of Edinburgh",
                    style="font-size:0.9em; color:white; text-align:center;"
                ),
            ),

            # === RIGHT COLUMN: PeaceRep + PA-X logos ===
            ui.column(
                4,
                ui.div(
                    ui.tags.a(
                        ui.img(
                            src="https://peacerep.github.io/logos/img/PeaceRep_white.jpg",
                            alt="PeaceRep logo",
                            style="height:45px; margin-right:15px; vertical-align:middle;"
                        ),
                        href="https://peacerep.org/",
                        target="_blank",
                    ),
                    ui.tags.a(
                        ui.img(
                            src="https://peacerep.github.io/logos/img/Pax_white.png",
                            alt="PA-X logo",
                            style="height:60px; vertical-align:middle;"
                        ),
                        href="https://www.peaceagreements.org/",
                        target="_blank",
                    ),
                    style="text-align:right;"
                ),
            ),
        ),
        style="padding:10px 40px;"
    ),
    style="background-color:#091f40; margin-top:10px; padding-top:10px;"
)


# --- APP UI ---
# app_ui = ui.page_fluid(
#     ui.page_navbar(
#     home.layout,
#     peace_process.layout,
#     topics.layout,
#     actors.layout,
#     title=ui.tags.div(
#         ui.tags.img(
#             src="https://peacerep.github.io/logos/img/PeaceRep_Icon_white.png", 
#             alt="PeaceRep logo",
#             style="height:36px; margin-right:10px; vertical-align:middle;"
#         ),
#         ui.tags.img(
#             src="https://peacerep.github.io/logos/img/Pax_Circle_white.png", 
#             alt="PA-X logo",
#             style="height:36px; margin-right:10px; vertical-align:middle;"
#         ),
#         ui.tags.span(
#             "PA-Xplorer",
#             style="font-weight:600; font-size:62"
#         ),
#     ),
#     id="main_navbar",
#     bg="#091f40",
#     inverse=True,
# ) ,
# footer
# )
app_ui = ui.page_navbar(
    home.layout,
    peace_process.layout,
    topics.layout,
    actors.layout,
    title=ui.tags.div(
        ui.tags.img(
            src="https://peacerep.github.io/logos/img/PeaceRep_Icon_white.png", 
            alt="PeaceRep logo",
            style="height:36px; margin-right:10px; vertical-align:middle;"
        ),
        ui.tags.img(
            src="https://peacerep.github.io/logos/img/Pax_Circle_white.png", 
            alt="PA-X logo",
            style="height:36px; margin-right:10px; vertical-align:middle;"
        ),
        ui.tags.span(
            "PA-Xplorer",
            style="font-weight:600; font-size:62"
        ),
    ),
    id="main_navbar",
    bg="#091f40",
    inverse=True,
    footer=footer,   # ✅ add footer here, not outside
)




# --- Add styles and meta tags into head ---
# app_ui.head_content = [
#     ui.tags.link(rel="icon", type="image/png", href="https://peacerep.github.io/logos/img/Pax_Circle_nobg.jpg"),
#     ui.tags.link(rel="stylesheet", href="style.css"),
#     ui.tags.meta(name="viewport", content="width=device-width, initial-scale=1"),
# ]

app_ui.head_content = [
    ui.tags.title("PA-Xplorer | PeaceRep – University of Edinburgh"),
    ui.tags.link(
        rel="icon",
        type="image/png",
        href="https://peacerep.github.io/logos/img/Pax_Circle_nobg.jpg"
    ),
    ui.tags.meta(name="viewport", content="width=device-width, initial-scale=1"),
    ui.tags.link(rel="stylesheet", href="style.css"),
]


# --- SERVER ---
def server(input, output, session):
    home_server.server(input, output, session)
    peace_process_server.server(input, output, session)
    topics_server.server(input, output, session)
    actors_server.server(input, output, session)

# --- STATIC FILES ---
static_dir = Path(__file__).parent / "static"
print("📁 Serving static files from:", static_dir.resolve())


app = App(app_ui, server, static_assets=static_dir)

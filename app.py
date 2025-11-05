from shiny import App, ui
from ui import home, peace_process, topics, actors
from server import home as home_server, peace_process as peace_process_server, topics as topics_server, actors as actors_server
from pathlib import Path

from utils.data_loader import load_pax_data
load_pax_data()  # pre-load data once at app startup

overlay = ui.div(
    ui.div(class_="pr-spinner"),
    ui.h4("Loading PA-Xplorer Data...", class_="loading-text"),
    id="startup-loading",
)

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
    id="main_navbar",
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
        ui.tags.span("PA-Xplorer", style="font-weight:600; font-size:62"),
    ),
    bg="#091f40",
    inverse=True,
    footer=footer
)



# app_ui = ui.page_navbar(  
#         ui.nav_panel("Home", home.layout, value="home"),
#         ui.nav_panel("Peace Process", peace_process.layout, value="peace_process"),
#         ui.nav_panel("Topics", topics.layout, value="topics"),
#         ui.nav_panel("Actors", actors.layout, value="actors"),
#         id="main_navbar",
#         title=ui.tags.div(
#             ui.tags.img(
#                 src="https://peacerep.github.io/logos/img/PeaceRep_Icon_white.png",
#                 alt="PeaceRep logo",
#                 style="height:36px; margin-right:10px; vertical-align:middle;"
#             ),
#             ui.tags.img(
#                 src="https://peacerep.github.io/logos/img/Pax_Circle_white.png",
#                 alt="PA-X logo",
#                 style="height:36px; margin-right:10px; vertical-align:middle;"
#             ),
#             ui.tags.span("PA-Xplorer", style="font-weight:600; font-size:62"),
#         ),
#         bg="#091f40", 
#         inverse=True, 
#         header=overlay,
#         footer=footer
#     )
    # === Loading overlay (visible until app ready) ===
# ui.div(
#     ui.div(class_="pr-spinner"),
#     ui.h4("Loading PA-Xplorer Data...", class_="loading-text"),
#     id="startup-loading",
# )

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

app_ui.head_content += [
    ui.tags.style("""
    #startup-loading {
    position: fixed;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-direction: column;
    background: white;
    z-index: 2147483647;
    font-family: 'Montserrat', system-ui, sans-serif;
    transition: opacity 0.5s ease;
    }
    #startup-loading.hidden {
    opacity: 0;
    pointer-events: none;
    }
    .pr-spinner {
    width: 60px; height: 60px;
    border: 6px solid #091f40;
    border-right-color: transparent;
    border-radius: 50%;
    animation: pr-spin 1s linear infinite;
    }
    @keyframes pr-spin { to { transform: rotate(360deg); } }
    .loading-text {
    margin-top: 16px;
    color: #091f40;
    font-weight: 600;
    letter-spacing: 0.2px;
    }
    """),

    # small JS snippet to hide overlay when shiny is fully connected
    ui.tags.script("""
    document.addEventListener('shiny:connected', function() {
        const loader = document.getElementById('startup-loading');
        if (loader) {
            // wait a little to ensure all UI updates complete
            setTimeout(() => loader.classList.add('hidden'), 600);
            // and remove it completely after fade
            setTimeout(() => loader.remove(), 1200);
        }
    });
    """),
]

app_ui.head_content += [
    ui.tags.script("""
    // When app connects, set tab based on ?_page=
    document.addEventListener('shiny:connected', function() {
        const params = new URLSearchParams(window.location.search);
        const page = params.get('_page');
        if (page) {
            const nav = document.querySelector('[data-value="' + page + '"]');
            if (nav) nav.click();
        }
    });

    // When user changes tab, update the URL
    document.addEventListener('shiny:value', function(e) {
        if (e.detail.name === 'main_navbar') {
            const newPage = e.detail.value;
            const url = new URL(window.location);
            url.searchParams.set('_page', newPage);
            window.history.replaceState({}, '', url);
        }
    });
    """)
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


from shiny import App, ui, run_app
from ui import home, topics, actors
from server import home as home_server, topics as topics_server, actors as actors_server

app_ui = ui.page_navbar(
    home.layout,
    topics.layout,
    actors.layout,
    title=None,  # We’ll use a custom header
    id="main_navbar",
    #head_content=ui.tags.link(rel="stylesheet", href="static/style.css")
)

ui.tags.script(
    """
    document.addEventListener("DOMContentLoaded", function() {
        const btn = document.getElementById("hamburger");
        const sidebar = document.getElementById("sidebar");
        if (btn && sidebar) {
            btn.addEventListener("click", () => {
                sidebar.classList.toggle("collapsed");
            });
        }
    });
    """
)

# Define server function
def server(input, output, session):
    # Import and call your server functions
    home_server.server(input, output, session)
    topics_server.server(input, output, session)
    actors_server.server(input, output, session)

# Create the app object
app = App(app_ui, server)
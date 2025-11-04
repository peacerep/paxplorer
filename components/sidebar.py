# components/sidebar.py

from shiny import ui

def collapsible_sidebar(content):
    return ui.tags.div(
        {"class": "sidebar-wrapper", "id": "sidebar"},
        content
    )

def hamburger_toggle():
    return ui.tags.button("☰", id="hamburger", class_="hamburger")

# components/header.py

from shiny import ui

def branding_header():
    return ui.tags.div(
        {"class": "shiny-heading"},
        ui.tags.img(src="static/logos/PeaceRep_nobg.png", alt="PeaceRep Logo"),
        ui.tags.h1("PA-Xplorer"),
        ui.tags.img(src="static/logos/Pax_nobg.png", alt="PAX Logo")
    )

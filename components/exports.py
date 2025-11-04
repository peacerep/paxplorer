# components/exports.py

from shiny import ui

def download_button_with_icon(id: str, label: str, icon: str):
    """
    Reusable download button with brand styling and icon.
    
    Args:
        id (str): The output ID (must match @render.download)
        label (str): The button text
        icon (str): Icon filename (e.g., 'png.png' or 'csv.png')
    """
    return ui.tags.a(
        ui.tags.img(src=f"static/logos/{icon}"),
        label,
        href="#",
        id=id,
        class_="btn shiny-download-link",
        download=None
    )
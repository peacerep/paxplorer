# utils/png_export_utils.py
import io
import matplotlib.pyplot as plt
import pandas as pd

LOGO_PATH = "static/logos/Pax.png"

# Optional standard logo positions
LOGO_POSITIONS = {
    "default": (0.92, 0.94, 0.078, 0.078),
    "with_legend": (0.99, 0.99, 0.075, 0.075)
}


def get_data_version(load_data_fn_or_df):
    """Extract PA-X data version from load_data() or a DataFrame."""
    try:
        if isinstance(load_data_fn_or_df, dict) and "pax" in load_data_fn_or_df:
            pax = load_data_fn_or_df["pax"]
        elif callable(load_data_fn_or_df):
            pax = load_data_fn_or_df()["pax"]
        else:
            pax = load_data_fn_or_df

        if "Ver" in pax.columns and not pax["Ver"].isna().all():
            return str(pax["Ver"].max())
    except Exception:
        pass
    return "Unknown"


def add_logo_and_subtitle(
    fig,
    filter_text: str,
    data_version: str,
    *,
    logo_position=(0.92, 0.94, 0.078, 0.078),
    filter_text_position=(0.5, 0.009),
    version_position=(0.98, 0.02)
):
    """Add logo, data version, and filter info to a Matplotlib figure."""
    # Subtitle (bottom-center)
    fig.text(
        filter_text_position[0],
        filter_text_position[1],
        filter_text,
        transform=fig.transFigure,
        ha="center",
        va="bottom",
        fontsize=8,
        style="italic",
        color="#666666",
    )

    # Data version (bottom-right)
    fig.text(
        version_position[0],
        version_position[1],
        f"PA-X Database v{data_version}",
        transform=fig.transFigure,
        ha="right",
        va="bottom",
        fontsize=7,
        color="#999999",
    )

    # Logo (top-right)
    try:
        logo_img = plt.imread(LOGO_PATH)
        logo_ax = fig.add_axes(list(logo_position))
        logo_ax.imshow(logo_img, alpha=0.8)
        logo_ax.axis("off")
    except Exception as e:
        print(f"Warning: Could not add logo: {e}")


def export_with_branding(
    plot_func,
    *,
    filter_text_fn=None,
    data_version_fn=None,
    load_data_fn=None,
    logo_position=(0.92, 0.94, 0.078, 0.078),
    filter_text_position=(0.5, 0.009),
    version_position=(0.98, 0.02),
):
    """
    Generate a branded PNG for any Matplotlib figure.
    Works for functions that return a Matplotlib figure.
    """
    try:
        if hasattr(plot_func, "_fn"):
            fig = plot_func._fn()
        else:
            fig = plot_func()

        filter_text = filter_text_fn() if filter_text_fn else "Filters applied"
        data_version = (
            data_version_fn(load_data_fn)
            if (data_version_fn and load_data_fn)
            else "Unknown"
        )

        add_logo_and_subtitle(
            fig,
            filter_text,
            data_version,
            logo_position=logo_position,
            filter_text_position=filter_text_position,
            version_position=version_position,
        )

        buf = io.BytesIO()
        fig.savefig(
            buf,
            format="png",
            bbox_inches="tight",
            dpi=300,
            facecolor="white",
            edgecolor="none",
        )
        buf.seek(0)
        plt.close(fig)
        return buf
    except Exception as e:
        print(f"Error exporting PNG: {e}")
        return io.BytesIO()

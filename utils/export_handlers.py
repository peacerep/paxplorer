from shiny import render
from io import BytesIO
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import pandas as pd
import os

LOGO_PATH = "static/logos/Pax.png"  # logo path

def make_png_download(fig_func, filename):
    @render.download(filename=filename)
    def _download():
        try:
            fig = fig_func()
            
            # Try to add logo
            if os.path.exists(LOGO_PATH):
                try:
                    logo_img = mpimg.imread(LOGO_PATH)
                    
                    # Get figure size in pixels
                    fig_width, fig_height = fig.get_size_inches() * fig.dpi
                    
                    # Calculate logo size (make it smaller, e.g., 10% of figure width)
                    logo_width = min(logo_img.shape[1], fig_width * 0.1)
                    logo_height = logo_img.shape[0] * (logo_width / logo_img.shape[1])
                    
                    # Position in top-right corner with padding
                    x_pos = fig_width - logo_width - 20
                    y_pos = fig_height - logo_height - 20
                    
                    # Add logo using figimage with correct positioning
                    fig.figimage(
                        logo_img,
                        xo=int(x_pos),
                        yo=int(y_pos),
                        zorder=10,
                        alpha=0.8  # Make it slightly transparent
                    )
                except Exception as e:
                    print(f"Warning: Could not add logo: {e}")
            
            # Create buffer and save
            buf = BytesIO()
            fig.savefig(buf, format="png", bbox_inches="tight", dpi=300, 
                       facecolor='white', edgecolor='none')
            buf.seek(0)
            plt.close(fig)  # Important: close the figure to free memory
            return buf
            
        except Exception as e:
            print(f"Error in PNG export: {e}")
            # Return empty buffer if something goes wrong
            buf = BytesIO()
            return buf

    return _download


def make_csv_download(data_func, filename):
    @render.download(filename=filename)
    def _download():
        try:
            df = data_func()
            if not isinstance(df, pd.DataFrame):
                raise ValueError("CSV export function must return a pandas DataFrame")

            # Create CSV string with explicit UTF-8 encoding and encode to bytes
            csv_string = df.to_csv(index=False, encoding="utf-8")
            return BytesIO(csv_string.encode('utf-8'))

        except Exception as e:
            print(f"Error in CSV export: {e}")
            # Return empty CSV if something goes wrong
            return BytesIO(b"Error,Message\nExport Failed,Please try again")

    return _download
# utils/export_handlers.py
import io
from shiny import render
import matplotlib.pyplot as plt

def make_png_download(fig_func, filename):
    @render.download(filename=filename)
    def download_handler():
        fig = fig_func()
        img_buffer = io.BytesIO()
        fig.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
        img_buffer.seek(0)
        plt.close(fig)  # Important: close the figure to free memory
        return img_buffer.getvalue()
    return download_handler

def make_csv_download(data_func, filename):
    @render.download(filename=filename)
    def download_handler():
        df = data_func()
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        return csv_buffer.getvalue().encode('utf-8')
    return download_handler
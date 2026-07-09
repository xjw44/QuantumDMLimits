import numpy as np
import requests
import fitz  # pymupdf


def show_pdf_page(source: str, page_num: int, dpi: int = 200) -> np.ndarray:
    """
    Render a PDF page and display it with Plotly for interactive zoom/pan.
    Hover over the image to read pixel (x, y) coordinates — use these to
    set crop corners in the next step.
    Returns the image array for use in cropping and calibration.
    """
    import plotly.express as px

    img = load_pdf_page(source, page_num, dpi=dpi)
    fig = px.imshow(img, title=f"{source}  —  page {page_num}")
    fig.update_layout(
        coloraxis_showscale=False,
        margin=dict(l=0, r=0, t=30, b=0),
        xaxis_title="pixel x",
        yaxis_title="pixel y",
    )
    fig.show(renderer="iframe")
    print(f"Image size: {img.shape[1]} × {img.shape[0]} px  (width × height)")
    return img


def show_image(path: str) -> np.ndarray:
    """
    Load a PNG (or any image file) and display it with Plotly.
    Hover over the image to read pixel (x, y) coordinates.
    Returns the image array.
    """
    import plotly.express as px
    from PIL import Image as PILImage

    img = np.array(PILImage.open(path).convert("RGB"))
    fig = px.imshow(img, title=path)
    fig.update_layout(
        coloraxis_showscale=False,
        margin=dict(l=0, r=0, t=30, b=0),
        xaxis_title="pixel x",
        yaxis_title="pixel y",
    )
    fig.show(renderer="iframe")
    print(f"Image size: {img.shape[1]} × {img.shape[0]} px  (width × height)")
    return img


def load_pdf_page(source: str, page_num: int, dpi: int = 200) -> np.ndarray:
    """Render a PDF page to an RGB numpy array. source can be a file path or URL."""
    if source.startswith("http://") or source.startswith("https://"):
        print(f"Downloading {source} ...")
        r = requests.get(source, timeout=60)
        r.raise_for_status()
        doc = fitz.open(stream=r.content, filetype="pdf")
    else:
        doc = fitz.open(source)

    if page_num < 1 or page_num > len(doc):
        raise ValueError(f"Page {page_num} out of range (PDF has {len(doc)} pages).")

    page = doc[page_num - 1]
    zoom = dpi / 72.0
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 3)
    doc.close()
    return img

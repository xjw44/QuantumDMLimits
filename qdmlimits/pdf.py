import numpy as np
import requests
import fitz  # pymupdf


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

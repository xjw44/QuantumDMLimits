import cv2
import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import label
from scipy.signal import savgol_filter

from .calibration import _click_points


def pick_color_at(img_rgb: np.ndarray, px: int, py: int) -> np.ndarray:
    """
    Sample the color at pixel (px, py) from the image.
    Hover over the curve in show_image() to read the coordinates, then pass them here.
    Returns BGR color array for use with extract_curve_by_color().

    Example:
      color_bgr = pick_color_at(img, px=540, py=312)
      pixels = extract_curve_by_color(img, color_bgr, tol=30)
    """
    color_rgb = img_rgb[py, px]
    color_bgr = color_rgb[::-1]
    swatch = f"\033[48;2;{color_rgb[0]};{color_rgb[1]};{color_rgb[2]}m     \033[0m"
    print(f"Sampled at ({px}, {py})  RGB={tuple(color_rgb)}  BGR={tuple(color_bgr)}  {swatch}")
    return color_bgr.copy()


def pick_color(crop: np.ndarray) -> np.ndarray:
    """User clicks on a curve; returns its BGR color."""
    print("\nClick directly on the curve you want to extract.")
    pts = _click_points(crop, 1, "Pick curve color", "Click on the curve line")
    x, y = pts[0]
    color_rgb = crop[y, x]
    print(f"  Sampled RGB: {color_rgb}")
    return color_rgb[::-1]  # BGR for OpenCV


def extract_curve_by_color(
    crop: np.ndarray,
    color_bgr: np.ndarray,
    tol: int = 30,
    min_pixels: int = 50,
    dilate: int = 0,
    component_rank: int = 1,
) -> np.ndarray:
    """
    Mask pixels within tol of color_bgr, find connected components.
    Returns (N, 2) array of (col, row) pixel coords.

    dilate: bridge horizontal gaps between dashes (pixels). Try 10-30 for dashed curves.
    component_rank: 1=largest, 2=second largest, etc. Use >1 to skip axis borders.
    """
    img_bgr = cv2.cvtColor(crop, cv2.COLOR_RGB2BGR)
    lower = np.clip(color_bgr.astype(int) - tol, 0, 255).astype(np.uint8)
    upper = np.clip(color_bgr.astype(int) + tol, 0, 255).astype(np.uint8)
    mask = cv2.inRange(img_bgr, lower, upper)

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)

    if dilate > 0:
        bridge = cv2.getStructuringElement(cv2.MORPH_RECT, (dilate * 2 + 1, 3))
        mask = cv2.dilate(mask, bridge, iterations=1)

    labeled, n = label(mask)
    if n == 0:
        print("  Warning: no pixels matched — try increasing tol.")
        return np.empty((0, 2))

    sizes = np.bincount(labeled.ravel())
    sizes[0] = 0
    ranked = np.argsort(sizes)[::-1]  # largest first

    print(f"  Found {n} components. Top sizes: {sizes[ranked[:5]]}")
    chosen = ranked[component_rank - 1]
    if sizes[chosen] < min_pixels:
        print(f"  Warning: component {component_rank} has only {sizes[chosen]} pixels.")

    ys, xs = np.where(labeled == chosen)
    return np.column_stack([xs, ys])


def trace_curve(
    img_rgb: np.ndarray,
    color_bgr: np.ndarray,
    calib,
    x_min: float,
    x_max: float,
    tol: int = 30,
) -> np.ndarray:
    """
    Trace a continuous curve column-by-column across the data x range [x_min, x_max].

    For each pixel column in that range, finds the row whose color is closest
    to color_bgr within tol. More robust than connected components for curves
    that cross other curves or have color gaps.

    Returns (N, 2) array of (col, row) pixel coords, one point per column.

    Example:
      sorted_pix = trace_curve(img, color_bgr, calib, x_min=2, x_max=6, tol=40)
      preview_extraction(img, sorted_pix, name='panda')
    """
    import math

    img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR).astype(np.int32)
    color = color_bgr.astype(np.int32)

    # convert data x range to pixel columns
    if calib.xlog:
        px_min = calib.px[0] + (math.log10(x_min) - calib.dx[0]) * (calib.px[1] - calib.px[0]) / (calib.dx[1] - calib.dx[0])
        px_max = calib.px[0] + (math.log10(x_max) - calib.dx[0]) * (calib.px[1] - calib.px[0]) / (calib.dx[1] - calib.dx[0])
    else:
        px_min = calib.px[0] + (x_min - calib.dx[0]) * (calib.px[1] - calib.px[0]) / (calib.dx[1] - calib.dx[0])
        px_max = calib.px[0] + (x_max - calib.dx[0]) * (calib.px[1] - calib.px[0]) / (calib.dx[1] - calib.dx[0])

    col_start = max(0, int(min(px_min, px_max)))
    col_end   = min(img_rgb.shape[1] - 1, int(max(px_min, px_max)))

    pts = []
    for col in range(col_start, col_end + 1):
        column = img_bgr[:, col, :]
        dist = np.max(np.abs(column - color), axis=1)
        best_row = int(np.argmin(dist))
        if dist[best_row] <= tol:
            pts.append((col, best_row))

    if not pts:
        print("  Warning: no points found — try increasing tol.")
        return np.empty((0, 2))

    print(f"  Traced {len(pts)} points from x={x_min} to x={x_max}.")
    return np.array(pts)


def sort_curve_pixels(pixels: np.ndarray) -> np.ndarray:
    """Sort pixels left-to-right, taking median y per unique x column."""
    if len(pixels) == 0:
        return pixels
    pixels = pixels[np.argsort(pixels[:, 0])]
    xs, ys = pixels[:, 0], pixels[:, 1]
    unique_x = np.unique(xs)
    median_y = np.array([np.median(ys[xs == xi]) for xi in unique_x])
    return np.column_stack([unique_x, median_y])


def smooth_curve(sorted_pix: np.ndarray, window: int = 11, poly: int = 3) -> np.ndarray:
    n = len(sorted_pix)
    if n < window:
        return sorted_pix
    window = min(window, n if n % 2 == 1 else n - 1)
    smoothed_y = savgol_filter(sorted_pix[:, 1], window_length=window, polyorder=poly)
    return np.column_stack([sorted_pix[:, 0], smoothed_y])


def preview_extraction(img_rgb: np.ndarray, pixels: np.ndarray, name: str = "curve") -> None:
    """Overlay extracted curve pixels on the image using Plotly."""
    import plotly.express as px
    import plotly.graph_objects as go

    fig = px.imshow(img_rgb, title=f"Extraction preview: {name}")
    fig.update_layout(
        coloraxis_showscale=False,
        margin=dict(l=0, r=0, t=40, b=0),
        xaxis_title="pixel x",
        yaxis_title="pixel y",
    )
    if len(pixels):
        fig.add_trace(go.Scatter(
            x=pixels[:, 0], y=pixels[:, 1],
            mode="markers",
            marker=dict(color="lime", size=2, opacity=0.7),
            name=name,
        ))
    fig.show(renderer="iframe")

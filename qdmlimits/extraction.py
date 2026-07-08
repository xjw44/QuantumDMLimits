import cv2
import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import label
from scipy.signal import savgol_filter

from .calibration import _click_points


def pick_color(crop: np.ndarray) -> np.ndarray:
    """User clicks on a curve; returns its BGR color."""
    print("\nClick directly on the curve you want to extract.")
    pts = _click_points(crop, 1, "Pick curve color", "Click on the curve line")
    x, y = pts[0]
    color_rgb = crop[y, x]
    print(f"  Sampled RGB: {color_rgb}")
    return color_rgb[::-1]  # BGR for OpenCV


def extract_curve_by_color(crop: np.ndarray, color_bgr: np.ndarray, tol: int = 30, min_pixels: int = 50) -> np.ndarray:
    """
    Mask pixels within tol of color_bgr, find the largest connected component.
    Returns (N, 2) array of (col, row) pixel coords.
    """
    img_bgr = cv2.cvtColor(crop, cv2.COLOR_RGB2BGR)
    lower = np.clip(color_bgr.astype(int) - tol, 0, 255).astype(np.uint8)
    upper = np.clip(color_bgr.astype(int) + tol, 0, 255).astype(np.uint8)
    mask = cv2.inRange(img_bgr, lower, upper)

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)

    labeled, n = label(mask)
    if n == 0:
        print("  Warning: no pixels matched — try increasing --tol.")
        return np.empty((0, 2))

    sizes = np.bincount(labeled.ravel())
    sizes[0] = 0
    largest = np.argmax(sizes)
    if sizes[largest] < min_pixels:
        print(f"  Warning: largest component has only {sizes[largest]} pixels.")

    ys, xs = np.where(labeled == largest)
    return np.column_stack([xs, ys])


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


def preview_extraction(crop: np.ndarray, pixels: np.ndarray, name: str):
    fig, ax = plt.subplots(figsize=(10, 7))
    ax.imshow(crop)
    if len(pixels):
        ax.scatter(pixels[:, 0], pixels[:, 1], s=1, c="lime", label="extracted")
    ax.set_title(f"Preview: {name}")
    ax.legend()
    plt.tight_layout()
    plt.show()

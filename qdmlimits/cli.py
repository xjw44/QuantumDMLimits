import argparse
from pathlib import Path

import numpy as np

from .pdf import load_pdf_page
from .calibration import crop_to_plot, calibrate_axes
from .extraction import pick_color, extract_curve_by_color, sort_curve_pixels, smooth_curve, preview_extraction


def digitize(source: str, page_num: int, out_dir: Path, tol: int, smooth: bool):
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nLoading page {page_num} from {source} ...")
    img = load_pdf_page(source, page_num)

    crop, _ = crop_to_plot(img)
    calib = calibrate_axes(crop)

    curve_index = 1
    while True:
        print(f"\n--- Curve {curve_index} ---")
        action = input("Press Enter to extract a curve, or type 'done' to finish: ").strip().lower()
        if action == "done":
            break

        color_bgr = pick_color(crop)
        pixels = extract_curve_by_color(crop, color_bgr, tol=tol)

        if len(pixels) == 0:
            print("  No curve found. Try again.")
            continue

        sorted_pix = sort_curve_pixels(pixels)
        if smooth:
            sorted_pix = smooth_curve(sorted_pix)

        preview_extraction(crop, sorted_pix, f"curve_{curve_index}")
        if input("  Keep this curve? [Y/n]: ").strip().lower() == "n":
            continue

        name = input(f"  Name for this curve [curve_{curve_index}]: ").strip() or f"curve_{curve_index}"
        x_data, y_data = calib.to_data(sorted_pix[:, 0], sorted_pix[:, 1])

        csv_path = out_dir / f"{name}.csv"
        np.savetxt(csv_path, np.column_stack([x_data, y_data]), delimiter=",", header="x,y", comments="")
        print(f"  Saved {len(x_data)} points → {csv_path}")

        curve_index += 1

    print(f"\nDone. {curve_index - 1} curve(s) saved to {out_dir}/")


def main():
    parser = argparse.ArgumentParser(
        description="Digitize limit curves from a PDF plot.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("source", help="PDF file path or URL")
    parser.add_argument("--page", type=int, default=1, help="PDF page number (1-indexed)")
    parser.add_argument("--out", default="curves", help="Output directory for CSV files")
    parser.add_argument("--tol", type=int, default=30, help="Color tolerance (0-255)")
    parser.add_argument("--no-smooth", action="store_true", help="Disable Savitzky-Golay smoothing")
    args = parser.parse_args()

    digitize(
        source=args.source,
        page_num=args.page,
        out_dir=Path(args.out),
        tol=args.tol,
        smooth=not args.no_smooth,
    )

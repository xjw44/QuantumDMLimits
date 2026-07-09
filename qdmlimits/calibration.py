import numpy as np
import matplotlib.pyplot as plt


def _click_points(img_rgb: np.ndarray, n: int, title: str, instructions: str) -> list:
    """Display image and collect n mouse clicks, returning list of (x, y) pixel coords."""
    pts = []
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.imshow(img_rgb)
    ax.set_title(f"{title}\n{instructions}", fontsize=10)

    def onclick(event):
        if event.inaxes != ax:
            return
        x, y = int(event.xdata), int(event.ydata)
        pts.append((x, y))
        ax.plot(x, y, "r+", markersize=12, markeredgewidth=2)
        ax.annotate(str(len(pts)), (x, y), color="red", fontsize=9, xytext=(5, 5), textcoords="offset points")
        fig.canvas.draw()
        if len(pts) == n:
            plt.close(fig)

    fig.canvas.mpl_connect("button_press_event", onclick)
    plt.tight_layout()
    plt.show()
    input(f"Click {n} point(s) on the plot above, then press Enter: ")
    plt.close(fig)
    if len(pts) < n:
        print(f"  Warning: expected {n} clicks, got {len(pts)}")
    return pts[:n]


def crop_to_plot(img_rgb: np.ndarray):
    """Interactively crop to plot area. Returns (cropped image, (x0, y0, x1, y1))."""
    print("\nClick the TOP-LEFT then BOTTOM-RIGHT corner of the plot area.")
    pts = _click_points(img_rgb, 2, "Crop plot region", "Click TOP-LEFT, then BOTTOM-RIGHT")
    (x0, y0), (x1, y1) = pts
    x0, x1 = min(x0, x1), max(x0, x1)
    y0, y1 = min(y0, y1), max(y0, y1)
    return img_rgb[y0:y1, x0:x1], (x0, y0, x1, y1)


class AxisCalibration:
    """Maps pixel coordinates to data coordinates for log or linear axes."""

    def __init__(self, px, py, dx, dy, xlog=False, ylog=False):
        self.px = px
        self.py = py
        self.dx = np.log10(dx) if xlog else np.array(dx, dtype=float)
        self.dy = np.log10(dy) if ylog else np.array(dy, dtype=float)
        self.xlog = xlog
        self.ylog = ylog

    def to_data(self, pix_x, pix_y):
        x = self.dx[0] + (pix_x - self.px[0]) * (self.dx[1] - self.dx[0]) / (self.px[1] - self.px[0])
        y = self.dy[0] + (pix_y - self.py[0]) * (self.dy[1] - self.dy[0]) / (self.py[1] - self.py[0])
        if self.xlog:
            x = 10.0 ** x
        if self.ylog:
            y = 10.0 ** y
        return x, y


def check_calibration(img_rgb: np.ndarray, calib: "AxisCalibration") -> None:
    """
    Overlay calibration lines on the image and display with Plotly.

    Blue vertical lines   = x-axis reference pixels (px1, px2)
    Red  horizontal lines = y-axis reference pixels (py1, py2)

    If the lines pass through the correct axis tick marks the calibration is good.
    """
    import plotly.express as px
    import plotly.graph_objects as go

    h, w = img_rgb.shape[:2]
    px1, px2 = calib.px
    py1, py2 = calib.py
    dx1, dx2 = (10 ** calib.dx) if calib.xlog else calib.dx
    dy1, dy2 = (10 ** calib.dy) if calib.ylog else calib.dy

    fig = px.imshow(img_rgb, title="Calibration check — blue=x-axis, red=y-axis")
    fig.update_layout(
        coloraxis_showscale=False,
        margin=dict(l=0, r=0, t=40, b=0),
        xaxis_title="pixel x",
        yaxis_title="pixel y",
        shapes=[
            # vertical lines at x-axis calibration pixels
            dict(type="line", x0=px1, x1=px1, y0=0, y1=h,
                 line=dict(color="blue", width=1.5, dash="dash")),
            dict(type="line", x0=px2, x1=px2, y0=0, y1=h,
                 line=dict(color="blue", width=1.5, dash="dash")),
            # horizontal lines at y-axis calibration pixels
            dict(type="line", x0=0, x1=w, y0=py1, y1=py1,
                 line=dict(color="red", width=1.5, dash="dash")),
            dict(type="line", x0=0, x1=w, y0=py2, y1=py2,
                 line=dict(color="red", width=1.5, dash="dash")),
        ],
    )

    # labels at image edges
    fig.add_trace(go.Scatter(
        x=[px1, px2], y=[h * 0.02, h * 0.02],
        mode="text",
        text=[f"x={dx1:g}", f"x={dx2:g}"],
        textfont=dict(color="blue", size=11),
        showlegend=False,
    ))
    fig.add_trace(go.Scatter(
        x=[w * 0.01, w * 0.01], y=[py1, py2],
        mode="text",
        text=[f"y={dy1:g}", f"y={dy2:g}"],
        textfont=dict(color="red", size=11),
        showlegend=False,
    ))

    fig.show(renderer="iframe")


def make_calibration(
    px1, px2,   # pixel x of two known x-axis points
    py1, py2,   # pixel y of two known y-axis points
    dx1, dx2,   # data values at those x-axis pixels
    dy1, dy2,   # data values at those y-axis pixels
    xlog=False,
    ylog=False,
) -> AxisCalibration:
    """
    Build an AxisCalibration from pixel coordinates read off the Plotly hover tooltip.

    Workflow:
      1. Call show_pdf_page() and zoom into the plot.
      2. Hover over two known x-axis tick marks — note their pixel x values (px1, px2)
         and their data values (dx1, dx2).
      3. Hover over two known y-axis tick marks — note their pixel y values (py1, py2)
         and their data values (dy1, dy2).
      4. Pass all eight values here along with xlog/ylog flags.

    Example:
      calib = make_calibration(
          px1=210, px2=980,   dx1=1.2,   dx2=10.0,  xlog=True,
          py1=80,  py2=750,   dy1=1e-39, dy2=1e-45, ylog=True,
      )
    """
    return AxisCalibration(
        [px1, px2], [py1, py2],
        [dx1, dx2], [dy1, dy2],
        xlog=xlog, ylog=ylog,
    )


def calibrate_axes(crop: np.ndarray) -> AxisCalibration:
    """Interactively calibrate axes by clicking known points. Returns AxisCalibration."""
    print("\nClick 2 points on the X-axis, then 2 points on the Y-axis.")
    pts = _click_points(
        crop, 4, "Calibrate axes",
        "Click: X-axis pt 1, X-axis pt 2, Y-axis pt 1, Y-axis pt 2"
    )

    px1, _ = pts[0]
    px2, _ = pts[1]
    _, py1 = pts[2]
    _, py2 = pts[3]

    def ask(prompt):
        while True:
            try:
                return float(input(prompt))
            except ValueError:
                print("  Enter a numeric value.")

    print("Enter the data values for each clicked point:")
    dx1 = ask(f"  X-axis pt 1 (pixel x={px1}): ")
    dx2 = ask(f"  X-axis pt 2 (pixel x={px2}): ")
    dy1 = ask(f"  Y-axis pt 1 (pixel y={py1}): ")
    dy2 = ask(f"  Y-axis pt 2 (pixel y={py2}): ")

    xlog = input("Is the X-axis logarithmic? [y/N]: ").strip().lower() == "y"
    ylog = input("Is the Y-axis logarithmic? [y/N]: ").strip().lower() == "y"

    return AxisCalibration([px1, px2], [py1, py2], [dx1, dx2], [dy1, dy2], xlog, ylog)

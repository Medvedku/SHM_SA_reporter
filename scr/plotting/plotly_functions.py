import numpy as np
import pandas as pd
import json
import plotly.io as pio
from pathlib import Path
import plotly.graph_objects as go
from scipy.stats import gaussian_kde
from plotly.subplots import make_subplots
import os

# Project paths from config
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = PROJECT_ROOT / "config" / "path.json"
if CONFIG_PATH.exists():
    with open(CONFIG_PATH, "r") as fh:
        _cfg = json.load(fh)
else:
    _cfg = {}

PLOTS_DIR = PROJECT_ROOT / _cfg.get("plots_dir", "plots")

def _ensure_plot_path():
    try:
        PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass


# # Assuming this file lives in: <project_root>/scr/plotting/plot_functions.py
# PROJECT_ROOT = Path(__file__).resolve().parents[2]
# CONFIG_PATH = PROJECT_ROOT / "config" / "path.json"

# with open(CONFIG_PATH, "r") as f:
#     paths = json.load(f)

# PLOT_PATH  = PROJECT_ROOT / paths["plots_dir"]

# ============================================================
#  GLOBAL MAPPINGS
# ============================================================

strain_temp_map = {
    "sst_hub1": {"S27": "T4", "S28": "T5", "S29": "T6"},
    "sst_hub2": {s: "T1" for s in ["S7","S8","S9","S10","S11","S12","S13","S14"]},
    "sst_hub3": {s: "T2" for s in ["S15","S16","S17","S18"]},
    "sst_hub4": {s: "T3" for s in ["S19","S20","S21","S22","S23","S24","S25","S26"]},
}

sensor_color_mapping = {
    # ==== Temperature sensors ====
    'T1': '#bf4054ff',
    'T2': '#862d3bff',
    'T3': '#d27987ff',
    'T4': '#d29779ff',
    'T5': '#bf6a40ff',
    'T6': '#864a2dff',

    # ==== Accelerometers ====
    'A30': '#e6196eff',
    'A31': '#19c3e6ff',
    'A32': '#e65d19ff',
    'A33': '#16cc62ff',
    'A34': '#196ee6ff',
    'A35': '#e6b219ff',

    # ==== Strain sensors ====
    'S7':  '#2d8652ff',
    'S8':  '#b3e6c8ff',
    'S9':  '#79d29eff',
    'S10': '#40bf75ff',
    'S11': '#b3c8e6ff',
    'S12': '#799ed2ff',
    'S13': '#2d5286ff',
    'S14': '#4075bfff',
    'S15': '#e6d9b3ff',
    'S16': '#866f2dff',
    'S17': '#bf9f40ff',
    'S18': '#d2bc79ff',
    'S19': '#a440bfff',
    'S20': '#bf79d2ff',
    'S21': '#732d86ff',
    'S22': '#b3dce6ff',
    'S23': '#79c3d2ff',
    'S24': '#dbb3e6ff',
    'S25': '#2d7686ff',
    'S26': '#40a9bfff',
    'S27': '#79d2b8ff',
    'S28': '#40bf99ff',
    'S29': '#2d866bff'
}

sensor_legend_mapping = {
    # ==== Temperatures (Arch) ====
    "T1": "T1 (North)",
    "T2": "T2 (Middle)",
    "T3": "T3 (South)",

    # ==== Temperatures (Column) ====
    "T4": "T4 (Bottom)",
    "T5": "T5 (Middle)",
    "T6": "T6 (Top)",

    # ==== Strain sensors ====
    "S7":  "Arch, Section 1 – Top",
    "S8":  "Arch, Section 1 – Diagonal",
    "S9":  "Arch, Section 1 – Bottom Right",
    "S10": "Arch, Section 1 – Bottom Left",
    "S11": "Arch, Section 2 – Diagonal",
    "S12": "Arch, Section 2 – Bottom Right",
    "S13": "Arch, Section 2 – Top",
    "S14": "Arch, Section 2 – Bottom Left",
    "S15": "Arch, Section 3 – Diagonal",
    "S16": "Arch, Section 3 – Top",
    "S17": "Arch, Section 3 – Bottom Left",
    "S18": "Arch, Section 3 – Bottom Right",
    "S19": "Arch, Section 5 – Bottom Left",
    "S20": "Arch, Section 5 – Bottom Right",
    "S21": "Arch, Section 5 – Top",
    "S22": "Arch, Section 4 – Diagonal",
    "S23": "Arch, Section 4 – Bottom Right",
    "S24": "Arch, Section 5 – Diagonal",
    "S25": "Arch, Section 4 – Top",
    "S26": "Arch, Section 4 – Bottom Left",
    "S27": "Column – Bottom",
    "S28": "Column – Middle",
    "S29": "Column – Top",

    # ==== Accelerometers ====
    'A30': 'Arch (North)',
    'A31': 'Arch (Middle)',
    'A32': 'Arch (South)',
    'A33': 'Column (Bottom)',
    'A34': 'Column (Middle)',
    'A35': 'Column (Top)'
}


pio.templates["shm"] = pio.templates["ggplot2"]

# pio.templates["shm"].layout.font = dict(
#     family="Montserrat, sans-serif",
#     size=12,
#     color="#222222",
# )

font_style1 = 'Courier New, monospace'
font_style2 = 'Montserrat, sans-serif'

pio.templates["shm"].layout.font = dict(
    family=font_style1,
    size=12,
    color="#222222",
)

pio.templates["shm"].layout.title = dict(
    font=dict(size=22),
    x=0.02,
    xanchor="left",
)

pio.templates["shm"].layout.legend = dict(
    font=dict(size=11),
    orientation="h",
    x=1,
    xanchor="right",
    y=1.025,
    yanchor="bottom",
)

pio.templates["shm"].layout.hoverlabel = dict(
    font=dict(
        family=font_style1,
        size=11,
        color="#222222",
    ),
    bgcolor="rgba(255,255,255,0.95)",
    bordercolor="#cccccc",
)

# Activate globally
pio.templates.default = "shm"


# ---- SAFETY COLOR FIX ----
def fix_color(c):
    """
    Ensures color is valid for Plotly.
    Accepts #RRGGBBAA or #RRGGBB or anything → always returns #RRGGBB.
    """
    if c is None:
        return "#000000"

    if isinstance(c, str) and c.startswith("#"):
        # If hex has alpha (8-digit), strip to 6-digit
        if len(c) >= 7:
            return c[:7]    # #RRGGBB
        else:
            return "#000000"

    # fallback
    return "#000000"


def temps_col_plotly(con, show=True, save=False, filename="temps_col_plotly.html", bin_time=15):
    """
    Plotly version of Column Temperatures (T4, T5, T6)
    Uses full available weekly range from DuckDB.
    """

    # --- Auto detect week range ---
    row = con.execute("""
        SELECT MIN(datetime), MAX(datetime)
        FROM sst_hub1
    """).fetchone()

    start_dt, end_dt = row[0], row[1]

    # --- Query hourly aggregated data ---
    query = f"""
        SELECT
            TIMESTAMP '1970-01-01'
            + FLOOR(EXTRACT(EPOCH FROM datetime) / ({bin_time} * 60)) * ({bin_time} * 60) * INTERVAL '1 second'
            AS dt_XYmin,

            AVG(T4) AS T4,
            AVG(T5) AS T5,
            AVG(T6) AS T6

        FROM sst_hub1
        WHERE datetime BETWEEN '{start_dt}' AND '{end_dt}'
        GROUP BY dt_XYmin
        ORDER BY dt_XYmin
    """


    df = con.execute(query).df()

    if df.empty:
        print("No data found for temps_col_plotly.")
        return None

    df["dt_XYmin"] = pd.to_datetime(df["dt_XYmin"])

    # --- Build Figure ---
    fig = go.Figure()

    for s in ["T4", "T5", "T6"]:
        color_raw = sensor_color_mapping.get(s, "#000000")
        color = fix_color(color_raw)

        fig.add_trace(
            go.Scatter(
                x=df["dt_XYmin"],
                y=df[s],
                mode="lines",
                name=sensor_legend_mapping.get(s, s),
                line=dict(width=2, color=color),
                hovertemplate="%{x|%H:%M}<br>%{y:.2f} °C<extra></extra>"
            )
        )

    # --- Layout ---
    fig.update_layout(
        title="Column A7 – Temperatures<br><sup>T4, T5, T6 (hourly mean)</sup>",
        # template="plotly_white",
        xaxis=dict(
            tickformat="%d. %b.",
            showgrid=True,
            gridcolor="rgba(0,0,0,0.12)",
        ),
        yaxis=dict(
            title="Temperature [°C]",
            showgrid=True,
            gridcolor="rgba(0,0,0,0.12)",
        ),
        # legend=dict(
        #     orientation="h",
        #     yanchor="bottom",
        #     y=1.05,
        #     xanchor="center",
        #     x=0.5,
        # ),
        margin=dict(l=40, r=20, t=80, b=40),
    )
    

    # --- Save if needed ---
    if save:
        _ensure_plot_path()
        if filename is None:
            filename = "temps_col_plotly.html"
        outpath = PLOTS_DIR / Path(filename).name
        if outpath.suffix == ".html":
            fig.write_html(str(outpath), include_plotlyjs="cdn")
        else:
            fig.write_image(str(outpath))  # Requires kaleido

    if show:
        fig.show()

    return None


def temps_arch_plotly(con, show=True, save=False, filename="temps_arch_plotly.html", bin_time=15):
    """
    Plotly version of Arch Temperatures (T1, T2, T3)
    - T1 from sst_hub2
    - T2 from sst_hub3
    - T3 from sst_hub4
    Uses full available weekly range from DuckDB.
    """

    # --- Auto detect week range across arch tables ---
    row = con.execute("""
        SELECT
            LEAST(
                (SELECT MIN(datetime) FROM sst_hub2),
                (SELECT MIN(datetime) FROM sst_hub3),
                (SELECT MIN(datetime) FROM sst_hub4)
            ) AS start_dt,
            GREATEST(
                (SELECT MAX(datetime) FROM sst_hub2),
                (SELECT MAX(datetime) FROM sst_hub3),
                (SELECT MAX(datetime) FROM sst_hub4)
            ) AS end_dt
    """).fetchone()

    start_dt, end_dt = row[0], row[1]

    # --- Queries for each sensor ---
    queries = {
        "T1": f"""
            SELECT
                TIMESTAMP '1970-01-01'
                + FLOOR(EXTRACT(EPOCH FROM datetime) / ({bin_time} * 60)) * ({bin_time} * 60) * INTERVAL '1 second'
                AS dt_XYmin,
                AVG(T1) AS val
            FROM sst_hub2
            WHERE datetime BETWEEN ? AND ?
            GROUP BY dt_XYmin
            ORDER BY dt_XYmin
        """,

        "T2": f"""
            SELECT
                TIMESTAMP '1970-01-01'
                + FLOOR(EXTRACT(EPOCH FROM datetime) / ({bin_time} * 60)) * ({bin_time} * 60) * INTERVAL '1 second'
                AS dt_XYmin,
                AVG(T2) AS val
            FROM sst_hub3
            WHERE datetime BETWEEN ? AND ?
            GROUP BY dt_XYmin
            ORDER BY dt_XYmin
        """,

        "T3": f"""
            SELECT
                TIMESTAMP '1970-01-01'
                + FLOOR(EXTRACT(EPOCH FROM datetime) / ({bin_time} * 60)) * ({bin_time} * 60) * INTERVAL '1 second'
                AS dt_XYmin,
                AVG(T3) AS val
            FROM sst_hub4
            WHERE datetime BETWEEN ? AND ?
            GROUP BY dt_XYmin
            ORDER BY dt_XYmin
        """,
    }


    fig = go.Figure()
    has_data = False

    for sensor, query in queries.items():
        df = con.execute(query, [start_dt, end_dt]).df()
        if df.empty:
            continue

        has_data = True
        df["dt_XYmin"] = pd.to_datetime(df["dt_XYmin"])

        color_raw = sensor_color_mapping.get(sensor, "#000000")
        color = fix_color(color_raw)

        fig.add_trace(
            go.Scatter(
                x=df["dt_XYmin"],
                y=df["val"],
                mode="lines",
                name=sensor_legend_mapping.get(sensor, sensor),
                line=dict(width=2, color=color),
                hovertemplate="%{x|%H:%M}<br>%{y:.2f} °C<extra></extra>"
            )
        )

    if not has_data:
        print("No data found for temps_arch_plotly.")
        return None

    # --- Layout (kept consistent with temps_col_plotly) ---
    fig.update_layout(
        title="Arch – Temperatures<br><sup>T1, T2, T3 hourly mean</sup>",
        # template="plotly_white",
        xaxis=dict(
            tickformat="%d. %b",
            showgrid=True,
            gridcolor="rgba(0,0,0,0.12)",
        ),
        yaxis=dict(
            title="Temperature [°C]",
            showgrid=True,
            gridcolor="rgba(0,0,0,0.12)",
        ),
        margin=dict(l=40, r=20, t=80, b=40),
    )

    # --- Save if needed ---
    if save:
        _ensure_plot_path()
        if filename is None:
            filename = "temps_arch_plotly.html"
        outpath = PLOTS_DIR / Path(filename).name
        if outpath.suffix == ".html":
            fig.write_html(str(outpath), include_plotlyjs="cdn")
        else:
            fig.write_image(str(outpath))  # requires kaleido

    if show:
        fig.show()

    return None


def strain_temp_plotly(
    con,
    sensor_id,
    start_dt=None,
    end_dt=None,
    show=True,
    save=False,
    filename=None,
    bin_time=15,
):
    """
    Plotly version of strain + temperature plot.
    - hourly MEDIAN
    - strain converted to epsilon [mm/m]
    - dual y-axis
    """

    # --------------------------------------------------
    # 1) Determine hub and temp sensor
    # --------------------------------------------------
    hub = None
    temp_id = None
    for hub_name, mapping in strain_temp_map.items():
        if sensor_id in mapping:
            hub = hub_name
            temp_id = mapping[sensor_id]
            break

    if hub is None:
        print(f"Sensor {sensor_id} not found in any sst_hub table.")
        return None

    # --------------------------------------------------
    # 2) Resolve time window (weekly DB → auto)
    # --------------------------------------------------
    if end_dt is None:
        end_dt = con.execute(
            f"SELECT MAX(datetime) FROM {hub}"
        ).fetchone()[0]

    if end_dt is None:
        print(f"No data for {sensor_id}")
        return None

    end_dt = pd.to_datetime(end_dt)

    if start_dt is None:
        start_dt = end_dt - pd.Timedelta(days=7)
    else:
        start_dt = pd.to_datetime(start_dt)

    # --------------------------------------------------
    # 3) Query aggregated data
    # --------------------------------------------------

    query = f"""
        SELECT
            TIMESTAMP '1970-01-01'
            + FLOOR(EXTRACT(EPOCH FROM datetime) / ({bin_time} * 60)) * ({bin_time} * 60) * INTERVAL '1 second'
            AS dt_XYmin,
            MEDIAN({sensor_id}) AS strain_raw,
            MEDIAN({temp_id})   AS temp
        FROM {hub}
        WHERE datetime BETWEEN '{start_dt}' AND '{end_dt}'
        GROUP BY dt_XYmin
        ORDER BY dt_XYmin
    """

    df = con.execute(query).df()

    if df.empty:
        print(f"No recent data for {sensor_id}")
        return None

    df["dt_XYmin"] = pd.to_datetime(df["dt_XYmin"])

    # --------------------------------------------------
    # 4) Strain conversion → epsilon [mm/m]
    # --------------------------------------------------
    CALIB = 3.11e-9
    df["epsilon_mm"] = df["strain_raw"] * CALIB * 1000.0

    # --------------------------------------------------
    # Colors & labels
    # --------------------------------------------------
    strain_color = fix_color(sensor_color_mapping.get(sensor_id, "#000000"))
    temp_color   = fix_color(sensor_color_mapping.get(temp_id, "#444444"))

    strain_label = sensor_legend_mapping.get(sensor_id, sensor_id)
    temp_label   = sensor_legend_mapping.get(temp_id, temp_id)

    # --------------------------------------------------
    # Plotly figure
    # --------------------------------------------------
    fig = go.Figure()

    # Strain (primary y-axis)
    fig.add_trace(
        go.Scatter(
            x=df["dt_XYmin"],
            y=df["epsilon_mm"],
            mode="lines",
            name=sensor_id,
            line=dict(color=strain_color, width=2),
            yaxis="y",
            hovertemplate="%{x|%H:%M}<br>%{y:.3f} mm/m<extra></extra>"
        )
    )

    # Temperature (secondary y-axis)
    fig.add_trace(
        go.Scatter(
            x=df["dt_XYmin"],
            y=df["temp"],
            mode="lines",
            name=temp_label,
            line=dict(color=temp_color, width=1.5),
            yaxis="y2",
            hovertemplate="%{x|%H:%M}<br>%{y:.2f} °C<extra></extra>",
        )
    )

    # --------------------------------------------------
    # Layout
    # --------------------------------------------------
    fig.update_layout(
        title=f"{strain_label}<br>"
              f"<sup>Strain {sensor_id} & Temp {temp_id} "
              f"({bin_time} min median)</sup>",
        # template="plotly_white",
        hovermode="x unified",
        xaxis=dict(
            title="Time",
            tickformat="%d. %b",
            showgrid=True,
            gridcolor="rgba(0,0,0,0.12)",
        ),
        yaxis=dict(
            title=r"ε [mm/m]",
            showgrid=True,
            gridcolor="rgba(0,0,0,0.12)",
        ),
        yaxis2=dict(
            title="Temperature [°C]",
            overlaying="y",
            side="right",
            showgrid=False,
        ),
        margin=dict(l=60, r=60, t=90, b=50),
    )

    # --------------------------------------------------
    # Save / show
    # --------------------------------------------------
    if save:
        _ensure_plot_path()
        if filename is None:
            filename = f"{sensor_id}_strain_temp.html"
        outpath = PLOTS_DIR / Path(filename).name
        if outpath.suffix == ".html":
            fig.write_html(str(outpath), include_plotlyjs="cdn")
        else:
            fig.write_image(str(outpath))  # kaleido

    if show:
        fig.show()

    return None


def fft_with_KDE_plotly(
    con,
    sensor_id,
    threshold=0.08,
    start_dt=None,
    end_dt=None,
    show=True,
    save=False,
    filename=None,
):
    """
    Plotly version of FFT scatter (freq vs amp) + KDE on secondary y-axis.
    """

    # --------------------------------------------------
    # Resolve time window (same logic as matplotlib)
    # --------------------------------------------------
    if end_dt is None:
        query_max = f"""
            SELECT MAX(datetime) FROM (
                SELECT datetime FROM fft_hub1 WHERE sensor_id = '{sensor_id}'
                UNION ALL
                SELECT datetime FROM fft_hub2 WHERE sensor_id = '{sensor_id}'
                UNION ALL
                SELECT datetime FROM fft_hub3 WHERE sensor_id = '{sensor_id}'
                UNION ALL
                SELECT datetime FROM fft_hub4 WHERE sensor_id = '{sensor_id}'
            )
        """
        end_dt = con.execute(query_max).fetchone()[0]
        if end_dt is None:
            print(f"No FFT data found for {sensor_id}")
            return None

    end_dt = pd.to_datetime(end_dt)

    if start_dt is None:
        start_dt = end_dt - pd.Timedelta(days=7)
    else:
        start_dt = pd.to_datetime(start_dt)

    # --------------------------------------------------
    # Query + unnest
    # --------------------------------------------------
    query = f"""
        WITH raw_fft AS (
             SELECT * FROM fft_hub1 WHERE sensor_id = '{sensor_id}'
             UNION ALL
             SELECT * FROM fft_hub2 WHERE sensor_id = '{sensor_id}'
             UNION ALL
             SELECT * FROM fft_hub3 WHERE sensor_id = '{sensor_id}'
             UNION ALL
             SELECT * FROM fft_hub4 WHERE sensor_id = '{sensor_id}'
        ),
        flattened AS (
            SELECT
                unnest(fft_freqs) AS freq,
                unnest(fft_amps)  AS amp
            FROM raw_fft
            WHERE datetime BETWEEN '{start_dt}' AND '{end_dt}'
        )
        SELECT freq, amp
        FROM flattened
        WHERE amp >= {threshold}
    """

    flat = con.execute(query).df()

    if flat.empty:
        print(f"No FFT peaks above threshold for {sensor_id}")
        return None

    # --------------------------------------------------
    # KDE
    # --------------------------------------------------
    freq_vals = flat["freq"].values
    kde = gaussian_kde(freq_vals)

    xs = np.linspace(freq_vals.min(), freq_vals.max(), 500)
    ys = kde(xs)

    idx_max = np.argmax(ys)
    f_peak = xs[idx_max]

    # --------------------------------------------------
    # Colors & labels
    # --------------------------------------------------
    raw_color = sensor_color_mapping.get(sensor_id, "#000000")
    color = fix_color(raw_color)
    label = sensor_legend_mapping.get(sensor_id, sensor_id)


    # --------------------------------------------------
    # Plotly figure
    # --------------------------------------------------
    fig = go.Figure()

    # Scatter (freq vs amp)
    fig.add_trace(
        go.Scatter(
            x=flat["freq"],
            y=flat["amp"],
            mode="markers",
            name='FFT',
            marker=dict(
                size=6,
                color=color,
                opacity=0.2,
                # symbol="o"
            ),
        )
    )

    # KDE (secondary y-axis)
    fig.add_trace(
        go.Scatter(
            x=xs,
            y=ys,
            mode="lines",
            name="KDE",
            yaxis="y2",
            line=dict(
                color="#bbbbbb",
                width=2,
            ),
        )
    )

    # Peak line as a trace (legend toggle works)
    fig.add_trace(
        go.Scatter(
            x=[f_peak, f_peak],
            y=[flat["amp"].min(), flat["amp"].max()],
            mode="lines",
            name=f"Peak @ {f_peak:.2f} Hz",
            line=dict(color="#888888", width=1, dash="dash"),
            hoverinfo="skip",
        )
    )


    # --------------------------------------------------
    # Layout
    # --------------------------------------------------
    fig.update_layout(
        title=f"{sensor_id} – FFT + KDE<br>"
              f"<sup>{label} – peaks ≥ {threshold}, "
              f"(last 7 days)</sup>",
        xaxis=dict(title="Frequency [Hz]"),
        yaxis=dict(title="Amplitude"),
        yaxis2=dict(
            title="KDE density",
            overlaying="y",
            side="right",
            showgrid=False,
        ),
        margin=dict(l=60, r=60, t=90, b=50),
    )

    # --------------------------------------------------
    # Save / show
    # --------------------------------------------------
    if save:
        _ensure_plot_path()
        if filename is None:
            filename = f"{sensor_id}_fft_kde.html"
        outpath = PLOTS_DIR / Path(filename).name
        if outpath.suffix == ".html":
            fig.write_html(str(outpath), include_plotlyjs="cdn")
        else:
            fig.write_image(str(outpath))  # needs kaleido

    if show:
        fig.show()

    return None


def accel_v_daily_grid_plotly(
    con,
    sensor_id,
    start_dt=None,
    end_dt=None,
    show=True,
    save=False,
    filename=None,
):
    """
    Daily resultant acceleration grid (Plotly).
    - Max 7 days
    - Alternating y-axis side (left / right)
    - Date labels on y-axis
    - Only min/max y-ticks
    - Min–max band + average line
    """

    # --------------------------------------------------
    # Resolve time window
    # --------------------------------------------------
    if end_dt is None:
        end_dt = con.execute(
            "SELECT MAX(datetime) FROM accel_all"
        ).fetchone()[0]

    if end_dt is None:
        print("No acceleration data found.")
        return None

    end_dt = pd.to_datetime(end_dt)

    if start_dt is None:
        start_dt = end_dt - pd.Timedelta(days=7)
    else:
        start_dt = pd.to_datetime(start_dt)

    start_day = start_dt.normalize()
    end_day   = end_dt.normalize()

    total_days = (end_day - start_day).days + 1
    if total_days <= 0:
        print("Invalid time window.")
        return None

    if total_days > 7:
        start_day = end_day - pd.Timedelta(days=6)
        total_days = 7

    # --------------------------------------------------
    # Identify accel columns
    # --------------------------------------------------
    ax_cols = [f"{sensor_id}_x", f"{sensor_id}_y", f"{sensor_id}_z"]
    schema = con.execute("DESCRIBE accel_all").df()["column_name"].tolist()

    for c in ax_cols:
        if c not in schema:
            print(f"Column {c} not found in accel_all.")
            return None

    # --------------------------------------------------
    # Aggregate by minute
    # --------------------------------------------------
    query = f"""
        SELECT
            date_trunc('minute', datetime) AS dt_min,
            AVG(SQRT({ax_cols[0]}*{ax_cols[0]} +
                     {ax_cols[1]}*{ax_cols[1]} +
                     {ax_cols[2]}*{ax_cols[2]})) AS v_avg,
            MIN(SQRT({ax_cols[0]}*{ax_cols[0]} +
                     {ax_cols[1]}*{ax_cols[1]} +
                     {ax_cols[2]}*{ax_cols[2]})) AS v_min,
            MAX(SQRT({ax_cols[0]}*{ax_cols[0]} +
                     {ax_cols[1]}*{ax_cols[1]} +
                     {ax_cols[2]}*{ax_cols[2]})) AS v_max
        FROM accel_all
        WHERE datetime BETWEEN '{start_day}' AND '{end_day + pd.Timedelta(days=1)}'
        GROUP BY dt_min
        ORDER BY dt_min
    """

    df = con.execute(query).df()
    if df.empty:
        print("No acceleration data in window.")
        return None

    df["datetime"] = pd.to_datetime(df["dt_min"])
    df = df.set_index("datetime")

    # --------------------------------------------------
    # Split by day
    # --------------------------------------------------
    days = []
    labels = []

    for i in range(total_days):
        d0 = start_day + pd.Timedelta(days=i)
        d1 = d0 + pd.Timedelta(days=1)
        chunk = df[(df.index >= d0) & (df.index < d1)]
        days.append(chunk)
        labels.append(d0.strftime("%d. %b."))

    # --------------------------------------------------
    # Colors
    # --------------------------------------------------
    raw_color = sensor_color_mapping.get(sensor_id, "#000000")
    color = fix_color(raw_color)
    label = sensor_legend_mapping.get(sensor_id, sensor_id)


    def hex_to_rgba(hex_color, alpha):
        h = hex_color.lstrip("#")
        r = int(h[0:2], 16)
        g = int(h[2:4], 16)
        b = int(h[4:6], 16)
        return f"rgba({r},{g},{b},{alpha})"

    band_color = hex_to_rgba(color, 0.25)

    # --------------------------------------------------
    # Plot
    # --------------------------------------------------
    fig = make_subplots(
        rows=total_days,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.01,
    )

    for i, day_df in enumerate(days, start=1):
        if day_df.empty:
            continue

        t_hours = (
            (day_df.index - day_df.index.normalize())
            / pd.Timedelta(hours=1)
        )

        # min baseline
        fig.add_trace(
            go.Scatter(
                x=t_hours,
                y=day_df["v_min"],
                mode="lines",
                line=dict(width=0),
                hoverinfo="skip",
                showlegend=False,
            ),
            row=i,
            col=1,
        )

        # max band
        fig.add_trace(
            go.Scatter(
                x=t_hours,
                y=day_df["v_max"],
                mode="lines",
                fill="tonexty",
                fillcolor=band_color,
                line=dict(width=0),
                hoverinfo="skip",
                showlegend=False,
            ),
            row=i,
            col=1,
        )

        # avg line
        fig.add_trace(
            go.Scatter(
                x=t_hours,
                y=day_df["v_avg"],
                mode="lines",
                line=dict(color=color, width=2),
                hovertemplate="%{x:.1f} h<br>%{y:.5f}<extra></extra>",
                #  %{x|%H:%M}<
                showlegend=False,
            ),
            row=i,
            col=1,
        )

        # y-axis formatting
        y_min = float(day_df["v_min"].min())
        y_max = float(day_df["v_max"].max())

        fig.update_yaxes(
            side="right" if i % 2 == 0 else "left",
            title_text=labels[i - 1],
            title_standoff=10,
            tickmode="array",
            tickvals=[y_min, y_max],
            tickformat=".3f",
            row=i,
            col=1,
        )

        fig.update_xaxes(
            range=[0, 24],
            tickmode="linear",
            tick0=0,
            dtick=1,
            row=i,
            col=1,
        )

    # x-axis title only on last subplot
    fig.update_xaxes(
        title_text="Hour of day",
        row=total_days,
        col=1,
    )

    fig.update_layout(
        title=f"{sensor_id} – Daily Resultant Acceleration<br>"
              f"<sup>{label} (last 7 days)",
        height=100 + 90 * total_days,
        margin=dict(l=60, r=60, t=90, b=50),
        showlegend=False,
        # template="plotly_white",
    )

    if save:
        _ensure_plot_path()
        if filename is None:
            filename = f"{sensor_id}_daily_v_grid.html"
        outpath = PLOTS_DIR / Path(filename).name
        if outpath.suffix == ".html":
            fig.write_html(str(outpath), include_plotlyjs="cdn")
        else:
            fig.write_image(str(outpath))

    if show:
        fig.show()

    return None




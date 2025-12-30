import os
import json
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
import matplotlib.ticker as mticker
import pandas as pd
import gc

# ============================================================
#  CONFIG & PATHS (RELATIVE TO PROJECT ROOT)
# ============================================================

# Assuming this file lives in: <project_root>/scr/plotting/plot_functions.py
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = PROJECT_ROOT / "config" / "path.json"

with open(CONFIG_PATH, "r") as f:
    paths = json.load(f)

PLOT_PATH  = PROJECT_ROOT / paths["plots_dir"]
FONT_DIR   = PROJECT_ROOT / paths["font_dir"]

# ============================================================
#  FONTS
# ============================================================

FONT_REGULAR = FONT_DIR / "Montserrat-Regular.ttf"
FONT_BLACK   = FONT_DIR / "Montserrat-Black.ttf"
FONT_MEDIUM  = FONT_DIR / "Montserrat-Medium.ttf"
FONT_LIGHT   = FONT_DIR / "Montserrat-Light.ttf"

for fpath in [FONT_REGULAR, FONT_BLACK, FONT_MEDIUM, FONT_LIGHT]:
    font_manager.fontManager.addfont(str(fpath))

plt.rcParams["font.family"] = "Montserrat"
plt.rcParams["font.size"] = 12

TITLE_FONT  = font_manager.FontProperties(fname=str(FONT_MEDIUM), size=14)
LABEL_FONT  = font_manager.FontProperties(fname=str(FONT_REGULAR), size=12)
LEGEND_FONT = font_manager.FontProperties(fname=str(FONT_LIGHT),  size=11)

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

# ============================================================
#  HELPERS
# ============================================================

def _ensure_plot_path():
    PLOT_PATH.mkdir(parents=True, exist_ok=True)

def set_fonts(ax):
    """Apply consistent fonts to axis, legend, ticks."""
    ax.xaxis.label.set_fontproperties(LABEL_FONT)
    ax.yaxis.label.set_fontproperties(LABEL_FONT)

    for tick in ax.get_xticklabels():
        tick.set_fontproperties(LEGEND_FONT)
    for tick in ax.get_yticklabels():
        tick.set_fontproperties(LEGEND_FONT)

    leg = ax.get_legend()
    if leg is not None:
        for text in leg.get_texts():
            text.set_fontproperties(LEGEND_FONT)

def resolve_time_window_single_table(con, table, start_dt=None, end_dt=None):
    """
    Resolve a (start_dt, end_dt) window based on a single table.
    If end_dt is None -> use MAX(datetime).
    If start_dt is None -> end_dt - 7 days.
    """
    if end_dt is None:
        end_dt = con.execute(f"SELECT MAX(datetime) FROM {table}").fetchone()[0]
        if end_dt is None:
            raise ValueError(f"Table {table} is empty or has no datetime.")
    end_dt = pd.to_datetime(end_dt)

    if start_dt is None:
        start_dt = end_dt - pd.Timedelta(days=7)
    else:
        start_dt = pd.to_datetime(start_dt)

    return start_dt, end_dt

def resolve_time_window_multi_tables(con, tables, start_dt=None, end_dt=None):
    """
    Resolve time window using MAX(datetime) across multiple tables.
    'tables' is a list of table names.
    """
    if end_dt is None:
        max_expr = "GREATEST(" + ",".join(
            [f"(SELECT MAX(datetime) FROM {t})" for t in tables]
        ) + ") AS max_dt"
        query = f"SELECT {max_expr}"
        end_dt = con.execute(query).fetchone()[0]
        if end_dt is None:
            raise ValueError(f"No datetime data found across tables: {tables}")
    end_dt = pd.to_datetime(end_dt)

    if start_dt is None:
        start_dt = end_dt - pd.Timedelta(days=7)
    else:
        start_dt = pd.to_datetime(start_dt)

    return start_dt, end_dt


# ============================================================
#  TEMPERATURE PLOTS
# ============================================================

def temps_col(con, start_dt=None, end_dt=None, show=True, save=True, filename="temps_col.png"):
    """
    Column temperatures (T4, T5, T6 from sst_hub1) for a given time window.

    Args:
        con: DuckDB connection
        start_dt, end_dt: pandas/str datetimes or None
    """
    import matplotlib.dates as mdates

    start_dt, end_dt = resolve_time_window_single_table(con, "sst_hub1", start_dt, end_dt)

    query = f"""
        SELECT date_trunc('hour', datetime) AS dt_hour,
               AVG(T4) AS T4,
               AVG(T5) AS T5,
               AVG(T6) AS T6
        FROM sst_hub1
        WHERE datetime BETWEEN '{start_dt}' AND '{end_dt}'
        GROUP BY dt_hour
        ORDER BY dt_hour
    """
    df_hour = con.execute(query).df()

    if df_hour.empty:
        print("No hourly aggregated data found for temps_col.")
        return None

    df_hour["dt_hour"] = pd.to_datetime(df_hour["dt_hour"])
    df_hour = df_hour.set_index("dt_hour")

    fig, ax = plt.subplots(figsize=(11, 6))

    sensors = ["T4", "T5", "T6"]
    for s in sensors:
        color = sensor_color_mapping.get(s, "#000000")
        label = sensor_legend_mapping.get(s, s)
        ax.plot(df_hour.index, df_hour[s], label=label, color=color, linewidth=2)

    ax.set_title("Column A7 – Temperatures", fontproperties=TITLE_FONT, pad=18)
    subtitle = "Temperatures T4, T5 and T6 (last week hour mean)"
    ax.text(
        0.5, 1.01, subtitle,
        transform=ax.transAxes,
        ha="center",
        fontproperties=LABEL_FONT,
        fontsize=10,
    )

    ax.set_xlabel("")
    ax.xaxis.label.set_visible(False)
    ax.set_ylabel("Temperature [°C]")
    ax.grid(True, linestyle="--", alpha=0.3)
    ax.legend()
    set_fonts(ax)

    ax.xaxis.set_major_locator(mdates.DayLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d. %b"))
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")

    if save:
        _ensure_plot_path()
        outpath = PLOT_PATH / filename
        fig.savefig(outpath, dpi=300, format="png")

    if show:
        plt.show()
    else:
        plt.close(fig)

    gc.collect()
    return None


def temps_arch(con, start_dt=None, end_dt=None, show=True, save=True, filename="temps_arch.png"):
    """
    Arch temperatures (T1 from sst_hub2, T2 from sst_hub3, T3 from sst_hub4)
    over a given time window.
    """
    import matplotlib.dates as mdates

    tables = ["sst_hub2", "sst_hub3", "sst_hub4"]
    start_dt, end_dt = resolve_time_window_multi_tables(con, tables, start_dt, end_dt)

    queries = {
        "T1": f"""
            SELECT date_trunc('hour', datetime) AS dt_hour, AVG(T1) AS T1
            FROM sst_hub2
            WHERE datetime BETWEEN '{start_dt}' AND '{end_dt}'
            GROUP BY dt_hour
            ORDER BY dt_hour
        """,
        "T2": f"""
            SELECT date_trunc('hour', datetime) AS dt_hour, AVG(T2) AS T2
            FROM sst_hub3
            WHERE datetime BETWEEN '{start_dt}' AND '{end_dt}'
            GROUP BY dt_hour
            ORDER BY dt_hour
        """,
        "T3": f"""
            SELECT date_trunc('hour', datetime) AS dt_hour, AVG(T3) AS T3
            FROM sst_hub4
            WHERE datetime BETWEEN '{start_dt}' AND '{end_dt}'
            GROUP BY dt_hour
            ORDER BY dt_hour
        """,
    }

    dfs = {}
    for sensor, query in queries.items():
        df_hour = con.execute(query).df()
        if not df_hour.empty:
            df_hour["dt_hour"] = pd.to_datetime(df_hour["dt_hour"])
            df_hour = df_hour.set_index("dt_hour")
        dfs[sensor] = df_hour

    fig, ax = plt.subplots(figsize=(11, 6))

    for sensor in ["T1", "T2", "T3"]:
        df_hour = dfs[sensor]
        if df_hour.empty:
            continue
        color = sensor_color_mapping.get(sensor, "#000000")
        label = sensor_legend_mapping.get(sensor, sensor)
        ax.plot(df_hour.index, df_hour[sensor], label=label, color=color, linewidth=2)

    ax.set_title("Arch – Temperatures", fontproperties=TITLE_FONT, pad=18)
    subtitle = "Temperatures T1, T2 and T3 (last week hour mean)"
    ax.text(
        0.5, 1.01, subtitle,
        transform=ax.transAxes,
        ha="center",
        fontproperties=LABEL_FONT,
        fontsize=10,
    )

    ax.set_xlabel("")
    ax.xaxis.label.set_visible(False)
    ax.set_ylabel("Temperature [°C]")
    ax.grid(True, linestyle="--", alpha=0.3)
    ax.legend()
    set_fonts(ax)

    ax.xaxis.set_major_locator(mdates.DayLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d. %b"))
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")

    if save:
        _ensure_plot_path()
        outpath = PLOT_PATH / filename
        fig.savefig(outpath, dpi=300, format="png")

    if show:
        plt.show()
    else:
        plt.close(fig)

    gc.collect()
    return None


# ============================================================
#  FFT + KDE PLOT
# ============================================================

def fft_with_KDE_plot(con, sensor_id, threshold=0.065,
                      start_dt=None, end_dt=None,
                      show=True, save=True):
    """
    Scatter plot of (frequency vs amplitude) for FFT peaks above threshold
    PLUS a KDE of frequency distribution on a secondary y-axis.
    Time window can be given or defaults to last 7 days across fft_hub1–4.
    """
    from scipy.stats import gaussian_kde

    # --- Resolve time window across all fft_hub tables for this sensor ---
    if end_dt is None:
        query_max = f"""
            SELECT MAX(datetime) AS max_dt
            FROM (
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

    # --- Query with unnest and threshold filter ---
    query_data = f"""
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
            SELECT unnest(fft_freqs) as freq,
                   unnest(fft_amps) as amp,
                   datetime
            FROM raw_fft
            WHERE datetime BETWEEN '{start_dt}' AND '{end_dt}'
        )
        SELECT freq, amp FROM flattened
        WHERE amp >= {threshold}
    """
    flat = con.execute(query_data).df()

    if flat.empty:
        print(f"No FFT data/peaks above threshold for {sensor_id} in given window.")
        return None

    fig, ax = plt.subplots(figsize=(11, 6))

    color = sensor_color_mapping.get(sensor_id, "#000000")
    label = sensor_legend_mapping.get(sensor_id, sensor_id)

    # Scatter
    ax.scatter(flat["freq"], flat["amp"], c=color, s=8, alpha=0.5, label=label)

    # KDE on secondary axis
    ax2 = ax.twinx()
    freq_vals = flat["freq"].values
    kde = gaussian_kde(freq_vals)
    xs = np.linspace(freq_vals.min(), freq_vals.max(), 500)
    ys = kde(xs)

    idx_max = np.argmax(ys)
    f_peak = xs[idx_max]

    ax.axvline(f_peak, color="#888888", linestyle="--", linewidth=1)
    ax.text(
        f_peak,
        flat["amp"].max(),
        f"{f_peak:.2f} Hz",
        ha="center",
        va="bottom",
        fontsize=10,
        color="#444444",
    )

    ax2.plot(xs, ys, color="#666666", linewidth=1, alpha=0.8, label="KDE")

    ax.set_title(f"{label} – FFT + KDE", fontproperties=TITLE_FONT, pad=18)
    subtitle = f"{sensor_id} – peaks above threshold = {threshold} (last 7 days)"
    ax.text(
        0.5, 1.01, subtitle,
        transform=ax.transAxes, ha="center",
        fontproperties=LABEL_FONT, fontsize=11,
    )

    ax.set_xlabel("Frequency [Hz]")
    ax.set_ylabel("Amplitude")
    ax2.set_ylabel("KDE Density")

    ax.grid(True, linestyle="--", alpha=0.3)

    set_fonts(ax)
    set_fonts(ax2)

    outname = f"{sensor_id}_fft_kde.png"
    if save:
        _ensure_plot_path()
        outpath = PLOT_PATH / outname
        fig.savefig(outpath, dpi=300, format="png")

    if show:
        plt.show()
    else:
        plt.close(fig)

    gc.collect()
    return None


# ============================================================
#  STRAIN + TEMPERATURE PLOT
# ============================================================

def strain_temp_plot(con, sensor_id, start_dt=None, end_dt=None,
                     show=True, save=True):
    """
    Plot hourly median strain (converted to epsilon mm/m) and temperature
    for a given S-sensor over a custom time window.
    """
    import matplotlib.dates as mdates

    # 1) Determine hub and temp sensor id
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

    # 2) Resolve time window for that hub
    start_dt, end_dt = resolve_time_window_single_table(con, hub, start_dt, end_dt)

    # 3) Load aggregated data
    query = f"""
        SELECT date_trunc('hour', datetime) AS dt_hour, 
               MEDIAN({sensor_id}) AS strain_raw, 
               MEDIAN({temp_id}) AS temp
        FROM {hub}
        WHERE datetime BETWEEN '{start_dt}' AND '{end_dt}'
        GROUP BY dt_hour
        ORDER BY dt_hour
    """
    df_hour = con.execute(query).df()

    if df_hour.empty:
        print(f"No recent data for {sensor_id} in given window.")
        return None

    df_hour["dt_hour"] = pd.to_datetime(df_hour["dt_hour"])
    df_hour = df_hour.set_index("dt_hour")

    # 4) Convert strain to epsilon [mm/m]
    CALIB = 3.11e-9
    df_hour["epsilon_raw"] = df_hour["strain_raw"] * CALIB
    df_hour["epsilon_mm"]  = df_hour["epsilon_raw"] * 1000.0

    fig, ax1 = plt.subplots(figsize=(11, 6))

    strain_color = sensor_color_mapping.get(sensor_id, "#000000")
    temp_color   = sensor_color_mapping.get(temp_id, "#444444")

    strain_label = sensor_legend_mapping.get(sensor_id, sensor_id)
    temp_label   = sensor_legend_mapping.get(temp_id, temp_id)

    # Strain (primary)
    ax1.plot(df_hour.index, df_hour["epsilon_mm"],
             color=strain_color, linewidth=2, label=r"$\varepsilon$")

    ax1.set_ylabel(r"$\varepsilon$ [mm/m]")
    ax1.grid(True, linestyle="--", alpha=0.3)

    # Temperature (secondary)
    ax2 = ax1.twinx()
    ax2.plot(df_hour.index, df_hour["temp"],
             color=temp_color, linewidth=1.5, label=temp_label)
    ax2.set_ylabel("T [°C]")

    title_label = strain_label
    ax1.set_title(f"{title_label}", fontproperties=TITLE_FONT, pad=18)
    subtitle = f"Strains {sensor_id} & Temp {temp_id} (last week, hour median)"
    ax1.text(
        0.5, 1.01, subtitle,
        transform=ax1.transAxes, ha="center",
        fontproperties=LABEL_FONT, fontsize=11,
    )

    ax1.xaxis.set_major_locator(mdates.DayLocator())
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%d. %b"))
    plt.setp(ax1.get_xticklabels(), rotation=45, ha="right")

    set_fonts(ax1)
    set_fonts(ax2)

    # Combined legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left")

    filename = f"{sensor_id}_strain_temp.png"
    if save:
        _ensure_plot_path()
        outpath = PLOT_PATH / filename
        fig.savefig(outpath, dpi=300, format="png")

    if show:
        plt.show()
    else:
        plt.close(fig)

    gc.collect()
    return None


# ============================================================
#  ACCEL RESULTANT DAILY GRID
# ============================================================

def accel_v_daily_grid(con, sensor_id,
                       start_dt=None, end_dt=None,
                       show=True, save=True):
    """
    Daily resultant acceleration grid for accelerometer Axx.
    - One subplot per day in the [start_dt, end_dt] window
    - X-axis: 0–23 hours
    - Filled band between v_min and v_max, line for v_avg

    If start_dt / end_dt are None, defaults to last 7 days based on accel_all.
    """
    color = sensor_color_mapping.get(sensor_id, "#000000")
    label = sensor_legend_mapping.get(sensor_id, sensor_id)

    # 1) Identify accel columns
    ax_cols = [f"{sensor_id}_x", f"{sensor_id}_y", f"{sensor_id}_z"]
    schema = con.execute("DESCRIBE accel_all").df()["column_name"].tolist()
    for c in ax_cols:
        if c not in schema:
            print(f"Column {c} not found in accel_all.")
            return None

    # 2) Resolve time window using accel_all
    start_dt, end_dt = resolve_time_window_single_table(con, "accel_all", start_dt, end_dt)

    # For daily grid we operate on date boundaries
    start_day = pd.to_datetime(start_dt).normalize()
    end_day = pd.to_datetime(end_dt).normalize()

    # Inclusive day count between start_day..end_day
    total_days = (end_day - start_day).days + 1
    if total_days <= 0:
        print("Invalid time window for accel_v_daily_grid.")
        return None

    # Ensure the grid covers at most 7 days (last 7 full days).
    MAX_DAYS = 7
    if total_days > MAX_DAYS:
        # Trim the start_day so the window is exactly MAX_DAYS ending on end_day
        start_day = end_day - pd.Timedelta(days=MAX_DAYS - 1)
        total_days = MAX_DAYS

    num_days = total_days

    # 3) Load & aggregate by minute
    query = f"""
        SELECT date_trunc('minute', datetime) as dt_min,
               AVG(SQRT({ax_cols[0]}*{ax_cols[0]} +
                        {ax_cols[1]}*{ax_cols[1]} +
                        {ax_cols[2]}*{ax_cols[2]})) as v_avg,
               MIN(SQRT({ax_cols[0]}*{ax_cols[0]} +
                        {ax_cols[1]}*{ax_cols[1]} +
                        {ax_cols[2]}*{ax_cols[2]})) as v_min,
               MAX(SQRT({ax_cols[0]}*{ax_cols[0]} +
                        {ax_cols[1]}*{ax_cols[1]} +
                        {ax_cols[2]}*{ax_cols[2]})) as v_max
        FROM accel_all
        WHERE datetime BETWEEN '{start_day}' AND '{end_day + pd.Timedelta(days=1)}'
        GROUP BY dt_min
        ORDER BY dt_min
    """
    df = con.execute(query).df()

    if df.empty:
        print("No acceleration data in given window.")
        return None

    df["datetime"] = pd.to_datetime(df["dt_min"])
    df = df.set_index("datetime")

    # 4) Split by day
    days = []
    day_labels = []
    for i in range(num_days):
        day_start = start_day + pd.Timedelta(days=i)
        day_end   = day_start + pd.Timedelta(days=1)
        chunk = df[(df.index >= day_start) & (df.index < day_end)]
        days.append(chunk)
        day_labels.append(day_start.strftime("%d. %b."))

    # 5) Create figure
    fig, axes_rows = plt.subplots(
        num_days, 1,
        figsize=(11, max(4, 0.8 * num_days)),
        sharex=False,
        gridspec_kw={"hspace": 0.15},
    )

    # If only 1 day, axes_rows is a single Axes
    if num_days == 1:
        axes_rows = [axes_rows]

    # 6) Plot each day
    for idx, ax in enumerate(axes_rows):
        old_formatter = ax.yaxis.get_major_formatter()
        ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.2f"))

        day_df = days[idx]
        day_txt = day_labels[idx]

        # alternating label left/right
        if idx % 2 == 0:
            ax.set_ylabel(day_txt, fontproperties=LABEL_FONT)
        else:
            ax.yaxis.set_label_position("right")
            ax.yaxis.tick_right()
            ax.set_ylabel(day_txt, fontproperties=LABEL_FONT)

        if not day_df.empty:
            t_hours = (day_df.index - day_df.index.normalize()) / pd.Timedelta(hours=1)
            ax.fill_between(t_hours, day_df["v_min"], day_df["v_max"], color=color, alpha=0.3)
            ax.plot(t_hours, day_df["v_avg"], color=color, linewidth=1.0)

        ax.grid(True, linestyle="--", alpha=0.3)
        ax.set_xticks(np.arange(0, 24))
        ax.set_xlim(0, 23)

        # Only bottom axis gets label
        if idx != num_days - 1:
            ax.set_xticklabels([])
        else:
            ax.set_xlabel("Hour of Day", fontproperties=LABEL_FONT)

        set_fonts(ax)
        ax.yaxis.set_major_formatter(old_formatter)

    # 7) Title & subtitle
    fig.suptitle(
        f"{label} – Daily Resultant Acceleration",
        fontproperties=TITLE_FONT,
        fontsize=15,
        y=0.97,
    )
    fig.text(
        0.5, 0.90,
        f"{day_labels[0]} – {day_labels[-1]} (last {num_days} full days)",
        ha="center",
        fontproperties=LABEL_FONT,
        fontsize=10,
    )

    filename = f"{sensor_id}_daily_v_grid.png"
    if save:
        _ensure_plot_path()
        outpath = PLOT_PATH / filename
        fig.savefig(outpath, dpi=300, format="png")

    if show:
        plt.show()
    else:
        plt.close(fig)

    gc.collect()
    return None

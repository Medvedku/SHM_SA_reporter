# processor.py — stream MongoDB → chunk Parquets → final weekly merge

from datetime import datetime

from .schemas import (
    HUBS,
    ACCEL_ALL,
    ACCEL_ALL_SCHEMA,
    make_fft_schema,
    make_sst_schema,
)

from .helpers import safe_float, safe_list
from .writer import append_chunk, merge_week

CHUNK = 5000  # number of Mongo documents per flush


def process_week_cursor(
    cursor,
    iso_year: int,
    iso_week: int,
    base_dir: str | None = "parquet_output",
) -> dict:
    """
    Stream Mongo cursor, write per-table CHUNK parquet files,
    then call merge_week() to create final weekly files.

    Returns:
        dict[table_key -> final_path]
    """
    base_dir = base_dir or "parquet_output"

    # Buffers
    accel_rows: list[dict] = []
    fft_rows: dict[str, list[dict]] = {hub: [] for hub in HUBS}
    sst_rows: dict[str, list[dict]] = {hub: [] for hub in HUBS}

    # Per-table chunk counters
    part_counters: dict[str, int] = {}

    for obj in cursor:
        dt_raw = obj.get("time", {}).get("datetime")
        if not dt_raw:
            continue

        dt = datetime.fromisoformat(dt_raw)

        # ---------------- ACCEL ----------------
        ar = {"datetime": dt}
        for a in ACCEL_ALL:
            if a in obj:
                ar[f"{a}_t"] = safe_float(obj[a].get("t"))
                ar[f"{a}_x"] = safe_float(obj[a].get("x"))
                ar[f"{a}_y"] = safe_float(obj[a].get("y"))
                ar[f"{a}_z"] = safe_float(obj[a].get("z"))
        accel_rows.append(ar)

        if len(accel_rows) >= CHUNK:
            append_chunk(
                rows=accel_rows,
                schema=ACCEL_ALL_SCHEMA,
                table_key="accel_all",
                iso_year=iso_year,
                iso_week=iso_week,
                base_dir=base_dir,
                part_counters=part_counters,
            )
            accel_rows.clear()

        # ---------------- HUBS: SST + FFT ----------------
        for hub in HUBS:
            # SST
            sr = {"datetime": dt}
            has_sst = False

            for s in HUBS[hub]["S"]:
                if s in obj:
                    sr[s] = safe_float(obj[s].get("s"))
                    has_sst = True

            for t in HUBS[hub]["T"]:
                if t in obj:
                    sr[t] = safe_float(obj[t].get("t"))
                    has_sst = True

            if has_sst:
                sst_rows[hub].append(sr)
                if len(sst_rows[hub]) >= CHUNK:
                    append_chunk(
                        rows=sst_rows[hub],
                        schema=make_sst_schema(hub),
                        table_key=f"sst_{hub}",
                        iso_year=iso_year,
                        iso_week=iso_week,
                        base_dir=base_dir,
                        part_counters=part_counters,
                    )
                    sst_rows[hub].clear()

            # FFT
            for a in HUBS[hub]["A"]:
                fft = obj.get(a, {}).get("fft")
                if fft:
                    mn = fft.get("main", {}) or {}
                    sp = fft.get("spectrum", []) or []
                    fft_rows[hub].append({
                        "datetime": dt,
                        "sensor_id": a,
                        "fft_main_f": safe_float(mn.get("f")),
                        "fft_main_a": safe_float(mn.get("a")),
                        "fft_freqs": safe_list(sp, "f"),
                        "fft_amps": safe_list(sp, "a"),
                    })
                    if len(fft_rows[hub]) >= CHUNK:
                        append_chunk(
                            rows=fft_rows[hub],
                            schema=make_fft_schema(),
                            table_key=f"fft_{hub}",
                            iso_year=iso_year,
                            iso_week=iso_week,
                            base_dir=base_dir,
                            part_counters=part_counters,
                        )
                        fft_rows[hub].clear()

    # ---------- FINAL FLUSH (remaining rows) ----------
    if accel_rows:
        append_chunk(
            rows=accel_rows,
            schema=ACCEL_ALL_SCHEMA,
            table_key="accel_all",
            iso_year=iso_year,
            iso_week=iso_week,
            base_dir=base_dir,
            part_counters=part_counters,
        )
        accel_rows.clear()

    for hub in HUBS:
        if fft_rows[hub]:
            append_chunk(
                rows=fft_rows[hub],
                schema=make_fft_schema(),
                table_key=f"fft_{hub}",
                iso_year=iso_year,
                iso_week=iso_week,
                base_dir=base_dir,
                part_counters=part_counters,
            )
            fft_rows[hub].clear()

        if sst_rows[hub]:
            append_chunk(
                rows=sst_rows[hub],
                schema=make_sst_schema(hub),
                table_key=f"sst_{hub}",
                iso_year=iso_year,
                iso_week=iso_week,
                base_dir=base_dir,
                part_counters=part_counters,
            )
            sst_rows[hub].clear()

    # Now merge all tables for this week into final Parquet files
    print("🔚 All chunks written, starting weekly merge…")
    weekly_files = merge_week(iso_year, iso_week, base_dir=base_dir)
    print("✔ Week processing complete (chunks + merge).")

    return weekly_files


def process_week(
    collection,
    week_start_dt,
    week_end_dt,
    iso_year: int,
    iso_week: int,
    base_dir: str | None = "parquet_output",
) -> dict:
    """
    High-level API used by ram_run_parqueter.py
    """
    base_dir = base_dir or "parquet_output"

    start_iso = week_start_dt.strftime("%Y-%m-%dT%H:%M:%S")
    end_iso   = week_end_dt.strftime("%Y-%m-%dT%H:%M:%S")

    cursor = collection.find(
        {"time.datetime": {"$gte": start_iso, "$lt": end_iso}},
        batch_size=5000,
    )

    return process_week_cursor(cursor, iso_year, iso_week, base_dir=base_dir)

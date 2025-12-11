# processor.py
from datetime import datetime
from .schemas import HUBS, ACCEL_ALL, ACCEL_ALL_SCHEMA, make_fft_schema, make_sst_schema
from .helpers import safe_float, safe_list
from .writer import append_rows_to_parquet

CHUNK = 5000

def process_week_cursor(cursor, weekly_files):
    accel_rows = []
    fft_rows = {hub: [] for hub in HUBS}
    sst_rows = {hub: [] for hub in HUBS}

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
            append_rows_to_parquet(accel_rows, ACCEL_ALL_SCHEMA, weekly_files["accel_all"])
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
                    append_rows_to_parquet(sst_rows[hub], make_sst_schema(hub), weekly_files[f"sst_{hub}"])
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
                        append_rows_to_parquet(fft_rows[hub], make_fft_schema(), weekly_files[f"fft_{hub}"])
                        fft_rows[hub].clear()

    # Final flush
    if accel_rows:
        append_rows_to_parquet(accel_rows, ACCEL_ALL_SCHEMA, weekly_files["accel_all"])

    for hub in HUBS:
        if fft_rows[hub]:
            append_rows_to_parquet(fft_rows[hub], make_fft_schema(), weekly_files[f"fft_{hub}"])

        if sst_rows[hub]:
            append_rows_to_parquet(sst_rows[hub], make_sst_schema(hub), weekly_files[f"sst_{hub}"])

    print("✔ Week processing complete.")


def process_week(collection, week_start_dt, week_end_dt, iso_year, iso_week):
    start_iso = week_start_dt.strftime("%Y-%m-%dT%H:%M:%S")
    end_iso   = week_end_dt.strftime("%Y-%m-%dT%H:%M:%S")

    from .writer import create_empty_week_files
    weekly_files = create_empty_week_files(iso_year, iso_week)

    cursor = collection.find(
        {"time.datetime": {"$gte": start_iso, "$lt": end_iso}},
        batch_size=5000
    )

    process_week_cursor(cursor, weekly_files)

    return weekly_files

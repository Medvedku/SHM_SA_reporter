# writer.py
import duckdb
import pyarrow as pa
import pyarrow.parquet as pq
from pathlib import Path

from .schemas import (
    ACCEL_ALL_SCHEMA,
    make_fft_schema,
    make_sst_schema,
    HUBS,
)

def create_empty_week_files(iso_year, iso_week, base_dir="parquet_output"):
    base = Path(base_dir)
    base.mkdir(exist_ok=True, parents=True)

    week_str = f"{iso_year}W{iso_week:02d}"

    files = {}

    # accel_all
    fn = base / f"{week_str}_accel_all.parquet"
    pq.write_table(pa.Table.from_pylist([], ACCEL_ALL_SCHEMA), fn)
    files["accel_all"] = fn

    # fft
    for hub in HUBS:
        fn = base / f"{week_str}_fft_{hub}.parquet"
        pq.write_table(pa.Table.from_pylist([], make_fft_schema()), fn)
        files[f"fft_{hub}"] = fn

    # sst
    for hub in HUBS:
        fn = base / f"{week_str}_sst_{hub}.parquet"
        pq.write_table(pa.Table.from_pylist([], make_sst_schema(hub)), fn)
        files[f"sst_{hub}"] = fn

    return files


def append_rows_to_parquet(rows, schema, parquet_path):
    if not rows:
        return

    tbl = pa.Table.from_pylist(rows, schema=schema)
    duckdb.register("new_rows", tbl)

    # Load existing file
    duckdb.execute(f"""
        CREATE OR REPLACE TEMP TABLE existing AS
        SELECT * FROM parquet_scan('{parquet_path}', union_by_name=true)
    """)

    # Merge
    duckdb.execute("""
        CREATE OR REPLACE TEMP TABLE merged AS
        SELECT * FROM existing
        UNION ALL
        SELECT * FROM new_rows
    """)

    # Overwrite parquet
    duckdb.execute(f"""
        COPY merged TO '{parquet_path}' (FORMAT PARQUET, COMPRESSION ZSTD);
    """)

    duckdb.unregister("new_rows")

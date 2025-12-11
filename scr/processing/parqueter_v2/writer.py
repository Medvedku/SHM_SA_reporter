# writer.py  —  CHUNK → MERGE STRATEGY (RAM-FRIENDLY)

from pathlib import Path
import shutil

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq

from .schemas import (
    ACCEL_ALL_SCHEMA,
    make_fft_schema,
    make_sst_schema,
    HUBS,
    TABLE_KEYS,
)


def week_str(iso_year: int, iso_week: int) -> str:
    """Return canonical week prefix: e.g. 2025W49."""
    return f"{iso_year}W{iso_week:02d}"


def get_chunk_dir(base_dir: str | Path, table_key: str, iso_year: int, iso_week: int) -> Path:
    """
    Directory where per-chunk Parquet files are written, e.g.:

    parquet_output/chunks/2025W49/accel_all/
    parquet_output/chunks/2025W49/fft_hub2/
    """
    base = Path(base_dir)
    wk = week_str(iso_year, iso_week)
    return base / "chunks" / wk / table_key


def get_final_path(base_dir: str | Path, table_key: str, iso_year: int, iso_week: int) -> Path:
    """
    Final weekly parquet path, e.g.:

        parquet_output/2025W49_accel_all.parquet
    """
    base = Path(base_dir)
    wk = week_str(iso_year, iso_week)
    return base / f"{wk}_{table_key}.parquet"


def append_chunk(
    rows: list[dict],
    schema: pa.Schema,
    table_key: str,
    iso_year: int,
    iso_week: int,
    base_dir: str | Path,
    part_counters: dict[str, int],
) -> None:
    """
    Write one CHUNK parquet file for given table_key & week.
    Does NOT touch the final weekly file.
    """
    if not rows:
        return

    # Determine chunk dir
    chunk_dir = get_chunk_dir(base_dir, table_key, iso_year, iso_week)
    chunk_dir.mkdir(parents=True, exist_ok=True)

    # Increment part counter
    part_counters[table_key] = part_counters.get(table_key, 0) + 1
    part_id = part_counters[table_key]

    wk = week_str(iso_year, iso_week)
    fn = chunk_dir / f"{table_key}_{wk}_{part_id:04d}.parquet"

    tbl = pa.Table.from_pylist(rows, schema=schema)
    pq.write_table(tbl, fn)

    # IMPORTANT: rows must be cleared by the caller
    # so we don't accidentally reuse them.


def _schema_for_table(table_key: str) -> pa.Schema:
    """Return base schema for a given final table_key (without week)."""
    if table_key == "accel_all":
        return ACCEL_ALL_SCHEMA
    elif table_key.startswith("fft_"):
        return make_fft_schema()
    elif table_key.startswith("sst_"):
        hub = table_key.replace("sst_", "")
        return make_sst_schema(hub)
    else:
        raise ValueError(f"Unknown table_key {table_key}")


def merge_week(
    iso_year: int,
    iso_week: int,
    base_dir: str | Path = "parquet_output",
) -> dict[str, Path]:
    """
    After all chunks for a given week are written, merge them into
    one final Parquet file per table_key.

    - If there are chunk files → DuckDB merges them (ORDER BY datetime)
    - If there are NO chunks for a table → write EMPTY parquet with correct schema
    - Afterwards, per-week chunk folder is deleted

    Returns:
        dict[table_key -> final_path]
    """
    base_dir = Path(base_dir)
    wk = week_str(iso_year, iso_week)
    results: dict[str, Path] = {}

    for table_key in TABLE_KEYS:
        schema = _schema_for_table(table_key)
        chunk_dir = get_chunk_dir(base_dir, table_key, iso_year, iso_week)
        final_path = get_final_path(base_dir, table_key, iso_year, iso_week)
        final_path.parent.mkdir(parents=True, exist_ok=True)

        if chunk_dir.exists() and any(chunk_dir.glob("*.parquet")):
            # We have data → merge all chunks into one file
            pattern = str(chunk_dir / "*.parquet")
            print(f"🔄 Merging {table_key} from chunks: {pattern}")

            duckdb.sql(f"""
                COPY (
                    SELECT *
                    FROM parquet_scan('{pattern}', union_by_name=true)
                    ORDER BY datetime
                ) TO '{final_path}' (FORMAT PARQUET);
            """)
        else:
            # No chunks → create empty file with correct schema
            print(f"⚠️ No chunks for {table_key} in week {wk}, writing EMPTY parquet.")
            empty_tbl = pa.Table.from_pylist([], schema=schema)
            pq.write_table(empty_tbl, final_path)

        results[table_key] = final_path

    # Cleanup chunk dirs for that week
    week_chunk_root = base_dir / "chunks" / wk
    if week_chunk_root.exists():
        shutil.rmtree(week_chunk_root)

    print(f"✔ Week {wk} merged into final Parquet files.")
    return results

"""scripts/lib/backend.py — backend abstraction for Fragility IV/V aggregation.

Supports pandas, duckdb, and polars as interchangeable engines for the
groupby-aggregate step that dominates cost at bigrun scale. ETL (extraction,
fact-building) stays pandas-based, consistent with Fragility I-III; this
abstraction is applied only where backend choice actually matters: reducing
a large Parquet fact table down to a small scorecard. The materialized
result is always returned as a pandas DataFrame so downstream chart/summary
code (shared with Fragility I-III) does not need to know which backend ran.

See flight_fragility_iv_operator_attribution_spec.md, "Architecture and
build location."
"""

import logging
import shutil
from pathlib import Path

import pandas as pd

log = logging.getLogger(__name__)

SUPPORTED_BACKENDS = ("pandas", "duckdb", "polars")


def _parquet_glob(path: Path) -> str:
    path = Path(path)
    return str(path / "**" / "*.parquet") if path.is_dir() else str(path)


def read_table(path: Path, backend: str = "pandas") -> pd.DataFrame:
    """Read a (possibly partitioned) Parquet dataset into a pandas DataFrame."""
    if backend not in SUPPORTED_BACKENDS:
        raise ValueError(f"Unknown backend '{backend}'; supported: {SUPPORTED_BACKENDS}")

    path = Path(path)
    if backend == "pandas":
        return pd.read_parquet(path)

    if backend == "duckdb":
        import duckdb
        glob = _parquet_glob(path)
        return duckdb.sql(
            f"SELECT * FROM read_parquet('{glob}', hive_partitioning=true)"
        ).to_df()

    if backend == "polars":
        import polars as pl
        glob = _parquet_glob(path)
        return pl.scan_parquet(glob, hive_partitioning=True).collect().to_pandas()

    raise AssertionError("unreachable")


def aggregate_sums(
    path: Path,
    group_cols: list[str],
    sum_cols: list[str],
    backend: str = "pandas",
) -> pd.DataFrame:
    """Group a Parquet dataset by group_cols, computing row_count plus
    sum(col) for each entry in sum_cols. This single shape covers every
    metric Fragility IV's scorecard needs (flights_total, cancelled_count,
    operated_count, severe_delay_count, controllable_*, late_arriving_*),
    since each is either a row count or a sum of a 0/1 flag column.

    Identical semantics across all three backends; only the engine that
    does the heavy lifting differs.
    """
    if backend not in SUPPORTED_BACKENDS:
        raise ValueError(f"Unknown backend '{backend}'; supported: {SUPPORTED_BACKENDS}")

    path = Path(path)
    log.info(f"Aggregating {path} via backend={backend} "
              f"(group_cols={group_cols}, sum_cols={sum_cols})")

    if backend == "pandas":
        df = pd.read_parquet(path)
        agg = df.groupby(group_cols, dropna=False).agg(
            row_count=(group_cols[0], "size"),
            **{f"{c}_sum": (c, "sum") for c in sum_cols},
        ).reset_index()
        return agg

    if backend == "duckdb":
        import duckdb
        glob = _parquet_glob(path)
        group_sql = ", ".join(group_cols)
        sum_sql = ", ".join(f"SUM({c}) AS {c}_sum" for c in sum_cols)
        query = f"""
            SELECT {group_sql}, COUNT(*) AS row_count, {sum_sql}
            FROM read_parquet('{glob}', hive_partitioning=true)
            GROUP BY {group_sql}
        """
        return duckdb.sql(query).to_df()

    if backend == "polars":
        import polars as pl
        glob = _parquet_glob(path)
        lf = pl.scan_parquet(glob, hive_partitioning=True)
        agg = lf.group_by(group_cols).agg(
            [pl.len().alias("row_count")]
            + [pl.col(c).sum().alias(f"{c}_sum") for c in sum_cols]
        ).collect()
        return agg.to_pandas()

    raise AssertionError("unreachable")


def write_partitioned_parquet(df: pd.DataFrame, out_dir: Path, partition_cols: list[str]):
    """Write a pandas DataFrame as a Hive-partitioned Parquet dataset.

    pandas' to_parquet() adds new uniquely-named files into existing
    partition directories rather than replacing them, so a dataset directory
    written this way would silently accumulate duplicate rows across repeated
    runs. Clear out_dir first so every write fully replaces prior output
    (idempotent re-runs, consistent with the rest of the pipeline's
    overwrite-on-rerun behavior).
    """
    out_dir = Path(out_dir)
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out_dir, partition_cols=partition_cols, index=False)
    log.info(f"Wrote partitioned Parquet: {out_dir} (partitioned by {partition_cols}, {len(df):,} rows)")

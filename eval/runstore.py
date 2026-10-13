"""Eval runs land in sqlite (data/eval.db) and are exported to parquet (data/parquet/)."""
import json
import sqlite3
import time
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from app.config import ROOT

DB = ROOT / "data" / "eval.db"
PARQUET = ROOT / "data" / "parquet"

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (run_id TEXT, split TEXT, sample INTEGER, config_hash TEXT, mode TEXT, guard_on INTEGER,
  s REAL, recall REAL, route_accuracy REAL, refusal_accuracy REAL, span_support REAL, acl_compliance REAL,
  cache_hits INTEGER, median_dollars REAL, p95_latency_ms REAL, backend TEXT, ts REAL);
CREATE TABLE IF NOT EXISTS responses (run_id TEXT, split TEXT, sample INTEGER, ticket_id TEXT, caller_role TEXT,
  route TEXT, gold_route TEXT, refused INTEGER, reason TEXT, dollars REAL, latency_ms REAL,
  leaked INTEGER, leaked_chunk_ids TEXT, cache_hit INTEGER);
"""


def connect(db: Path | str = DB) -> sqlite3.Connection:
    con = sqlite3.connect(db)
    con.executescript(SCHEMA)
    return con


def record(run_id: str, split: str, sample: int, cfg_hash: str, mode: str, guard_on: bool, m: dict, g: dict,
           backend: str, rows: list[dict], db: Path | str = DB, export: bool = True) -> None:
    con = connect(db)
    con.execute("INSERT INTO runs VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (run_id, split, sample, cfg_hash, mode, int(guard_on), m["S"], m["recall"], m["route_accuracy"],
                 m["refusal_accuracy"], m["span_support"], m["acl_compliance"], m["cache_hits"],
                 g["median_dollars"], g["p95_latency_ms"], backend, time.time()))
    con.executemany("INSERT INTO responses VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    [(run_id, split, sample, r["ticket_id"], r["caller_role"], r["route"], r["gold_route"],
                      int(r["refused"]), r["reason"], r["dollars"], r["latency_ms"], int(r["leaked"]),
                      json.dumps(r["leaked_chunk_ids"]), int(r["cache_hit"])) for r in rows])
    con.commit()
    if export:
        export_parquet(con, Path(db).parent / "parquet")
    con.close()


def export_parquet(con: sqlite3.Connection, out: Path = PARQUET) -> None:
    out.mkdir(parents=True, exist_ok=True)
    for table in ("runs", "responses"):
        cur = con.execute(f"SELECT * FROM {table}")
        cols = [d[0] for d in cur.description]
        data = cur.fetchall()
        pq.write_table(pa.table({c: [row[i] for row in data] for i, c in enumerate(cols)}), out / f"{table}.parquet")

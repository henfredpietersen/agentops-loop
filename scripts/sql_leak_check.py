"""CI: run sql/check.sql against data/eval.db and fail if the leaked-chunk count is not 0."""
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
con = sqlite3.connect(ROOT / "data" / "eval.db")
for stmt in [s for s in (ROOT / "sql" / "check.sql").read_text().split(";") if "SELECT" in s]:
    rows = con.execute(stmt).fetchall()
    print(stmt.strip().splitlines()[0], "->", rows[:6])
leaked = con.execute([s for s in (ROOT / "sql" / "check.sql").read_text().split(";") if "leaked_chunks" in s][0]).fetchone()[0]
sys.exit(1 if leaked else 0)

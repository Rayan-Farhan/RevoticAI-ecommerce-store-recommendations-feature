import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "scripts" / "schema.sql"
SEED = ROOT / "scripts" / "seed.sql"

def run_psql(file_path: Path, database: str | None = None) -> None:
    db = database or os.getenv("DATABASE_URL")
    args = [
        "psql",
        "-U",
        os.getenv("PGUSER", "postgres"),
        "-h",
        os.getenv("PGHOST", "localhost"),
    ]
    dbname = os.getenv("PGDATABASE", "grocery_db")
    args += ["-d", dbname, "-f", str(file_path)]

    print(f"Running: {' '.join(args)}")
    res = subprocess.run(args, check=False)
    if res.returncode != 0:
        print(f"psql failed with exit code {res.returncode}", file=sys.stderr)
        sys.exit(res.returncode)

if __name__ == "__main__":
    if not SCHEMA.exists():
        print(f"schema.sql not found at {SCHEMA}", file=sys.stderr)
        sys.exit(1)

    run_psql(SCHEMA)

    if SEED.exists():
        run_psql(SEED)
    else:
        print("seed.sql not found; skipping seeding.")
    print("Database initialized via SQL scripts.")
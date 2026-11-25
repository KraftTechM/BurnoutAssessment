import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

DB_PATH = Path(os.environ.get("BURNOUT_DB", BASE_DIR / "data" / "burnout.db"))
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "change-me")
TEAMS = [t.strip() for t in os.environ.get("TEAMS", "engineering,research,operations,clinical-ops").split(",") if t.strip()]
MIN_CELL = int(os.environ.get("MIN_CELL", "5"))

# Transparent heuristic weights. This is NOT a validated clinical score.
RISK_WEIGHTS = {"demand": 0.35, "low_resource": 0.35, "strain": 0.30}

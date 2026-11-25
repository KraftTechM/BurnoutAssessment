"""Insert synthetic responses so you can see the dashboard populated."""
import json, random, sys
from datetime import datetime, timezone
from pathlib import Path

# Make `import app` work when this file is run directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import db
from app.scoring import QUESTIONS, score_response

db.init_db()

TEAMS = ["engineering", "research", "operations", "clinical-ops"]
ROLES = ["engineer", "coordinator", "cra", "manager", "medical-monitor"]
random.seed(42)

def pick_index(bias):
    # Returns an integer 0-4 based on normal distribution around 'bias'
    return min(max(int(random.gauss(bias, 1)), 0), 4)

with db.connect() as c:
    for _ in range(60):
        team = random.choice(TEAMS)
        # Give one team a worse profile on purpose (higher index = worse answers)
        bias = 2.5 if team == "clinical-ops" else 1.2

        # Store answers as integers
        answers = {q.id: pick_index(bias) for q in QUESTIONS}
        result = score_response(answers)

        cur = c.execute(
            "INSERT INTO responses (team, role, consent, submitted_at, answers) VALUES (?, ?, 1, ?, ?)",
            (team, random.choice(ROLES), datetime.now(timezone.utc).isoformat(), json.dumps(answers)),
        )
        c.execute(
            "INSERT INTO scores (response_id, demand_index, resource_index, strain_index, risk_score) "
            "VALUES (?, ?, ?, ?, ?)",
            (cur.lastrowid, result["demand_index"], result["resource_index"],
             result["strain_index"], result["risk_score"]),
        )
print(f"Seeded 60 demo responses into {db.config.DB_PATH}")

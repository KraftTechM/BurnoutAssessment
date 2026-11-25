import os
os.environ["BURNOUT_DB"] = ":memory:"  # not used; we use a temp file below
import tempfile, pathlib
os.environ["BURNOUT_DB"] = str(pathlib.Path(tempfile.gettempdir()) / "burnout_test.db")
os.environ["ADMIN_TOKEN"] = "test-token"
os.environ["TEAMS"] = "eng,ops"
os.environ["MIN_CELL"] = "1"

# Import after env is set
from fastapi.testclient import TestClient
from app.main import app
from app.scoring import QUESTIONS, OPTIONS

client = TestClient(app)


def _form(team="eng", role="engineer"):
    data = {"team": team, "role": role, "consent": "on"}
    for q in QUESTIONS:
        data[q.id] = OPTIONS[q.options][0]
    return data


def test_survey_submission_and_dashboard():
    r = client.post("/api/survey", data=_form(), follow_redirects=False)
    assert r.status_code == 303

    r = client.get("/dashboard?token=test-token")
    assert r.status_code == 200
    assert "eng" in r.text


def test_dashboard_requires_token():
    r = client.get("/dashboard")
    assert r.status_code == 401


def test_export_csv_is_aggregated():
    client.post("/api/survey", data=_form(team="ops"), follow_redirects=False)
    r = client.get("/api/export?token=test-token")
    assert r.status_code == 200
    assert "team,n,demand_index" in r.text
    assert "ops" in r.text

import json
from datetime import datetime, timezone
from statistics import mean, pstdev

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates

from . import config, db
from .scoring import QUESTIONS, score_response
from .i18n import get_text

app = FastAPI(title="Burnout Assessment MVP")
templates = Jinja2Templates(directory="app/templates")

db.init_db()

def _check_token(token: str | None) -> None:
    if token != config.ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")

# ---------- Public survey flow ----------

@app.get("/", response_class=HTMLResponse)
def index(request: Request, lang: str = "en"):
    t = lambda k: get_text(lang, k)
    return templates.TemplateResponse(request, "consent.html", {
        "lang": lang,
        "t": t,
        "teams": config.TEAMS,
        "min_cell": config.MIN_CELL,
    })

@app.get("/survey", response_class=HTMLResponse)
def survey(request: Request, team: str, role: str = "", lang: str = "en"):
    if team not in config.TEAMS:
        raise HTTPException(400, "Unknown team")
    t = lambda k: get_text(lang, k)

    translated_options = {
        "freq5": t("opt_freq"),
        "extent5": t("opt_extent"),
        "agree5": t("opt_agree"),
    }

    return templates.TemplateResponse(request, "survey.html", {
        "lang": lang,
        "t": t,
        "team": team,
        "role": role,
        "questions": QUESTIONS,
        "options": translated_options,
    })

@app.post("/api/survey")
async def submit_survey(request: Request):
    form = await request.form()
    team = form.get("team", "")
    role = form.get("role", "") or ""
    lang = form.get("lang", "en")
    consent = form.get("consent") == "on"

    if not consent or team not in config.TEAMS:
        return RedirectResponse(f"/?lang={lang}&err=1", status_code=303)

    answers = {}
    for q in QUESTIONS:
        val = form.get(q.id)
        answers[q.id] = int(val) if val is not None and val.isdigit() else None

    result = score_response(answers)

    with db.connect() as c:
        cur = c.execute(
            "INSERT INTO responses (team, role, consent, submitted_at, answers) VALUES (?, ?, ?, ?, ?)",
            (team, role, 1, datetime.now(timezone.utc).isoformat(), json.dumps(answers)),
        )
        c.execute(
            "INSERT INTO scores (response_id, demand_index, resource_index, strain_index, risk_score) "
            "VALUES (?, ?, ?, ?, ?)",
            (cur.lastrowid, result["demand_index"], result["resource_index"],
             result["strain_index"], result["risk_score"]),
        )

    return RedirectResponse(f"/thanks?lang={lang}", status_code=303)

@app.get("/thanks", response_class=HTMLResponse)
def thanks(request: Request, lang: str = "en"):
    t = lambda k: get_text(lang, k)
    return templates.TemplateResponse(request, "thanks.html", {"lang": lang, "t": t})

# ---------- Admin / aggregated view ----------

def _get_risk_level(score):
    if score is None: return "unknown"
    if score < 25: return "no_risk"
    if score < 50: return "slight_risk"
    if score < 75: return "middle_risk"
    return "high_risk"

def _load_aggregates() -> dict:
    with db.connect() as c:
        rows = c.execute(
            """
            SELECT r.team, s.demand_index, s.resource_index, s.strain_index, s.risk_score
            FROM responses r JOIN scores s ON s.response_id = r.id
            """
        ).fetchall()

    by_team: dict[str, list[dict]] = {}
    for r in rows:
        by_team.setdefault(r["team"], []).append(dict(r))

    all_risk = [r["risk_score"] for r in rows if r["risk_score"] is not None]
    baseline_mean = round(mean(all_risk), 2) if all_risk else None
    baseline_sd   = round(pstdev(all_risk), 2) if len(all_risk) > 1 else None

    teams_out = []
    for team, items in sorted(by_team.items()):
        n = len(items)
        if n < config.MIN_CELL:
            teams_out.append({"team": team, "n": n, "suppressed": True})
            continue
        def m(key):
            vals = [i[key] for i in items if i[key] is not None]
            return round(mean(vals), 2) if vals else None
        risk = m("risk_score")
        delta = round(risk - baseline_mean, 2) if (risk is not None and baseline_mean is not None) else None
        flag = bool(baseline_sd is not None and risk is not None and risk > baseline_mean + baseline_sd)

        teams_out.append({
            "team": team, "n": n, "suppressed": False,
            "demand_index": m("demand_index") or 0,
            "resource_index": m("resource_index") or 0,
            "strain_index": m("strain_index") or 0,
            "risk_score": risk or 0,
            "risk_level": _get_risk_level(risk),
            "delta": delta,
            "flag": flag,
        })

    return {
        "teams": teams_out,
        "baseline_mean": baseline_mean,
        "baseline_sd": baseline_sd,
        "total_responses": len(rows),
        "min_cell": config.MIN_CELL,
    }

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, token: str = "", lang: str = "en"):
    _check_token(token)
    t = lambda k: get_text(lang, k)
    data = _load_aggregates()

    chart_data = []
    for tm in data["teams"]:
        if not tm.get("suppressed"):
            chart_data.append({
                "team": tm["team"],
                "risk": float(tm["risk_score"]),
                "risk_level": tm["risk_level"],
                "demand": float(tm["demand_index"]),
                "resource": float(tm["resource_index"]),
                "strain": float(tm["strain_index"])
            })

    return templates.TemplateResponse(request, "dashboard.html", {
        "token": token,
        "lang": lang,
        "t": t,
        "chart_data_json": json.dumps(chart_data),
        **data
    })

@app.get("/api/export", response_class=PlainTextResponse)
def export_csv(token: str = ""):
    _check_token(token)
    data = _load_aggregates()
    lines = ["team,n,demand_index,resource_index,strain_index,risk_score,risk_level,delta_vs_baseline,flagged"]
    for t in data["teams"]:
        if t.get("suppressed"):
            lines.append(f"{t['team']},{t['n']},,,,insufficient_data,,")
        else:
            lines.append(
                f"{t['team']},{t['n']},{t['demand_index']},{t['resource_index']},"
                f"{t['strain_index']},{t['risk_score']},{t['risk_level']},{t['delta']},{int(t['flag'])}"
            )
    return PlainTextResponse("\n".join(lines), media_type="text/csv")

# Burnout Assessment MVP (COPSOQ-based)

A small, ethically constrained pulse-survey app that scores a curated subset of the
Copenhagen Psychosocial Questionnaire (COPSOQ) and reports **team-level trends** to HR.

## What this is

- A 26-item monthly pulse based on COPSOQ II questions.
- All scales scored 0–100 using COPSOQ II conventions (5-point options → 100/75/50/25/0,
  reverse-scored items flipped, scale = mean of items).
- A composite `risk_score` (0–100, higher = worse) combining demand, low-resource, and
  strain indices with **transparent, documented weights**.
- Team-level aggregation only. Cells with fewer than `MIN_CELL` (default 5) respondents
  are suppressed.
- A CSV export of aggregated data — safe to import into Google Sheets for further analysis.

## What this is NOT

- Not a clinical diagnosis.
- Not an individual monitoring tool. **No individual alerts are sent to HR.**
- Not a validated psychometric instrument. It is a pragmatic monitoring MVP built on
  validated COPSOQ item wording.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# edit .env — change ADMIN_TOKEN

python -m uvicorn app.main:app --reload
# open http://localhost:8000

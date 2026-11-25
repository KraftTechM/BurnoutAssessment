"""COPSOQ-based scoring engine.

All scales are scored 0-100, following COPSOQ II conventions:
- 5-point options map to 100, 75, 50, 25, 0 (based on integer indices 0, 1, 2, 3, 4)
- reverse-scored items are flipped (100 - raw)
- a scale score is the average of its items
- direction: 'harm' = high is bad, 'resource' = high is good
"""
from dataclasses import dataclass
from typing import Optional
from statistics import mean
from .config import RISK_WEIGHTS


@dataclass(frozen=True)
class Question:
    id: str
    section: str
    text: str
    options: str
    reverse: bool = False


OPTIONS = {
    "freq5":   ["Always", "Often", "Sometimes", "Seldom", "Never/hardly ever"],
    "extent5": ["To a very large extent", "To a large extent", "Somewhat",
                "To a small extent", "To a very small extent"],
    "agree5":  ["Correct", "Almost correct", "Somewhat correct",
                "Only slightly correct", "Incorrect"],
}


QUESTIONS: list[Question] = [
    # Workload and demands
    Question("q1", "Workload and demands", "Is your workload unevenly distributed so it piles up?", "freq5"),
    Question("q2", "Workload and demands", "Do you get behind with your work?", "freq5"),
    Question("q3", "Workload and demands", "How often can you take it easy and still do your work?", "freq5", reverse=True),
    Question("q4", "Workload and demands", "Do you have enough time for your work tasks?", "freq5", reverse=True),
    Question("q5", "Workload and demands", "Is your work emotionally demanding?", "extent5"),
    Question("q6", "Workload and demands", "Are contradictory demands placed on you at work?", "extent5"),
    Question("q7", "Workload and demands", "Do you sometimes have to do things which seem to you to be unnecessary?", "extent5"),

    # Control and resources
    Question("q8",  "Control and resources", "Do you have a large degree of influence concerning your work?", "freq5"),
    Question("q9",  "Control and resources", "Do you have any influence on WHAT you do at work?", "freq5"),
    Question("q10", "Control and resources", "Do you have the possibility of learning new things through your work?", "extent5"),
    Question("q11", "Control and resources", "Can you use your skills or expertise in your work?", "extent5"),
    Question("q12", "Control and resources", "Are you informed well in advance about important decisions, changes, or plans for the future?", "extent5"),
    Question("q13", "Control and resources", "Do you receive all the information you need in order to do your work well?", "extent5"),
    Question("q14", "Control and resources", "Does your work have clear objectives?", "extent5"),
    Question("q15", "Control and resources", "Do you know exactly what is expected of you at work?", "extent5"),
    Question("q16", "Control and resources", "Is your immediate superior good at work planning?", "extent5"),
    Question("q17", "Control and resources", "Is your immediate superior good at solving conflicts?", "extent5"),
    Question("q18", "Control and resources", "How often do you get help and support from your colleagues?", "freq5"),
    Question("q19", "Control and resources", "How often do you get help and support from your immediate superior?", "freq5"),
    Question("q20", "Control and resources", "Do you feel part of a community at your place of work?", "freq5"),

    # How you have been feeling (past 4 weeks)
    Question("q21", "How you have been feeling (past 4 weeks)", "I have not had the time to relax or enjoy myself", "agree5"),
    Question("q22", "How you have been feeling (past 4 weeks)", "I have lacked initiative", "agree5"),
    Question("q23", "How you have been feeling (past 4 weeks)", "Have you had tension in various muscles?", "freq5"),
    Question("q24", "How you have been feeling (past 4 weeks)", "Have you had stomach ache or stomach problems?", "freq5"),
    Question("q25", "How you have been feeling (past 4 weeks)", "Have you had problems concentrating?", "freq5"),
    Question("q26", "How you have been feeling (past 4 weeks)", "Have you found it difficult to think clearly?", "freq5"),
]

QUESTION_BY_ID = {q.id: q for q in QUESTIONS}

SCALES = {
    "quantitative_demands": {"direction": "harm",     "items": ["q1", "q2", "q3", "q4"]},
    "emotional_demands":    {"direction": "harm",     "items": ["q5"]},
    "role_conflicts":       {"direction": "harm",     "items": ["q6", "q7"]},
    "influence":            {"direction": "resource", "items": ["q8", "q9"]},
    "development":          {"direction": "resource", "items": ["q10", "q11"]},
    "predictability":       {"direction": "resource", "items": ["q12", "q13"]},
    "role_clarity":         {"direction": "resource", "items": ["q14", "q15"]},
    "leadership":           {"direction": "resource", "items": ["q16", "q17"]},
    "social_support":       {"direction": "resource", "items": ["q18", "q19"]},
    "community":            {"direction": "resource", "items": ["q20"]},
    "behavioural_stress":   {"direction": "harm",     "items": ["q21", "q22"]},
    "somatic_stress":       {"direction": "harm",     "items": ["q23", "q24"]},
    "cognitive_stress":     {"direction": "harm",     "items": ["q25", "q26"]},
}

DEMAND_SCALES   = ["quantitative_demands", "emotional_demands", "role_conflicts"]
RESOURCE_SCALES = ["influence", "development", "predictability", "role_clarity",
                   "leadership", "social_support", "community"]
STRAIN_SCALES   = ["behavioural_stress", "somatic_stress", "cognitive_stress"]


def _raw_score(options_key: str, answer: Optional[int]) -> Optional[float]:
    if answer is None:
        return None

    # Fixed: removed the accidental len() wrapper here
    opts_len = {"freq5": 5, "extent5": 5, "agree5": 5}[options_key]

    if not isinstance(answer, int) or answer < 0 or answer >= opts_len:
        return None
    n = opts_len - 1
    return 100.0 * (1.0 - answer / n)


def score_response(answers: dict[str, Optional[int]]) -> dict:
    """Return per-scale scores and composite indices for one response."""
    item_scores: dict[str, Optional[float]] = {}
    for q in QUESTIONS:
        raw = _raw_score(q.options, answers.get(q.id))
        if raw is not None and q.reverse:
            raw = 100.0 - raw
        item_scores[q.id] = raw

    scale_scores: dict[str, Optional[float]] = {}
    for name, spec in SCALES.items():
        vals = [item_scores[i] for i in spec["items"] if item_scores[i] is not None]
        scale_scores[name] = round(mean(vals), 2) if vals else None

    demand_vals   = [scale_scores[s] for s in DEMAND_SCALES   if scale_scores[s] is not None]
    resource_vals = [scale_scores[s] for s in RESOURCE_SCALES if scale_scores[s] is not None]
    strain_vals   = [scale_scores[s] for s in STRAIN_SCALES   if scale_scores[s] is not None]

    demand_index   = round(mean(demand_vals), 2)   if demand_vals   else None
    resource_index = round(mean(resource_vals), 2) if resource_vals else None
    strain_index   = round(mean(strain_vals), 2)   if strain_vals   else None

    risk_score = None
    if None not in (demand_index, resource_index, strain_index):
        w = RISK_WEIGHTS
        risk_score = round(
            100.0 * (
                w["demand"]       * (demand_index / 100.0)
                + w["low_resource"] * ((100.0 - resource_index) / 100.0)
                + w["strain"]       * (strain_index / 100.0)
            ),
            2,
        )

    return {
        "item_scores": item_scores,
        "scale_scores": scale_scores,
        "demand_index": demand_index,
        "resource_index": resource_index,
        "strain_index": strain_index,
        "risk_score": risk_score,
    }

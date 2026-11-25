from app.scoring import QUESTIONS, score_response

ALL_TOP = {q.id: 0 for q in QUESTIONS}   # all index 0 (highest)
ALL_BOT = {q.id: 4 for q in QUESTIONS}   # all index 4 (lowest)


def test_all_top_and_all_bottom_are_symmetric_for_single_item_scale():
    # community is a single-item resource scale
    top = score_response(ALL_TOP)["scale_scores"]["community"]
    bot = score_response(ALL_BOT)["scale_scores"]["community"]
    assert top == 100.0
    assert bot == 0.0


def test_reverse_items_are_flipped():
    # q3 "How often can you take it easy..." is reverse scored
    answers = dict(ALL_TOP)
    answers["q3"] = 0  # "Always"
    s = score_response(answers)["item_scores"]["q3"]
    assert s == 0.0


def test_missing_answers_are_skipped():
    answers = {q.id: 0 for q in QUESTIONS if q.id != "q1"}
    result = score_response(answers)
    assert result["scale_scores"]["quantitative_demands"] is not None
    assert result["item_scores"]["q1"] is None


def test_composite_indices_are_populated_with_full_answers():
    result = score_response(ALL_TOP)
    assert result["demand_index"] is not None
    assert result["resource_index"] is not None
    assert result["strain_index"] is not None
    assert result["risk_score"] is not None
    assert 0 <= result["risk_score"] <= 100


def test_worst_case_scores_higher_risk_than_best_case():
    # Best case = low demands, high resources, low strain
    best = dict(ALL_TOP)
    for qid in ["q1", "q2", "q5", "q6", "q7", "q21", "q22", "q23", "q24", "q25", "q26"]:
        best[qid] = 4
    worst = dict(ALL_BOT)
    for qid in ["q8", "q9", "q10", "q11", "q12", "q13", "q14", "q15", "q16", "q17", "q18", "q19", "q20"]:
        worst[qid] = 0

    best_risk = score_response(best)["risk_score"]
    worst_risk = score_response(worst)["risk_score"]
    assert worst_risk > best_risk

"""The offline chat: dialogue behaviour and grounding of every statement it shows."""
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def run():
    r = subprocess.run(["node", str(ROOT / "tests" / "chat_dialogue.js")], capture_output=True, text=True, cwd=ROOT, timeout=300)
    assert r.returncode == 0, r.stderr[-500:]
    return json.loads(r.stdout)


def test_greeting_and_help(run):
    g = run["scenarios"]["greet"]
    assert g[0]["kind"] == "greeting" and g[1]["kind"] == "help"


def test_answer_has_citation_points_and_followups(run):
    a = run["scenarios"]["renewal"][0]
    assert a["kind"] == "answer" and a["primary"]["label"] == "IRPWM Para 616" and a["points"] >= 1 and a["followups"] >= 1


def test_commands_source_more_related_use_the_last_answer(run):
    _, src, more, rel = run["scenarios"]["renewal"]
    assert src["kind"] == "source" and "IRPWM Para 616" in src["text"]
    assert more["kind"] == "more" and more["primary"]["para"] == "616"
    assert rel["kind"] == "related_list"


def test_follow_up_inherits_the_topic(run):
    _, f = run["scenarios"]["wear"]
    assert f["kind"] == "answer" and f["interpreted"] and f["primary"]["label"] == "IRPWM Para 429"


def test_out_of_scope_is_refused_not_guessed(run):
    r = run["scenarios"]["oos"][0]
    assert r["kind"] == "no_evidence" and r["points"] == 0


def test_a_fresh_question_is_not_dragged_into_the_previous_manual(run):
    _, r = run["scenarios"]["fresh_after_other_manual"]
    assert r["kind"] == "answer" and r["primary"]["alias"] != "USFD"


def test_reset_forgets_context(run):
    _, reset, more = run["scenarios"]["reset"]
    assert reset["kind"] == "reset" and more["kind"] == "no_context"
    assert run["scenarios"]["no_context"][0]["kind"] == "no_context"


def test_every_statement_shown_is_copied_from_the_cited_passage(run):
    g = run["grounding"]
    assert g["checked"] >= 100
    assert g["violations"] == [], g["violations"][:3]

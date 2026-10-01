"""The 20 real engineer-style questions (user-supplied, IRPWM 2024): none may be refused, and the cited paragraph must
stay the right one for the questions where it is (a regression guard, not an accuracy estimate: the grades are the
author's own reading of the answers)."""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run():
    out = subprocess.run(["node", "tests/chat_real.js"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def test_no_real_question_is_refused():
    assert [r["id"] for r in run() if r["kind"] != "answer"] == ["R19"]    # R19 asks about two manuals at once and clarifies


def test_right_paragraph_is_cited_for_the_questions_that_had_it():
    bad = [r["id"] for r in run() if r["grade"] != "wrong" and r["label"] != r["expected"]]
    assert bad == [], bad


def test_fully_correct_answers_keep_showing_their_key_numbers():
    bad = [(r["id"], r["facts"], r["total"]) for r in run() if r["grade"] == "correct" and r["facts"] < r["total"] - 1]
    assert bad == [], bad

import pathlib
from app.services.parser import parse_resume, parse_job
from app.services import matching
S = pathlib.Path(__file__).parent.parent / "seed"

def _ctx():
    p = parse_resume((S / "sample_resume.txt").read_text())
    jt = (S / "sample_job.txt").read_text()
    return p, parse_job(jt), jt

def test_evidence_classification():
    p, _, _ = _ctx()
    st = {s["skill"]: s["status"] for s in p["skill_evidence"]}
    assert st["fastapi"] == "proven"
    assert st["kubernetes"] == "insufficient_evidence"

def test_match_and_gaps():
    p, job, jt = _ctx()
    user = {s["skill"]: s["status"] for s in p["skill_evidence"]}
    r = matching.match(user, p["years_experience"], (S / "sample_resume.txt").read_text(), job, jt)
    assert "aws" in r["recommended_learning_order"]
    assert 0 <= r["score"] <= 100

def test_what_if_improves():
    p, job, jt = _ctx()
    user = {s["skill"]: s["status"] for s in p["skill_evidence"]}
    w = matching.what_if(user, 0.5, (S / "sample_resume.txt").read_text(), job, jt, ["aws"])
    assert w["steps"][0]["delta"] > 0

import csv
from pathlib import Path
import pytest
from app.prerequisites import evaluate, PrerequisiteError
from app.planner import Planner
from app.arabic import normalize, search_variants

DATA=Path(__file__).resolve().parents[1]/"data"
def rows(name):
    with (DATA/name).open(encoding="utf-8-sig") as f:return list(csv.DictReader(f))
@pytest.fixture
def planner():return Planner(rows("computer_engineering_courses.csv"),{"requirements":rows("degree_requirements.csv"),"degree_conflicts":[{"value":163}]})

@pytest.mark.parametrize("expression,done,expected",[
 ("",set(),True),("1",set(),False),("1",{"1"},True),
 ("(1 OR 2) AND (3 OR 4)",{"2","4"},True),
 ("(1 OR 2) AND (3 OR 4)",{"1"},False),
 ("1 OR 2 AND 3",{"1"},True),("1 OR 2 AND 3",{"2"},False),
 ("(10221231 OR 10641211) AND (10221253 OR 10641211)",{"10641211"},True)])
def test_logic(expression,done,expected):assert evaluate(expression,done)==expected
@pytest.mark.parametrize("expression",["__import__('os')","1 AND","(1 OR 2","1 XOR 2","1 2","1) OR 2"])
def test_bad_logic(expression):
    with pytest.raises(PrerequisiteError):evaluate(expression,{"1"})
def test_arabic():
    assert normalize("إِنذار ١٢") == "انذار 12"
    assert "انسحاب" in search_variants("بدي اسحب مادة")[1]
def test_real_complex_prerequisite(planner):
    course=planner.courses["10641373"]
    assert evaluate(course["prerequisite_expression"],{"10641211"})
def test_no_invented_project_sequence(planner):
    result=planner.plan(["10636410"],[])
    assert {"10636581","10636582"}<={c["course_code"] for c in result["eligible"]}
def test_ambiguity_not_eligible(planner):
    result=planner.plan(["10221101","10221102"],[])
    assert "10221115" in {c["course_code"] for c in result["needs_review"]}
    assert "10221115" not in {c["course_code"] for c in result["eligible"]}
def test_credit_caps_and_no_false_graduation(planner):
    completed=[c["course_code"] for c in planner.courses.values() if c["requirement_group"]=="major_elective"]
    result=planner.plan(completed,[])
    category=next(c for c in result["categories"] if c["key"]=="major_elective")
    assert category["earned"]>15 and category["counted"]==15
    assert not result["graduation_confirmed"]
    assert any("163" in w for w in result["warnings"])
def test_duplicate_completion_not_double_counted(planner):
    assert planner.plan(["11000101","11000101"],[])["earned_credits"]==3
def test_unknown_code_rejected(planner):
    with pytest.raises(ValueError):planner.plan(["99999999"],[])
def test_proposed_requires_previously_passed_prerequisites(planner):
    result=planner.plan([],["10211102"])
    assert not result["proposal_valid"]
def test_overload(planner):
    result=planner.plan([],[])
    choices=[c["course_code"] for c in result["eligible"] if int(c["credit_hours"])==3][:7]
    assert not planner.plan([],choices)["proposal_valid"]

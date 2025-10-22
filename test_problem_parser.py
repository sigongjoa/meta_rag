import pytest
from problem_parser import ProblemParser

def test_parse_only_text():
    parser = ProblemParser()
    problem = "This is a simple text problem with no formulas."
    result = parser.parse_problem(problem)
    assert result["text"] == "This is a simple text problem with no formulas."
    assert result["formulas"] == []
    assert result["metadata"] is None

def test_parse_inline_formula():
    parser = ProblemParser()
    problem = "The equation is $a+b=c$."
    result = parser.parse_problem(problem)
    assert result["text"] == "The equation is ."
    assert result["formulas"] == ["a+b=c"]
    assert result["metadata"] is None

def test_parse_display_formula():
    parser = ProblemParser()
    problem = "The main equation is $$x^2+y^2=z^2$$."
    result = parser.parse_problem(problem)
    assert result["text"] == "The main equation is ."
    assert result["formulas"] == ["x^2+y^2=z^2"]
    assert result["metadata"] is None
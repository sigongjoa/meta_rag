import pytest
import pytest_html
import pprint
from problem_parser import ProblemParser

def test_parse_only_text(extras):
    parser = ProblemParser()
    problem = "This is a simple text problem with no formulas."
    result = parser.parse_problem(problem)
    extras.append(pytest_html.extras.text(f"Input Problem:
{problem}", name="Input"))
    extras.append(pytest_html.extras.text(pprint.pformat(result), name="Parsed Output"))
    assert result["text"] == "This is a simple text problem with no formulas."
    assert result["formulas"] == []
    assert result["metadata"] is None

def test_parse_inline_formula(extras):
    parser = ProblemParser()
    problem = "The equation is $a+b=c$.
    result = parser.parse_problem(problem)
    extras.append(pytest_html.extras.text(f"Input Problem:
{problem}", name="Input"))
    extras.append(pytest_html.extras.text(pprint.pformat(result), name="Parsed Output"))
    assert result["text"] == "The equation is ."
    assert result["formulas"] == ["a+b=c"]
    assert result["metadata"] is None

def test_parse_display_formula(extras):
    parser = ProblemParser()
    problem = "The main equation is $$x^2+y^2=z^2$.
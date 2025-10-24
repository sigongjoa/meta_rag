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

def test_parse_latex_equation_block():
    parser = ProblemParser()
    problem = "Consider the following equation:\n\\begin{equation}\nx = \frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}\n\\end{equation}\nThis is the quadratic formula."
    result = parser.parse_problem(problem)
    assert result["text"] == "Consider the following equation: This is the quadratic formula."
    assert result["formulas"] == ["x = \frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}"]
    assert result["metadata"] is None

def test_parse_latex_align_block():
    parser = ProblemParser()
    problem = "Here is an alignment:\n\\begin{align}\nA &= B + C \\\\ \\label{eq:1}\\ \\ \\ &= D - E\n\\end{align}\nThis is an aligned equation."
    result = parser.parse_problem(problem)
    assert result["text"] == "Here is an alignment: This is an aligned equation."
    assert result["formulas"] == ["A &= B + C \\\\ \\label{eq:1}\\ \\ \\ &= D - E"]
    assert result["metadata"] is None

def test_parse_multiple_formulas():
    parser = ProblemParser()
    problem = "An inline formula $a=1$, a display formula $$\sum_{i=1}^n i = \\frac{n(n+1)}{2}$$, and an equation block \\begin{equation}e^{i\\pi} + 1 = 0\\end{equation}."
    result = parser.parse_problem(problem)
    assert result["text"] == "An inline formula , a display formula , and an equation block ."
    assert sorted(result["formulas"]) == sorted(["a=1", "\\sum_{i=1}^n i = \\frac{n(n+1)}{2}", "e^{i\\pi} + 1 = 0"])
    assert result["metadata"] is None

def test_parse_latex_gather_block():
    parser = ProblemParser()
    problem = "A gather environment: \\begin{gather} a = b+c \\\\ d = e+f+g \\end{gather}"
    result = parser.parse_problem(problem)
    assert result["text"] == "A gather environment:"
    assert result["formulas"] == ["a = b+c \\\\ d = e+f+g"]
    assert result["metadata"] is None
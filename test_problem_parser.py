import pytest
import pytest_html
import pprint
from problem_parser import ProblemParser

def test_parse_only_text(extras):
    print("--- Starting test_parse_only_text ---")
    parser = ProblemParser()
    problem = "This is a simple text problem with no formulas."
    print(f"Input problem string:\n{problem}")
    result = parser.parse_problem(problem)
    print(f"Parsed result:\n{pprint.pformat(result)}")
    extras.append(pytest_html.extras.text(f"""Input Problem:
{problem}""", name="Input"))
    extras.append(pytest_html.extras.text(pprint.pformat(result), name="Parsed Output"))
    assert result["text"] == "This is a simple text problem with no formulas."
    assert result["formulas"] == []
    assert result["metadata"] is None
    print("--- Finished test_parse_only_text ---")

def test_parse_inline_formula(extras):
    print("--- Starting test_parse_inline_formula ---")
    parser = ProblemParser()
    problem = "The equation is $a+b=c$. "
    print(f"Input problem string:\n{problem}")
    result = parser.parse_problem(problem)
    print(f"Parsed result:\n{pprint.pformat(result)}")
    extras.append(pytest_html.extras.text(f"""Input Problem:
{problem}""", name="Input"))
    extras.append(pytest_html.extras.text(pprint.pformat(result), name="Parsed Output"))
    assert result["text"] == "The equation is."
    assert result["formulas"] == ["a+b=c"]
    assert result["metadata"] is None
    print("--- Finished test_parse_inline_formula ---")

def test_parse_display_formula(extras):
    print("--- Starting test_parse_display_formula ---")
    parser = ProblemParser()
    problem = "The main equation is $$x^2+y^2=z^2$$. "
    print(f"Input problem string:\n{problem}")
    result = parser.parse_problem(problem)
    print(f"Parsed result:\n{pprint.pformat(result)}")
    extras.append(pytest_html.extras.text(f"""Input Problem:
{problem}""", name="Input"))
    extras.append(pytest_html.extras.text(pprint.pformat(result), name="Parsed Output"))
    assert result["text"] == "The main equation is."
    assert result["formulas"] == ["x^2+y^2=z^2"]
    assert result["metadata"] is None
    print("--- Finished test_parse_display_formula ---")

def test_parse_complex_problem(extras):
    print("--- Starting test_parse_complex_problem ---")
    parser = ProblemParser()
    problem = r"""This is a more complex problem. It has an inline formula, like $E=mc^2$, and also a display formula:
$$
\sum_{i=1}^{n} i = \frac{n(n+1)}{2}
$$
Here is another inline formula: $a^2 + b^2 = c^2$.
Let's also include a LaTeX environment:
\begin{equation}
\int_0^\infty e^{-x^2} dx = \frac{\sqrt{\pi}}{2}
\end{equation}
This should be parsed correctly. What do you think?
"""
    print(f"Input problem string:\n{problem}")
    result = parser.parse_problem(problem)
    print(f"Parsed result:\n{pprint.pformat(result)}")
    extras.append(pytest_html.extras.text(f"""Input Problem:
{problem}""", name="Input"))
    extras.append(pytest_html.extras.text(pprint.pformat(result), name="Parsed Output"))
    expected_text = "This is a more complex problem. It has an inline formula, like, and also a display formula: Here is another inline formula:. Let's also include a LaTeX environment: This should be parsed correctly. What do you think?"
    expected_formulas = sorted([
        "E=mc^2",
        "a^2 + b^2 = c^2",
        "\\sum_{i=1}^{n} i = \\frac{n(n+1)}{2}",
        "\\int_0^\\infty e^{-x^2} dx = \\frac{\\sqrt{\\pi}}{2}"
    ])
    assert result["text"] == expected_text
    assert result["formulas"] == expected_formulas
    assert result["metadata"] is None
    print("--- Finished test_parse_complex_problem ---")
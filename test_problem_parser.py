import pytest
from problem_parser import ProblemParser

@pytest.fixture
def parser():
    return ProblemParser()

def test_parse_simple_text_no_formulas(parser):
    problem_string = "이것은 간단한 문제입니다. 수학 공식은 포함되어 있지 않습니다."
    result = parser.parse_problem(problem_string)
    assert result["text"] == "이것은 간단한 문제입니다. 수학 공식은 포함되어 있지 않습니다."
    assert result["formulas"] == []
    assert result["metadata"] is None

def test_parse_inline_formula(parser):
    problem_string = "이것은 $x^2 + y^2 = z^2$ 와 같은 인라인 공식입니다."
    result = parser.parse_problem(problem_string)
    assert result["text"] == "이것은 와 같은 인라인 공식입니다."
    assert result["formulas"] == ["x^2 + y^2 = z^2"]
    assert result["metadata"] is None

def test_parse_display_formula(parser):
    problem_string = "다음은 중요한 공식입니다: $$E=mc^2$$"
    result = parser.parse_problem(problem_string)
    assert result["text"] == "다음은 중요한 공식입니다:"
    assert result["formulas"] == ["E=mc^2"]
    assert result["metadata"] is None

def test_parse_multiple_formulas_mixed(parser):
    problem_string = "문제 1: $a+b=c$. 문제 2: $$x^2-y^2=(x-y)(x+y)$$. 끝."
    result = parser.parse_problem(problem_string)
    assert result["text"] == "문제 1: . 문제 2: . 끝."
    assert set(result["formulas"]) == set(["a+b=c", "x^2-y^2=(x-y)(x+y)"])
    assert result["metadata"] is None

def test_parse_with_metadata(parser):
    problem_string = "회사명_문제유형: 이것은 메타데이터가 있는 문제입니다. $A=B$"
    result = parser.parse_problem(problem_string)
    assert result["text"] == "이것은 메타데이터가 있는 문제입니다."
    assert result["formulas"] == ["A=B"]
    assert result["metadata"] == {"company": "회사명", "problem_type": "문제유형"}

def test_parse_with_metadata_and_no_formula(parser):
    problem_string = "회사명_문제유형: 이것은 메타데이터만 있는 문제입니다."
    result = parser.parse_problem(problem_string)
    assert result["text"] == "이것은 메타데이터만 있는 문제입니다."
    assert result["formulas"] == []
    assert result["metadata"] == {"company": "회사명", "problem_type": "문제유형"}

def test_parse_latex_environment_formula(parser):
    problem_string = "다음은 방정식입니다.\n\begin{equation}\nx + y = z\n\end{equation}\n설명입니다."
    result = parser.parse_problem(problem_string)
    assert result["text"] == "다음은 방정식입니다. 설명입니다."
    assert result["formulas"] == ["x + y = z"]
    assert result["metadata"] is None

def test_parse_latex_align_environment_formula(parser):
    problem_string = "다음은 정렬된 방정식입니다.\n\begin{align}\nA &= B \\ C &= D\n\end{align}\n설명입니다."
    result = parser.parse_problem(problem_string)
    assert result["text"] == "다음은 정렬된 방정식입니다. 설명입니다."
    assert result["formulas"] == ["A &= B \\ C &= D"]
    assert result["metadata"] is None

def test_add_custom_formula_pattern(parser):
    parser.add_custom_formula_pattern("custom_tag", r'\\[(.*?)\\]')
    problem_string = "이것은 [커스텀 공식] 입니다."
    result = parser.parse_problem(problem_string)
    assert result["text"] == "이것은 입니다."
    assert result["formulas"] == ["커스텀 공식"]

def test_add_custom_metadata_pattern(parser):
    parser.add_custom_metadata_pattern(r'^ID:(?P<id>\\d+)'
)
    problem_string = "ID:12345 이것은 새로운 메타데이터 패턴입니다."
    result = parser.parse_problem(problem_string)
    assert result["text"] == "이것은 새로운 메타데이터 패턴입니다."
    assert result["metadata"] == {"id": "12345"}

def test_empty_string(parser):
    problem_string = ""
    result = parser.parse_problem(problem_string)
    assert result["text"] == ""
    assert result["formulas"] == []
    assert result["metadata"] is None

def test_formula_with_newlines_and_spaces(parser):
    problem_string = "$$  \n  x^2 + y^2 \n  = z^2  \n$$"
    result = parser.parse_problem(problem_string)
    assert result["text"] == ""
    assert result["formulas"] == ["x^2 + y^2 \n  = z^2"]
    assert result["metadata"] is None

def test_problem_with_only_formulas(parser):
    problem_string = "$a+b=c$$$E=mc^2$$"
    result = parser.parse_problem(problem_string)
    assert result["text"] == ""
    assert set(result["formulas"]) == set(["a+b=c", "E=mc^2"])
    assert result["metadata"] is None

def test_problem_with_only_metadata(parser):
    problem_string = "회사명_문제유형:"
    result = parser.parse_problem(problem_string)
    assert result["text"] == ""
    assert result["formulas"] == []
    assert result["metadata"] == {"company": "회사명", "problem_type": "문제유형"}

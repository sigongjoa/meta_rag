# RAG Enhancement: Data Schema Guide

This document provides the concrete data schema required to implement the `RAG_Enhancement_Plan.md` and `Implementation_Guide.md`. While those documents outline *what* needs to be done, this guide specifies *exactly what the data should look like*.

As per the plan, we need to manually create two core JSON files:

1.  `knowledge_base.json`: The entire problem bank (Knowledge Base) to be searched.
2.  `golden_queries.json`: The evaluation queries with pre-defined ground truth answers.

---

## 1. `knowledge_base.json` (Knowledge Base) Data Schema

This file is an extension of the `sample_problems` dictionary from `main.py`. Ideally, it should include not just the plain text, but also the processed results from `problem_parser.py` and 'concept' tags for future integration with a graph database.

### File Example: `knowledge_base.json`
```json
[
  {
    "id": "kb-001",
    "source": "수학(상) p.75 예제 1",
    "problem_text": "이차방정식 $x^2 - 4 = 0$의 해를 구하시오.",
    "parsed_text": "이차방정식 의 해를 구하시오.",
    "formulas": [
      "x^2 - 4 = 0"
    ],
    "concepts": ["이차방정식", "인수분해", "제곱근"]
  },
  {
    "id": "kb-002",
    "source": "수학 I p.112 문제 3",
    "problem_text": "등차수열 ${a_n}$에서 $a_3 = 5$, $a_7 = 13$일 때, 일반항 $a_n$을 구하시오.",
    "parsed_text": "등차수열 에서 , 일 때, 일반항 을 구하시오.",
    "formulas": [
      "{a_n}",
      "a_3 = 5",
      "a_7 = 13",
      "a_n"
    ],
    "concepts": ["등차수열", "일반항", "연립방정식"]
  },
  {
    "id": "kb-003",
    "source": "미적분 p.45 예제 2",
    "problem_text": "함수 $f(x) = x^2$의 $x=1$에서의 미분계수를 구하시오. 정의: $\lim_{h \to 0} \frac{f(1+h) - f(1)}{h}$",
    "parsed_text": "함수 의 에서의 미분계수를 구하시오. 정의:",
    "formulas": [
      "f(x) = x^2",
      "x=1",
      "\\lim_{h \\to 0} \\frac{f(1+h) - f(1)}{h}"
    ],
    "concepts": ["미분계수", "함수의 극한", "다항함수"]
  }
]
```
> **Note:** Meaningful evaluation can begin once this file contains at least 100-200 problems.

---

## 2. `golden_queries.json` (Ground Truth) Data Schema

This is the concrete format for the "30 test queries" and "5 ground truth IDs" that were to be manually matched, as specified in `RAG_Enhancement_Plan.md`. The `ground_truth_ids` must be sorted in order of similarity to calculate metrics like P'@10 and nDCG'.

### File Example: `golden_queries.json`
```json
[
  {
    "query_id": "gq-001",
    "query_text": "이차방정식의 근을 구하는 문제를 찾아줘. $x^2 = 4$와 비슷한 걸로.",
    "ground_truth_ids": [
      "kb-001", // 1st priority answer (most similar)
      "kb-088", // 2nd priority answer
      "kb-042", // 3rd priority answer
      "kb-115", // 4th priority answer
      "kb-019"  // 5th priority answer
    ]
  },
  {
    "query_id": "gq-002",
    "query_text": "미분계수의 정의를 이용하는 문제가 있나요? $\lim_{h \to 0}$ 이 기호가 들어간 것.",
    "ground_truth_ids": [
      "kb-003", // 1st priority answer
      "kb-177", // 2nd priority answer
      "kb-029", // 3rd priority answer
      "kb-101", // 4th priority answer
      "kb-055"  // 5th priority answer
    ]
  }
]
```
> **Note:** Creating about 30-50 of these queries will result in a powerful evaluation set.

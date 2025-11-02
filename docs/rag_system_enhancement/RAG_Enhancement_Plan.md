# Meta-RAG System Enhancement Plan

This document outlines the plan for enhancing the Meta-RAG system by defining clear metrics, building a benchmark dataset, and executing a structured action plan.

## 1. Metric: What to Measure (The Goal)

The primary direction is **"Improving the accuracy of math problem retrieval."** The metrics to measure this goal are well-defined in the `Meta-RAG_Math_Formula_Embedding_RAG_Report.md` report.

### a. Retrieval Performance Metrics (Core)

The core function of our RAG system is to retrieve the "correct similar problem" to enable the LLM to generate a good answer. Therefore, retrieval performance is the most critical metric.

*   **P'@10 (Precision at 10):** Measures how many of the top 10 search results are actual correct answers (similar problems).
*   **nDCG'@10 (Normalized Discounted Cumulative Gain):** Measures the quality of the ranking within the top 10 results, giving more weight to more accurate (more similar) problems appearing higher in the list.
*   **Partial bpref:** A specialized metric for math formula search that gives partial scores for matches on parts of a formula.

### b. End-to-End (E2E) Quality Metric

Ultimately, the system must generate a "thought process" that satisfies the user.

*   **Reward Score:** A score calculated by the `RewardEvaluator` designed in `Meta-RAG_Detailed_Design_PseudoCode.md`. This can include (1) the accuracy of the retrieved problem, (2) the logical coherence of the generated thought process, and (3) user feedback (👍/👎).

## 2. Benchmark: How to Measure (The Data)

Metrics are useless without data to measure. The 4 `sample_problems` in the PoC are insufficient to measure P'@10.

The most urgent task now is to build our own benchmark dataset, called a **"Golden Set"**.

*   **Step 1 (Knowledge Base Construction):** First, we need to expand the database of problems to be searched, increasing it to 100, 500, 1000, etc. (e.g., problems from Korean middle and high school math textbooks).
*   **Step 2 (Golden Set Construction):** From this, we will set aside 30-50 problems specifically for "queries". For each of these queries, a human will manually match and pre-define the "top 5 most similar problems" (these are the ground truth answers) from the Step 1 knowledge base.

Once this Golden Set is complete, we can calculate P'@10 and nDCG'@10 scores for any embedding model.

## 3. Action Plan: What to Do Now (The Plan)

The direction is clear: **"Build a Golden Set and find the embedding model that maximizes its P'@10 score."**

We will proceed with the following 4 steps in order:

### a. Build the Golden Set (Most Important)

1.  Expand `sample_problems` to at least 100 to create a knowledge base.
2.  Create a separate set of 30 test queries and manually match 5 "ground truth similar problems" for each query.

### b. [Metric 1] Measure Baseline Score

1.  Use the current PoC model (`get_dual_embedding` in `main.py`) to search against the Golden Set of 30 queries.
2.  Calculate the P'@10 score by comparing the results with the manually matched ground truth. This will be our "baseline score".

### c. [Metric 2] Measure Enhanced Model Score

1.  Implement the previously discussed TangentCFT or R-GCN model.
2.  Use this enhanced model to search against the same Golden Set of 30 queries.
3.  Recalculate the P'@10 score.

### d. Compare and Evaluate

1.  Compare the Baseline Score (PoC model) vs. the Enhanced Model Score.
2.  If the score has improved, the embedding enhancement is a success. This process can be repeated to continuously improve the metric scores.

> **Note:** The test performed in `test_embedding.py` ("Did it find problem ID 2 correctly?") was effectively measuring "P'@1". The most clear and immediate task is to expand this excellent test code into an evaluation script that measures P'@10 for the entire Golden Set.

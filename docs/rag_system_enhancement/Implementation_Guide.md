# RAG Enhancement: Implementation Guide

This document provides a detailed breakdown of the key documents and immediate next steps required to implement the `RAG_Enhancement_Plan.md`.

## Three Core Implementation Documents

To execute the enhancement plan, we need to understand and utilize the following three detailed documents.

### 1. [Model Implementation] "How to implement TangentCFT/R-GCN?"
*   **Required Detailed Document:** `Meta-RAG_Math_Formula_Embedding_RAG_Report.md`

*   **Explanation:**
    The `RAG_Enhancement_Plan.md` states, "Implement the TangentCFT or R-GCN model." The specific technical architecture and implementation details for this are already perfectly described in sections **2.2 (TangentCFT)** and **2.4 (R-GCN/ColBERT)** of the `Meta-RAG_Math_Formula_Embedding_RAG_Report.md`. This report is not just an idea; it is a **technical specification** that presents a concrete modeling method, including how to parse formulas into SLT/OPT trees and apply fastText or GNNs.

### 2. [Evaluation Implementation] "How to measure the P'@10 score?"
*   **Required Detailed Document:** `evaluate.py` (New code to be written)

*   **Explanation:**
    The `RAG_Enhancement_Plan.md` states, "Calculate the P'@10 score." The detailed document for this should be 'code', not a 'document'. An evaluation script named `evaluate.py`, which extends `test_embedding.py`, will serve as this 'detailed document'. This script must specifically contain the following logic:
    *   Logic to load `knowledge_base.json` and `golden_queries.json`.
    *   Logic to call the `get_dual_embedding` (Baseline) from `main.py` or the TangentCFT (Enhanced) model from step 1, embed the entire knowledge base, and build a FAISS index.
    *   Logic to iterate through `golden_queries`, execute searches, and calculate the P'@10 score by comparing the results with `ground_truth_ids`.

### 3. [Data Implementation] "What data is in the Golden Set?"
*   **Required Detailed Document:** `knowledge_base.json` / `golden_queries.json` (New data to be created)

*   **Explanation:**
    The `RAG_Enhancement_Plan.md` states, "Build the Golden Set." The detailed document for this is the actual data file itself. The first step of implementation is the manual creation of `knowledge_base.json` (with 100+ KB) and `golden_queries.json` (with 30 queries + 5 ground truth IDs each). Without this dataset, the evaluation script from step 2 is useless.

## Conclusion and Next Steps

The `RAG_Enhancement_Plan.md` is the 'map', and the implementation is the 'driving'. If the map tells us to "Take the P'@10 highway from Seoul to Busan," we must now actually prepare the car (data), turn on the navigation (evaluation script), and start driving in the first lane (TangentCFT).

**Summary:**

*   **Strategy Document (WHAT):** `RAG_Enhancement_Plan.md` (Direction set / **Complete**)
*   **Technical Specification (HOW-Model):** `Meta-RAG_Math_Formula_Embedding_RAG_Report.md` (Model blueprint / **To be utilized**)
*   **Data Specification (HOW-Data):** `golden_queries.json` (Ground truth / **To be built now**)
*   **Evaluation Specification (HOW-Metric):** `evaluate.py` (Score calculator / **To be built now**)

Therefore, **the immediate "detailed tasks" required now** are the manual work of creating `golden_queries.json` and the coding task of writing the `evaluate.py` script.

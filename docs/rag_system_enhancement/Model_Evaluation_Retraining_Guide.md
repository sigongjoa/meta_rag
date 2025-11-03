# Model Evaluation and Retraining Guide

**Goal:** To define the procedure for periodically measuring the performance of the current embedding model (e.g., TangentCFT) and replacing it with a better model (e.g., R-GCN).

## Key Content

### 1. Regular Evaluation

*   Add a scheduled `evaluate` job to the `CI_CD_Pipeline_Guide.md` to run once a month.
*   This job will execute the `evaluate.py` script defined in the `Implementation_Guide.md`.
*   It will calculate the current P'@10 score based on `golden_queries.json` and report the results.

### 2. Model Replacement Scenario (A/B Testing)

*   **Background:** The P'@10 score for Model A (TangentCFT) has stagnated at 52%.
*   **Development:** Develop Model B (R-GCN) and deploy it to a new Vertex AI Endpoint (Staging).
*   **Evaluation:** Run the `evaluate.py` script pointed at the Model B endpoint.
*   **Comparison:** Model A P'@10: 52% vs. Model B P'@10: 59%.
*   **Approval:** Model B's superior performance is proven.
*   **Execution:** Following the procedure in `KB_Management_Playbook.md`, re-embed the **entire KB (200 problems)** with Model B and replace the entire index in the Vertex AI Matching Engine.
*   **Deployment:** Modify the environment variables in `terraform/gcp/main.tf` to point the Cloud Run (FastAPI) service to the Model B endpoint and run `terraform apply`.

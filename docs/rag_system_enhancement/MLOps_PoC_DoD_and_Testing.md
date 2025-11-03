# MLOps PoC: Definition of Done (DoD) and Testing Plan

This document defines the Definition of Done and the testing plan for the MLOps and RAG System Enhancement phase of the Meta-RAG project.

---

## 1. Definition of Done (DoD)

To consider this MLOps Proof of Concept (PoC) complete, the following conditions must be met:

*   **[DoD-1] Evaluation Pipeline is Operational:**
    *   The `evaluate.py` script is implemented and successfully calculates P'@10 scores on a sample `golden_queries.json` and `knowledge_base.json`.
    *   The script is executable and provides a clear summary of the results.

*   **[DoD-2] KB Update Process is Proven:**
    *   The process described in `KB_Management_Playbook.md` is demonstrated to work.
    *   A new data point can be added to the `knowledge_base.json`, and the `upsert` functionality of the Vertex AI Matching Engine is successfully used to add the new vector to the live index without downtime.

*   **[DoD-3] Monitoring Dashboards are Configured:**
    *   A basic monitoring dashboard is set up in Google Cloud Monitoring (or equivalent).
    *   The dashboard tracks key System Health metrics (5xx errors, latency) for the API Gateway and Cloud Run as defined in `RAG_Monitoring_Alerting_Guide.md`.

*   **[DoD-4] Alerting is Simulated:**
    *   A basic alert is configured based on a System Health metric (e.g., a high latency alert).
    *   The alert is successfully triggered and a notification is received (e.g., via email or a log entry), proving the mechanism works.

---

## 2. Test Code Plan

To verify the functionality of the MLOps components, the following test code and scripts are required.

### a. `test_evaluate.py` (Unit Tests for Evaluation)

*   **Purpose:** To unit-test the `evaluate.py` script itself.
*   **Key Tests:**
    *   `test_load_data`: Mocks the JSON files and verifies that the data loading function correctly parses them.
    *   `test_calculate_metrics`: Provides mock retrieval results and ground truth to verify that the P'@10 and nDCG'@10 calculation logic is correct.
    *   `test_build_index`: Uses a small, fixed set of embeddings to ensure the FAISS index is built correctly.

### b. `test_kb_management.py` (Integration Test for KB Updates)

*   **Purpose:** To test the KB update and error correction process (the "Upsert" functionality).
*   **Test Flow:**
    1.  **Initial State:** Query the index for a specific vector and verify its existence.
    2.  **Update:** Use the Vertex AI SDK to `upsert` a modified version of that same vector (with the same ID).
    3.  **Verification:** Query the index again for the same ID and verify that the returned vector is the updated one.
    4.  **Add:** `upsert` a completely new vector with a new ID.
    5.  **Verification:** Query for the new ID and verify its existence.

### c. `test_monitoring_alerts.py` (Simulation Script)

*   **Purpose:** To simulate conditions that should trigger alerts, allowing for testing of the monitoring and alerting pipeline.
*   **Test Flow:**
    *   `simulate_high_latency()`: A function that sends a series of slow requests to the API endpoint to trigger the latency alert.
    *   `simulate_5xx_errors()`: A function that intentionally sends malformed requests or calls a test-only endpoint designed to return 5xx errors, triggering the error rate alert.

This plan provides a clear path to not only implement the MLOps features but also to ensure they are robust and reliable through automated testing.

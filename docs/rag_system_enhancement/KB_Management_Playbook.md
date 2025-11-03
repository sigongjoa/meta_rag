# KB Management Playbook

**Goal:** To define the procedures for keeping `knowledge_base.json` up-to-date and correcting errors.

## Key Content

### 1. KB Update Cadence

*   **Regular:** Once per quarter to reflect new curriculum.
*   **Ad-hoc:** Immediately upon confirmation from RAG Monitoring that a specific concept is missing due to "Retrieval Failures" or "User 👎 Feedback".

### 2. KB Update Procedure (Playbook)

1.  **Add Data:** Manually add new problem data (e.g., kb-201 to kb-210) to `knowledge_base.json`.
2.  **Generate Embeddings:** Run a separate script, such as `python run_embedding.py --file kb-new-chunk.json`, to embed only the 10 newly added problems (by calling the Vertex AI Endpoint).
3.  **Update Index:** Call the Vertex AI Matching Engine API to **add (Upsert)** the 10 newly generated vectors to the **existing index**. (This does not require application redeployment).

### 3. KB Error Correction Procedure

*   If a typo is found in problem `kb-042`, perform the same embed -> upsert process after correcting the `json` file to overwrite the existing vector.

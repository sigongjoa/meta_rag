# RAG Monitoring and Alerting Guide

**Goal:** To detect in real-time when the system is 'down' or 'degrading in performance'.

## Key Content

### 1. System Health Monitoring (via GCP/AWS Dashboard)

*   **API Gateway:**
    *   **5xx Error Rate:** Alert if > 1% over 5 minutes.
    *   **Latency:** Alert if response time > 2 seconds.
*   **Cloud Run:**
    *   Number of instances
    *   CPU/Memory usage
*   **Vertex AI Endpoint:**
    *   **Latency**
    *   **Traffic** (Directly related to cost)

### 2. RAG Quality Monitoring (The Core)

*   **Retrieval Failures:** The rate at which the Vertex AI Matching Engine returns zero search results.
*   **User Feedback Rate:** The hourly rate of '👎 (Dislike)' feedback collected via the `RewardEvaluator`.

### 3. Alerting Scenarios

*   **IF** 5xx Error Rate > 1% (for 5 minutes) **THEN** send an urgent alert to PagerDuty/Slack.
*   **IF** User '👎' Rate > 10% (for 1 hour) **THEN** automatically create a 'Quality Degradation' ticket in Jira/Asana.

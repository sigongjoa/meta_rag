# Troubleshooting 504 Gateway Timeout for API Gateway and Cloud Run

## Problem Description
The user encountered a `504 Gateway Timeout` error when their frontend application (running locally on `http://127.0.0.1:8001`) attempted to make an `OPTIONS` preflight request to the deployed Google Cloud API Gateway (`https://meta-rag-gateway-10puw1u9.an.gateway.dev/chat`). This error prevented the actual `POST` request from being sent.

## Debugging Process and Findings

### 1. Initial Hypothesis: Short API Gateway Deadline
*   **Hypothesis:** The `504 Gateway Timeout` might be due to an overly aggressive deadline for `OPTIONS` requests configured in the API Gateway's `openapi.yaml`. Cloud Run services can experience "cold starts," which might cause a delay in initial response.
*   **Action Taken:** Increased the `deadline` for the `OPTIONS /chat` endpoint in `docs/api/openapi.yaml` from `5` seconds to `30` seconds.
*   **Outcome:** The issue persisted; the user still reported `504 Gateway Timeout` for `OPTIONS` requests.
*   **Reason for Failure:** While a short deadline can contribute to timeouts, it was not the root cause in this scenario. The backend service was not successfully responding to the OPTIONS request at all, even with an extended deadline.

### 2. Deeper Investigation: Cloud Run Service Logs
To understand why the backend Cloud Run service was not responding successfully, the `gcloud` CLI was used to inspect the service's status and logs.

*   **Action Taken:**
    1.  Listed Cloud Run services to confirm deployment and service name:
        ```bash
        gcloud run services list --region=asia-northeast3 --project=<YOUR_GCP_PROJECT_ID>
        ```
        *   **Observation:** The service `meta-rag-backend-v2` was found to be running in `asia-northeast3`.
    2.  Read the logs of the `meta-rag-backend-v2` service:
        ```bash
        gcloud run services logs read meta-rag-backend-v2 --region=asia-northeast3 --limit=100
        ```
*   **Key Observation from Logs:** The logs showed entries like:
    ```
    2025-10-31 03:55:56 INFO:     169.254.169.126:57960 - "OPTIONS / HTTP/1.1" 405 Method Not Allowed
    ```
    This indicated that:
    *   The API Gateway *was* successfully forwarding the `OPTIONS` request to the Cloud Run service.
    *   The Cloud Run service was receiving the `OPTIONS` request at its **root path (`/`)**.
    *   The Cloud Run service (a FastAPI application) was explicitly rejecting this `OPTIONS /` request with a `405 Method Not Allowed` error. This is the default behavior for HTTP methods that do not have an explicitly defined route handler in FastAPI.

*   **Root Cause Identification:** The `openapi.yaml` configuration for the `OPTIONS /chat` endpoint had its `x-google-backend` address set to `${cloud_run_uri}`, meaning the API Gateway was routing the OPTIONS request to the root of the Cloud Run service (`/`), not to `/chat` or `/solve`. Since the FastAPI application did not have a handler for `OPTIONS /`, it returned a `405 Method Not Allowed`, which the API Gateway then interpreted as a failure to get a successful response, leading to the `504 Gateway Timeout`.

### 3. Second Attempted Fix: Adding CORS Middleware to FastAPI
To enable the FastAPI application to correctly handle `OPTIONS` requests and provide the necessary CORS headers, `CORSMiddleware` was added.

*   **Action Taken:** Modified `main.py` to include and configure `CORSMiddleware`:
    ```python
    from fastapi.middleware.cors import CORSMiddleware

    app = FastAPI(
        title="Meta-RAG PoC API",
        version="0.5.0", # Version updated for lifespan refactor
        lifespan=lifespan
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:8001"],  # Allow your frontend origin
        allow_credentials=True,
        allow_methods=["*"],  # Allow all methods (GET, POST, OPTIONS, etc.)
        allow_headers=["*"],  # Allow all headers
    )
    ```
*   **Purpose:** `CORSMiddleware` automatically intercepts `OPTIONS` requests, responds with appropriate CORS headers, and allows the actual cross-origin requests (like `POST /solve`) to proceed.

## Current Status and Next Steps for User
Despite the `CORSMiddleware` being added and pushed, the user is still reporting the `504 Gateway Timeout`.

**Possible reasons for persistence:**
1.  **Deployment Propagation:** It's possible that the latest Cloud Run service deployment (with the CORS middleware) has not fully propagated or taken effect. Cloud Run deployments can sometimes take a few minutes.
2.  **Frontend Origin Mismatch:** Double-check that `allow_origins=["http://127.0.0.1:8001"]` in `main.py` exactly matches the origin of the frontend application making the request.
3.  **API Gateway Caching:** The API Gateway might be caching an older configuration. A redeployment of the API Gateway (which happens automatically when `openapi.yaml` is changed via Terraform) should clear this, but it's worth considering.

**User Action Required:**
1.  **Verify Cloud Run Deployment:** In the GCP console, confirm that the `meta-rag-backend-v2` Cloud Run service has successfully deployed the latest revision (the one including the CORS middleware changes).
2.  **Re-test Frontend:** Once the Cloud Run deployment is confirmed, try making the request from the frontend again.
3.  **Provide New Logs:** If the issue persists, please provide the latest Cloud Run service logs after the deployment, as well as any new error messages from the browser's developer console.

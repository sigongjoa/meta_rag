# Meta-RAG Deployment Troubleshooting Report

This document summarizes the troubleshooting process for the deployment issues encountered with the Meta-RAG application.

## 1. Initial Problem: 405 Method Not Allowed

The initial problem was a `405 Method Not Allowed` error when trying to access the service. This was caused by a mismatch between the API Gateway configuration and the client application's request path.

*   **Problem:** The API Gateway was configured to expose the `/solve` endpoint, but the client application was sending requests to the `/chat` endpoint.
*   **Solution:** The `openapi.yaml` file was modified to expose the `/chat` endpoint and use `path_translation` to route requests to the `/solve` endpoint on the Cloud Run service.

## 2. Deployment Error: Image Not Found

During the deployment process, a new error occurred: `Image not found`. This was because the Docker image tag was not correctly specified in the `terraform apply` command.

*   **Problem:** The `terraform apply` command was using the `:latest` tag, but the CI/CD pipeline tags images with the git commit SHA.
*   **Solution:** The correct image tag (the git commit SHA) was retrieved and used in the `terraform apply` command.

## 3. Runtime Error: 500 Internal Server Error

After the deployment was successful, the service started returning a `500 Internal Server Error`. This was caused by a bug in the Cloud Run application code.

*   **Problem:** The `find_neighbors` function in `main.py` was being called without the required `deployed_index_id` argument.
*   **Solution:** The `main.py` file was updated to pass the `deployed_index_id` to the `find_neighbors` function. The `deployed_index_id` was passed to the Cloud Run service as an environment variable.

## 4. Recommendations for the Future

To avoid these issues in the future, the following recommendations should be followed:

*   **Ensure client-server contract:** The client application and the API Gateway configuration must be in sync. Any changes to the API endpoint paths should be reflected in both the client and the `openapi.yaml` file.
*   **Use a consistent image tagging strategy:** Use a consistent tagging strategy for Docker images, such as using the git commit SHA. This will help to avoid confusion and ensure that the correct image is deployed.
*   **Implement robust error handling:** The application code should include more robust error handling to catch missing arguments and other potential issues.
*   **Implement comprehensive health checks:** Implement a more comprehensive health check for the Cloud Run service that verifies all the required dependencies and configurations.

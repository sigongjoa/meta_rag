# Terraform API Gateway Templating Guide

This document outlines the correct procedure for using template files for the OpenAPI specification in a Terraform configuration for Google Cloud API Gateway.

## 1. Problem

When applying the Terraform configuration, the following error occurs:

```
Error: Error creating ApiConfig: googleapi: Error 400: com.google.apps.framework.request.BadRequestException: Cannot convert to service config.
'location:  "unknown location"
kind: ERROR
message: "OpenAPI file 'openapi.yaml.tpl' has invalid extension 'tpl'. Only files with {yaml, yml, json} file extensions are allowed."
```

This error happens because the `google_api_gateway_api_config` resource was configured with the `path` attribute pointing to a file with a `.tpl` extension. The Google Cloud provider only accepts `.yaml`, `.yml`, or `.json` files for the OpenAPI specification. The `.tpl` file is a Terraform template file and cannot be processed directly by the API Gateway.

## 2. Solution: Using `templatefile`

The correct approach is to use Terraform's built-in `templatefile` function. This function reads a template file, substitutes variables, and returns the rendered content as a string. This string can then be passed to the `contents` attribute of the `openapi_documents` block.

### Provider Versions

This solution is confirmed to work with the following provider versions in `terraform/gcp/main.tf`:

- **google:** `>= 5.25.0`
- **google-beta:** `>= 5.25.0`

### Implementation Steps

1.  **Ensure the API resource exists:** The `google_api_gateway_api` resource must be defined.

    ```terraform
    resource "google_api_gateway_api" "api" {
      provider = google-beta
      project  = var.gcp_project_id
      api_id   = var.api_id
    }
    ```

2.  **Modify the API Config resource:** In the `google_api_gateway_api_config` resource, remove the `path` attribute and use the `contents` attribute with the `templatefile` and `base64encode` functions. The `api` attribute should also be updated to depend on the `google_api_gateway_api` resource.

    ```terraform
    resource "google_api_gateway_api_config" "api_config" {
      provider      = google-beta
      project       = var.gcp_project_id
      api           = google_api_gateway_api.api.api_id // Explicit dependency
      api_config_id = var.api_config_id

      openapi_documents {
        document {
          // The path attribute is removed.
          // path = "openapi.yaml.tpl" 
          
          // Use `contents` to provide the rendered template, base64 encoded.
          contents = base64encode(templatefile("${path.module}/../../docs/api/openapi.yaml.tpl", {
            cloud_run_uri = data.google_cloud_run_v2_service.default.uri
          }))
        }
      }
      lifecycle {
        create_before_destroy = true
      }
    }
    ```

3.  **Update the Gateway resource:** Modify the `google_api_gateway_gateway` to use the `name` attribute from the `api_config` resource, ensuring an explicit dependency.

    ```terraform
    resource "google_api_gateway_gateway" "gateway" {
      provider     = google-beta
      api_config   = google_api_gateway_api_config.api_config.name // Use direct reference
      region       = "asia-northeast1"
      gateway_id   = var.gateway_id
      display_name = var.gateway_id
    }
    ```

By following these steps, the OpenAPI template will be correctly rendered and applied, resolving the deployment error.

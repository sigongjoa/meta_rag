
import requests
import json

def test_solve_endpoint():
    # URL of the local API endpoint
    url = "http://127.0.0.1:8000/solve"

    # The input data for the POST request
    data = {
        "problem_text": "What is the derivative of $x^2$?"
    }

    # Set the headers for the request
    headers = {
        "Content-Type": "application/json"
    }

    try:
        # Send the POST request
        response = requests.post(url, data=json.dumps(data), headers=headers)

        # Raise an exception if the request was unsuccessful
        response.raise_for_status()

        # Parse the JSON response
        response_data = response.json()

        # Print the response from the server
        print("API Response:")
        print(json.dumps(response_data, indent=2))

        # Assertions to verify the response
        assert "message" in response_data
        assert response_data["message"] == "Successfully generated thought process using Vertex AI."
        assert "received_problem" in response_data
        assert "retrieved_similar_problem" in response_data
        assert "generated_thought_process" in response_data
        
        print("\nIntegration test passed successfully!")

    except requests.exceptions.RequestException as e:
        print(f"\nAn error occurred during the API request: {e}")
        # If the test fails, we should exit with a non-zero code to indicate failure
        exit(1)

if __name__ == "__main__":
    test_solve_endpoint()

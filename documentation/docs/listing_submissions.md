# Listing your submission forecast skill scores

This section provides an example of how to list your submissions and retrieve the submitted forecast time-series.

## Retrieving your historical submissions forecasts:

Here's how you can retrieve the list your past submissions.

```python title="download_submissions.py"
--8<-- "docs/examples/download_submissions.py"
```

### JSON Example Response 
??? example "Click to view Example Response"

    ```json
    {
      "code": 200,
      "data": [
        {
          "id": "41ccbb67-1612-4045-8674-671e7631777d",
          "market_session_challenge_resource_id": "ba7203df-0618-4001-a2e9-b0a11cc477f9",
          "variable": "q50",
          "registered_at": "2024-10-25T15:35:04.213124Z",
          "market_session_challenge": "77c6e03a-0e45-467c-aa81-2cb7fb11c497",
          "user": "6a71b254-8a52-4dd8-a345-32c02af3ebb0"
        }
      ]
    }
    ```
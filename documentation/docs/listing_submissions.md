# Listing your submission forecast skill scores

This section provides an example of how to list your submissions and retrieve the submitted forecast time-series.

## API Endpoints:

To interact with the Predicto API and retrieve information about 
your submissions and respective submitted forecast time-series, 
you can use the following endpoints:

- **GET** [`/api/v1/market/challenge/submission`](https://127.0.0.1/redoc/#tag/market/operation/get_market_session_submission) - Retrieve a list of your previous submissions (and respective challenges).
- **GET** [`/api/v1/market/challenge/submission/forecasts`](https://127.0.0.1/redoc/#tag/market/operation/get_market_session_submission_forecasts) - Retrieve your forecasted time-series for a specific submission or challenge.


!!! important "Access Token Required"
    An access token must be included in the `Authorization` header of your request. If you haven't obtained an access token yet, please refer to the [Authentication](authentication.md) section.

!!! tip "Check this out"
    Check our [Useful Links](useful_links.md) section for additional resources (Jupyter Notebook, API Specifications) to help you get started with the Predico platform.


## Retrieving your historical submissions forecasts:

Here's how you can retrieve the list your past submissions.

```python title="download_submissions.py"
--8<-- "docs/examples/download_submissions.py"
```

<a href="../examples/download_submissions.py" download="download_submissions.py"><b>Download Full Example</b></a>


### JSON Example Response 

After running the example script, you will have access your submissions list and the respective forecasted time-series. 

If no data is received, please confirm if you are requesting data for the right challenge and/or resource identifier. 


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

## What's next?

Learn how to list your submission scores on the Predico platform in the [Listing Submission Scores](listing_submissions_scores.md) section.

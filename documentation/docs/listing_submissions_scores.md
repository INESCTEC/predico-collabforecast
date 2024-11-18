# Listing your submission forecast skill scores

This section provides an example of how to access your submissions forecast skill scores and relative rank to other forecasters.

## API Endpoints:

To interact with the Predicto API and retrieve information about 
your submissions scores,
you can use the following endpoints:

- **GET** [`/api/v1/market/challenge/submission`](https://127.0.0.1/redoc/#tag/market/operation/get_market_session_submission) - Retrieve a list of your previous submissions (and respective challenges).
- **GET** [`/api/v1/market/challenge/submission-scores`](https://127.0.0.1/redoc/#tag/market/operation/get_market_session_submission_scores) - Retrieve a list of your submissions scores and relative ranking to other forecasters.

!!! important "Access Token Required"
    An access token must be included in the `Authorization` header of your request. If you haven't obtained an access token yet, please refer to the [Authentication](authentication.md) section.

!!! tip "Check this out"
    Check our [Useful Links](useful_links.md) section for additional resources (Jupyter Notebook, API Specifications) to help you get started with the Predico platform.


## Retrieving your historical submissions:

Here's how you can retrieve the list your past submissions.

```python title="download_submissions_scores.py"
--8<-- "docs/examples/download_submissions_scores.py:10:22"
```

## For each submission, you can then retrieve the forecast skill scores:

```python title="download_submissions_scores.py"
--8<-- "docs/examples/download_submissions_scores.py:24:46"
```


<a href="../examples/download_submissions_scores.py" download="download_submissions_scores.py"><b>Download Full Example</b></a>


### JSON Example Response 

After running the example script, you will have access your submissions scores to the final ensemble forecasts.

Note that you will only have access to submission scores once the evaluation phase of the challenge has been completed (which depends on the measurements data availability for the challenge period).

If you are not seeing any data during some days, please confirm if you are requesting data for the right challenge identifier. 



??? example "Click to view Example Response"

    ```json
    {
      "code": 200,
      "data": {
        "personal_metrics": [
          {
            "submission": "41ccbb67-1612-4045-8674-671e7631777d",
            "variable": "q50",
            "metric": "mae",
            "value": 44.231,
            "rank": 1,
            "total_participants": 3
          },
          {
            "submission": "41ccbb67-1612-4045-8674-671e7631777d",
            "variable": "q50",
            "metric": "pinball",
            "value": 22.115,
            "rank": 1,
            "total_participants": 3
          },
          {
            "submission": "41ccbb67-1612-4045-8674-671e7631777d",
            "variable": "q50",
            "metric": "rmse",
            "value": 54.162,
            "rank": 1,
            "total_participants": 3
          }
        ],
        "general_metrics": [
          {
            "submission__variable": "q50",
            "metric": "mae",
            "avg_value": 496.221,
            "min_value": 44.231,
            "max_value": 1392.914,
            "std_value": 634.065
          },
          {
            "submission__variable": "q50",
            "metric": "pinball",
            "avg_value": 248.11,
            "min_value": 22.115,
            "max_value": 696.457,
            "std_value": 317.032
          },
          {
            "submission__variable": "q50",
            "metric": "rmse",
            "avg_value": 511.077,
            "min_value": 54.162,
            "max_value": 1416.82,
            "std_value": 640.465
          }
        ]
      }
    }
    ```

## What's next?

Learn how to list your submission contribution (i.e., to the final ensemble forecasts) on the Predico platform in the [Listing Submission Contributions](listing_submissions_contributions.md) section.
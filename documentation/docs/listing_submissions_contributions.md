# Listing your submission forecast skill scores

This section provides an example of how to list your submissions contributions to the final ensemble forecasts.

## API Endpoints:

To interact with the Predicto API and retrieve information about 
your submission contributions to the final ensemble forecasts,
you can use the following endpoints:

- **GET** [`/api/v1/market/challenge/submission`](https://predico-elia.inesctec.pt/redoc/#tag/market/operation/get_market_session_submission) - Retrieve a list of your previous submissions (and respective challenges).
- **GET** [`/api/v1/market/challenge/ensemble-weights`](https://predico-elia.inesctec.pt/redoc/#tag/market/operation/get_market_session_ensemble_weights) - Retrieve a list of your submissions scores and relative ranking to other forecasters.


!!! important "Access Token Required"
    An access token must be included in the `Authorization` header of your request. If you haven't obtained an access token yet, please refer to the [Authentication](authentication.md) section.


!!! tip "Check this out"
    Check our [Useful Links](useful_links.md) section for additional resources (Jupyter Notebook, API Specifications) to help you get started with the Predico platform.


## Retrieving your historical submissions:

Here's how you can retrieve the list your past submissions.

```python title="download_submissions_contributions.py"
--8<-- "docs/examples/download_submissions_contributions.py:10:22"
```

## For each submission, you can then retrieve the forecast skill scores:

```python title="download_submissions_contributions.py"
--8<-- "docs/examples/download_submissions_contributions.py:24:46"
```


<a href="../examples/download_submissions_contributions.py" download="download_submissions_contributions.py"><b>Download Full Example</b></a>


### JSON Example Response 

After running the example script, you will have access your submissions contributions to the final ensemble forecasts.

Note that you will only have access to submission contributions once the evaluation phase of the challenge has been completed (which depends on the measurements data availability for the challenge period).

If you are not seeing any data during some days, please confirm if you are requesting data for the right challenge identifier. 


??? example "Click to view Example Response"

    ```json
    {
      "code": 200,
      "data": [
        {
          "ensemble": "ac63fe9a-302c-45a1-bbe6-812b85f48dc2",
          "variable": "q10",
          "rank": 1,
          "total_participants": 3
        },
        {
          "ensemble": "87380061-cefe-4bc4-9aaa-87d9304dd342",
          "variable": "q90",
          "rank": 1,
          "total_participants": 3
        },
        {
          "ensemble": "96afa99b-adbe-41ec-8a6c-16c092367520",
          "variable": "q50",
          "rank": 1,
          "total_participants": 3
        }
      ]
    }
    ```
# Listing your historical forecasts

This section provides an example of how to preview the historical forecasts you initially submitted into the platform.

!!! important "Important"
    - The data is provided at a **15-minute resolution**, resulting in a large volume of samples. Therefore, **pagination** (Limit/Offset Strategy) is required to retrieve all data properly.


## API Endpoints:

To interact with the Predicto API and retrieve information about 
your historical forecasts available in the platform, 
you can use the following endpoints:

- **GET** [`/api/v1/data/individual-forecasts/historical`](https://127.0.0.1/redoc/#tag/data/operation/get_individual_forecasts_historical) - Retrieve your forecasted time-series for a specific submission or challenge.


!!! important "Access Token Required"
    An access token must be included in the `Authorization` header of your request. If you haven't obtained an access token yet, please refer to the [Authentication](authentication.md) section.

!!! tip "Check this out"
    Check our [Useful Links](useful_links.md) section for additional resources (Jupyter Notebook, API Specifications) to help you get started with the Predico platform.


## Specify a resource to download data for

If you do not know a resource identifier (UUID), you can retrieve it from current or previous challenges (see [Listing Challenges](listing_challenges.md) section.) 

```python title="download_historical_forecasts.py"
--8<-- "docs/examples/download_historical_forecasts.py:10:11"
```

## Retrieving Historical Forecasts for this resource

Retrieve the raw data for the selected resource:

```python title="download_historical_forecasts.py"
--8<-- "docs/examples/download_historical_forecasts.py:13:38"
```

<a href="../examples/download_historical_forecasts.py" download="download_historical_forecasts.py"><b>Download Full Example</b></a>


### JSON Example Response 

After running the example script, you will have access your historical forecasted time-series. 

If no data is received, please confirm if you are requesting data for the right challenge and/or resource identifier. 

!!! warning "Warning"

    - You will not have access to your submissions via this endpoint, just the initial historical forecasts upload. 
    - To access your submitted forecasts (to challenges), please refer to the [Listing Submissions](listing_submissions.md) section.


??? example "Click to view Example Response"

    ```json
    {
      "code": 200,
      "data": {
        "count": 2,
        "next": null,
        "previous": null,
        "results": [
          {
            "datetime": "2024-06-20T00:00:00Z",
            "launch_time": "2024-06-24T09:00:00Z",
            "variable": "q90",
            "value": 0.101,
            "registered_at": "2024-06-24T09:00:43.430995Z"
          },
          {
            "datetime": "2024-06-20T00:00:00Z",
            "launch_time": "2024-06-24T12:15:00Z",
            "variable": "q10",
            "value": 0.776,
            "registered_at": "2024-06-24T12:17:54.804330Z"
          }
        ]
      }
    }
    ```


# Downloading Raw Data

After selecting a challenge, the next step is to download the raw observed data associated with the challenge's resource. Market Makers send time-series data periodically, which includes raw measurement data for their registered resources (e.g., wind farm #1).

!!! important "Important"
    - The data is provided at a **15-minute resolution**, resulting in a large volume of samples. Therefore, **pagination** (Limit/Offset Strategy) is required to retrieve all data properly.


## API Endpoints:

To interact with the Predicto API and retrieve information about 
the raw measurements for a specific challenge target resource,
you can use the following endpoints:

- **GET** [`/api/v1/market/challenge`](https://127.0.0.1/redoc/#tag/market/operation/get_market_session_challenge) - Retrieve challenges for an open market session.
- **GET** [`/api/v1/data/raw-measurements/`](https://127.0.0.1/redoc/#tag/data/operation/get_raw_data) - Retrieve raw measurements for a specific challenge target resource.


!!! important "Access Token Required"
    An access token must be included in the `Authorization` header of your request. If you haven't obtained an access token yet, please refer to the [Authentication](authentication.md) section.


!!! tip "Check this out"
    Check our [Useful Links](useful_links.md) section for additional resources (Jupyter Notebook, API Specifications) to help you get started with the Predico platform.


## Selecting a Challenge

First, select a challenge from the list of challenges you have retrieved:

```python title="download_raw_measurements.py"
--8<-- "docs/examples/download_raw_measurements.py:28:34"
```

## List challenge resource info

This allows you to get more information on the data availability for this challenge target resource raw measurements.


```python title="download_raw_measurements.py"
--8<-- "docs/examples/download_raw_measurements.py:36:43"
```


## Retrieving Raw Data for a Challenge

Retrieve the raw data for the selected resource:

```python title="download_raw_measurements.py"
--8<-- "docs/examples/download_raw_measurements.py:45:71"
```

<a href="../examples/download_raw_measurements.py" download="download_raw_measurements.py"><b>Download Full Example</b></a>


### JSON Example Response 

After running the example script, you will have access to the full dataset of raw measurements data published by the Market Maker. 
If no data is received, please confirm if you are requesting data for the right resource identifier. 


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
            "datetime": "2024-05-20T09:15:00Z",
            "value": 0.182,
            "units": "mw",
            "resource": "b92c96d1-f5ee-4f96-a4cc-216a92acb10b",
            "registered_at": "2024-06-24T09:19:19.428512Z",
            "resource_name": "wind_farm_1"
          },
          {
            "datetime": "2024-05-20T09:30:00Z",
            "value": 0.772,
            "units": "mw",
            "resource": "b92c96d1-f5ee-4f96-a4cc-216a92acb10b",
            "registered_at": "2024-06-24T09:19:19.428512Z",
            "resource_name": "wind_farm_1"
          }
        ]
      }
    }
    ```

## What's next?

Learn how to prepare a forecast submission in the [Preparing a Forecast](preparing_forecast.md) section.

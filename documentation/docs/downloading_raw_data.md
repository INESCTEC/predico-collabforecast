# Downloading Raw Data

After selecting a challenge, the next step is to download the raw observed data associated with the challenge's resource. Market Makers send time-series data periodically, which includes raw measurement data for their registered resources (e.g., wind farm #1).

!!! info "Note"
    - This step can be replicated for every challenge. In this example, we'll select the first challenge from the list.
    - The data is provided at a **15-minute resolution**, resulting in a large volume of samples. Therefore, **pagination** (Limit/Offset Strategy) is required to retrieve all data properly.

!!! info "Prerequisites"

    - **Access Token**: Ensure you have a valid access token. Refer to the [Authentication](authentication.md) section if needed.
    - **Challenges List**: You should have a list of challenges retrieved. See [Listing Challenges](listing_challenges.md) section to obtain this list.

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
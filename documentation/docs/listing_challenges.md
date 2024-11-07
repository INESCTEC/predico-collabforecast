# Listing Challenges for Market Sessions

After retrieving the open market sessions, you may want to list the challenges associated with a specific market session. 
Challenges are opportunities published by the Market Maker (Elia) that Forecasters can submit forecasts for.

## API Endpoints:

To interact with the Predicto API and retrieve information about 
challenges published in open market sessions, 
you can use the following endpoints:

- **GET** [`/api/v1/market/session`](https://predico-elia.inesctec.pt/redoc/#tag/market/operation/get_market_session) - Retrieve list of market sessions (you can filter by 'open' sessions with query parameters)
- **GET** [`/api/v1/market/challenge`](https://predico-elia.inesctec.pt/redoc/#tag/market/operation/get_market_session_challenge) - Retrieve challenges for an open market session.


!!! info "Prerequisites"
    - **Access Token**: Ensure you have a valid access token. Refer to the [Authentication](authentication.md) section if needed.
    - **Open Market Session ID**: You should have the ID of the open market session you're interested in. See [Listing Open Sessions](listing_open_sessions.md) to retrieve it.

!!! tip "Check this out"
    Check our [Useful Links](useful_links.md) section for additional resources (Jupyter Notebook, API Specifications) to help you get started with the Predico platform.


## Retrieving Challenges for an Open Market Session

Here's how you can retrieve the list of registered challenges for a specific open market session using Python:

```python title="list_challenges_for_open_session.py"
--8<-- "docs/examples/list_challenges_for_open_session.py"
```

<a href="../examples/list_challenges_for_open_session.py" download="list_challenges_for_open_session.py"><b>Download Full Example</b></a>


### JSON Example Response 

After running the example script, you will receive a response containing a list of market challenges. 
It's important to verify whether the response contains any data, as there may be not challenges created yet, by the Market Maker. 

If the response is empty, you may need to try again later.

??? example "Click to view Example Response"

    ```json
    {
      "code": 200,
      "data": [
        {
          "id": "ef3a473f-0fcf-4880-8b42-93f6bf732e3a",
          "use_case": "wind_power",
          "start_datetime": "2024-06-24T22:00:00Z",
          "end_datetime": "2024-06-25T21:45:00Z",
          "target_day": "2024-06-25",
          "registered_at": "2024-06-24T09:19:33.990638Z",
          "updated_at": "2024-06-24T09:19:33.990638Z",
          "user": "3ca74375-2ac0-46f4-b4bf-7cf013d0c28f",
          "resource": "b92c96d1-f5ee-4f96-a4cc-216a92acb10b",
          "market_session": 1,
          "resource_name": "wind_farm_x"
        }
      ]
    }
    ```

## What's next?

Learn how to download measurements data information (published by Market Makers) on the Predico platform in the [Downloading Raw Data](downloading_raw_data.md) section.

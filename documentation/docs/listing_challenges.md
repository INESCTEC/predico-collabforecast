# Listing Challenges for Open Market Sessions

After retrieving the open market sessions, you may want to list the challenges associated with a specific open market session. Challenges are opportunities published by the Market Maker (Elia) that Forecasters can submit forecasts for.

!!! info "Prerequisites"
    - **Access Token**: Ensure you have a valid access token. Refer to the [Authentication](authentication.md) section if needed.
    - **Open Market Session ID**: You should have the ID of the open market session you're interested in. See [Listing Open Market Sessions](listing_open_market_sessions.md) to retrieve it.

## Retrieving Challenges for an Open Market Session

Here's how you can retrieve the list of registered challenges for a specific open market session using Python:

```python title="list_challenges_for_open_session.py"
--8<-- "docs/examples/list_challenges_for_open_session.py"
```

<a href="../examples/list_challenges_for_open_session.py" download="list_challenges_for_open_session.py"><b>Download Full Example</b></a>


### JSON Example Response 
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
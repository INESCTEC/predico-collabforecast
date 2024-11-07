# Listing Open Sessions

The most basic type of interaction is to list existing market sessions. Specifically, to check if there is any open market session available at this moment.

## API Endpoints:

To interact with the Predicto API and retrieve information about 
open market sessions, 
you can use the following endpoints:

- **GET** [`/api/v1/market/session`](https://predico-elia.inesctec.pt/redoc/#tag/market/operation/get_market_session) - Retrieve list of market sessions (you can filter by 'open' sessions with query parameters)

!!! important "Access Token Required"
    An access token must be included in the `Authorization` header of your request. If you haven't obtained an access token yet, please refer to the [Authentication](authentication.md) section.

!!! tip "Check this out"
    Check our [Useful Links](useful_links.md) section for additional resources (Jupyter Notebook, API Specifications) to help you get started with the Predico platform.


## Retrieving Current Open Sessions

Here's how you can retrieve the current open market sessions using Python:

```python title="list_open_market_sessions.py"
--8<-- "docs/examples/list_open_market_sessions.py"
```

<a href="../examples/list_open_market_sessions.py" download="list_open_market_sessions.py"><b>Download Full Example</b></a>


## Expected Response

After making the request, you will receive a response containing a list of open market sessions. 
It's important to verify whether the response contains any data, as there may be times when no sessions are open. 
Market sessions run periodically once a day, so if the response is empty, you may need to try again later.


### JSON Example Response 
??? example "Click to view Example Response"

    ```json
    {
      "code": 200,
      "data": [
        {
          "id": 1,
          "open_ts": "2024-06-24T09:19:23.251536Z",
          "close_ts": null,
          "launch_ts": null,
          "finish_ts": null,
          "status": "open"
        }
      ]
    }
    ```

## What's next?

Learn how to list session challenges information on the Predico platform in the [Listing Challenges](listing_challenges.md) section.

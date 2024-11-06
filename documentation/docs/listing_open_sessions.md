# Listing Open Sessions

To interact with the Predico API and retrieve information about open market sessions, you need to make an authenticated GET request to the `/api/v1/market/session` endpoint.

!!! info "Access Token Required"
    An access token must be included in the `Authorization` header of your request. If you haven't obtained an access token yet, please refer to the [Authentication](authentication.md) section.

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
# Listing Open Market Sessions

To interact with the Predico API and retrieve information about open market sessions, you need to make an authenticated GET request to the `/api/v1/market/session` endpoint.

!!! info "Access Token Required"
    An access token must be included in the `Authorization` header of your request. If you haven't obtained an access token yet, please refer to the [Authentication](authentication.md) section.

## Retrieving Current Open Market Sessions

Here's how you can retrieve the current open market sessions using Python:

```python title="list_open_market_sessions.py"
import requests

access_token = "your_access_token_here"

response = requests.get(
    url='https://predico-elia.inesctec.pt/api/v1/market/session',
    params={"status": "open"},
    headers={
        'Accept': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }
)

# Check if the request was successful
if response.status_code == 200:
    market_sessions = response.json()
    print("Open Market Sessions:")
    for session in market_sessions:
        print(f"- Session ID: {session['id']}, Name: {session['name']}")
else:
    print(f"Failed to retrieve market sessions. Status code: {response.status_code}")
```

## Expected Response

After making the request, you will receive a response containing a list of open market sessions. 
It's important to verify whether the response contains any data, as there may be times when no sessions are open. 
Market sessions run periodically once a day, so if the response is empty, you may need to try again later.


### JSON Example Response 
??? example "Click to view Example Response"

    ```json
    [
        {
            "id": 1,
            "name": "Session Q1 2023",
            "description": "Market session for Q1 of 2023",
            "status": "open",
            "start_date": "2023-01-01T00:00:00Z",
            "end_date": "2023-03-31T23:59:59Z",
            "created_at": "2022-12-15T10:00:00Z",
            "updated_at": "2022-12-20T15:30:00Z",
            "challenges": [
                {
                    "id": 101,
                    "name": "Challenge A",
                    "description": "Forecasting challenge A",
                    "start_date": "2023-01-01T00:00:00Z",
                    "end_date": "2023-01-31T23:59:59Z"
                },
                {
                    "id": 102,
                    "name": "Challenge B",
                    "description": "Forecasting challenge B",
                    "start_date": "2023-02-01T00:00:00Z",
                    "end_date": "2023-02-28T23:59:59Z"
                }
            ]
        },
        {
            "id": 2,
            "name": "Session Q2 2023",
            "description": "Market session for Q2 of 2023",
            "status": "open",
            "start_date": "2023-04-01T00:00:00Z",
            "end_date": "2023-06-30T23:59:59Z",
            "created_at": "2023-03-15T10:00:00Z",
            "updated_at": "2023-03-20T15:30:00Z",
            "challenges": []
        }
    ]
    ```
# Listing Challenges for Open Market Sessions

After retrieving the open market sessions, you may want to list the challenges associated with a specific open market session. Challenges are opportunities published by the Market Maker (Elia Group) that Forecasters can submit forecasts for.

!!! info "Prerequisites"
    - **Access Token**: Ensure you have a valid access token. Refer to the [Authentication](authentication.md) section if needed.
    - **Open Market Session ID**: You should have the ID of the open market session you're interested in. See [Listing Open Market Sessions](listing_open_market_sessions.md) to retrieve it.

## Retrieving Challenges for an Open Market Session

Here's how you can retrieve the list of registered challenges for a specific open market session using Python:

```python title="listing_challenges_for_open_session.py"
import requests

access_token = "your_access_token"
open_market_session_id = "your_open_market_session_id"

headers = {
    'Authorization': f'Bearer {access_token}',
    'Accept': 'application/json'
}

params = {
    'market_session': open_market_session_id
}

response = requests.get(
    url='https://predico-elia.inesctec.pt/api/v1/market/challenge',
    params=params,
    headers=headers
)

# Check if the request was successful
if response.status_code == 200:
    challenges = response.json()
    print("Challenges for Open Market Session:")
    for challenge in challenges:
        print(f"- Challenge ID: {challenge['id']}, Name: {challenge['name']}")
else:
    print(f"Failed to retrieve challenges. Status code: {response.status_code}")

```
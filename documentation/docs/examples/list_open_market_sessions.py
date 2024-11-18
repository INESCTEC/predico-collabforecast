import requests

access_token = "your_access_token_here"

headers = {
    'Authorization': f'Bearer {access_token}',
    'Accept': 'application/json'
}

response = requests.get(
    url='https://127.0.0.1/api/v1/market/session',
    params={"status": "open"},
    headers=headers
)

# Check if the request was successful
if response.status_code == 200:
    market_sessions = response.json()
    print(market_sessions)
else:
    print(f"Failed to retrieve market sessions.")
    print(f"Status code: {response.status_code}")
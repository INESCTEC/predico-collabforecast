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
    url='https://127.0.0.1/api/v1/market/challenge',
    params=params,
    headers=headers
)

# Check if the request was successful
if response.status_code == 200:
    challenges = response.json()
    print("Challenges for Open Market Session:")
    print(challenges)
else:
    print("Failed to retrieve challenges.")
    print(f"Status code: {response.status_code}")

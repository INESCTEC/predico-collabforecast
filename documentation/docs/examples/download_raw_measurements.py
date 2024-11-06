import requests

# Authenticate via `/token` endpoint
access_token = "your_access_token_here"
headers = {
    'Authorization': f'Bearer {access_token}',
    'Accept': 'application/json'
}

# Get the session id from `/market/session/` endpoint
open_market_session_id = "your_open_market_session_id"

# Request the challenges for the open market session:
response = requests.get(
    url='https://predico-elia.inesctec.pt/api/v1/market/challenge',
    params={'market_session': open_market_session_id},
    headers=headers
)

# Check if the request was successful
if response.status_code == 200:
    challenges = response.json()
else:
    print("Failed to retrieve challenges.")
    print(f"Status code: {response.status_code}")
    exit()

# Select the first challenge of the list of challenges previous retrieved
selected_challenge = challenges["data"][0]
resource_id = selected_challenge['resource']
print("Selected Challenge:")
print(f"Challenge ID: {selected_challenge['id']}")
print(f"Challenge Resource ID: {resource_id}")

# Get information on the data availability for this resource:
response = requests.get(
    url=f'https://predico-elia.inesctec.pt/api/v1/user/resource',
    params={"resource": resource_id},
    headers=headers
)
print("-"*79)
print("Resource Information:")
print(response.json()["data"])

# Download raw measurements data for this resource:
start_date = response.json()["data"][0]["measurements_metadata"]["start_datetime"]
end_date = response.json()["data"][0]["measurements_metadata"]["end_datetime"]
params = {
    "resource": resource_id,
    "start_date": start_date,
    "end_date": end_date
}
# Download data:
next_url = "https://predico-elia.inesctec.pt/api/v1/data/raw-measurements/"
dataset = []

# -- Note: This will stop once all the samples are retrieved.
# -- next_url indicates the URL of the next page (pagination) to be requested)

while next_url is not None:
    print(f"Requesting data...\n{next_url}") # This may take a while
    response = requests.get(url=next_url, params=params, headers=headers)
    dataset += response.json()["data"]["results"]
    next_url = response.json()["data"]["next"]
    # -- Note: This will stop once all the samples are retrieved.

print("-"*79)
print(f"Retrieved {len(dataset)} records")
print(f"Challenge observed data (first 10 records preview):")
print(dataset[:10])

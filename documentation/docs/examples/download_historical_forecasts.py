import requests

# Authenticate via `/token` endpoint
access_token = "your_access_token_here"
headers = {
    'Authorization': f'Bearer {access_token}',
    'Accept': 'application/json'
}

# Specify a resource ID (UUID) to download historical forecasts data
resource_id = "ba7203df-0618-4001-a2e9-b0a11cc477f9"

# Download historical forecasts data for this resource:
start_date = "2024-06-01T00:00:00Z"
end_date = "2025-06-01T00:00:00Z"
params = {
    "resource": resource_id,
    "start_date": start_date,
    "end_date": end_date
}
# Download data:
next_url = "https://127.0.0.1/api/v1/data/individual-forecasts/historical"
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
print(f"Historical forecasts (first 10 records preview):")
print(dataset[:10])

# Downloading Raw Data

After selecting a challenge, the next step is to download the raw observed data associated with the challenge's resource. Market Makers send time-series data periodically, which includes raw measurement data for their registered resources (e.g., wind farm #1).

!!! info "Note"
    - This step can be replicated for every challenge. In this example, we'll select the first challenge from the list.
    - The data is provided at a **15-minute resolution**, resulting in a large volume of samples. Therefore, **pagination** is required to retrieve all data properly.

!!! info "Prerequisites"

    - **Access Token**: Ensure you have a valid access token. Refer to the [Authentication](authentication.md) section if needed.
    - **Challenges List**: You should have a list of challenges retrieved. See [Listing Challenges for Open Sessions](listing_challenges_for_open_session.md) to obtain this list.

## Selecting a Challenge

First, select a challenge from the list of challenges you have retrieved:

```python title="select_challenge.py"
# Assume 'challenges' is a list of challenges obtained previously
selected_challenge = challenges[0]  # Selecting the first challenge
print("Selected Challenge:")
print(f"- Challenge ID: {selected_challenge['id']}, Name: {selected_challenge['name']}")
```

## Retrieving Raw Data for a Challenge

Here's how you can retrieve the raw data for a specific challenge using Python:

```python title="downloading_raw_data.py"
headers = {
    'Authorization': f'Bearer {access_token}',
    'Accept': 'application/json'
}

# Download raw measurements data for this resource:
resource_id = selected_challenge["resource"]
start_date = "2024-01-01T00:00:00Z"
end_date = "2025-01-01T00:00:00Z"
params = {
    "resource": resource_id,
    "start_date": start_date,
    "end_date": end_date
}
# Download data:
next_url = f"{predico_base_url}/data/raw-measurements/"
dataset = []

# -- Note: This will stop once all the samples are retrieved.
# -- next_url indicates the URL of the next page (pagination) to be requested)

while next_url is not None:
    response = requests.get(url=next_url, params=params, headers=headers)                            
    dataset += response.json()["data"]["results"]
    next_url = response.json()["data"]["next"]

dataset_df = pd.DataFrame(dataset)

print("-"*79)
print(f"Challenge observed data for resource {resource_id}")
dataset_df
```

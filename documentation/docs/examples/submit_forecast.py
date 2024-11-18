import json
import requests
import numpy as np
import pandas as pd

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
    url='https://127.0.0.1/api/v1/market/challenge',
    params={'market_session': int(open_market_session_id)},
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

# Unpack selected challenge information
resource_id = selected_challenge["resource"]
challenge_id = selected_challenge["id"]
start_datetime = selected_challenge["start_datetime"]
end_datetime = selected_challenge["end_datetime"]
print(f"""
Challenge info:
ID: {challenge_id}
Resource ID: {resource_id}
First forecast leadtime): {start_datetime}
Last forecast leadtime): {end_datetime}
""")

# Create a random 24h submission (random values):
# Generate datetime values for the challenge period:
datetime_range = pd.date_range(start=start_datetime,
                               end=end_datetime,
                               freq='15T')
datetime_range = [x.strftime("%Y-%m-%dT%H:%M:%SZ") for x in datetime_range]
# Generate random values for the "value" column
values = np.random.uniform(low=0.0, high=1.0, size=len(datetime_range))
values = [round(x, 3) for x in values]

# Reuse this data to prepare 3 different quantiles submissions Q10, Q50, Q90
submission_list = []
for qt in ["q10", "q50", "q90"]:
    qt_forec = pd.DataFrame({
    'datetime': datetime_range,
    'value': values,
    })
    submission_list.append({
        "variable": qt,
        "forecasts": qt_forec.to_dict(orient="records")
    })

# Your submissions:
print("Submission List:")
for i, submission in enumerate(submission_list):
    print("-"*79)
    print(f"Submission #{i+1}")
    print(json.dumps(submission, indent=3))

# Submit the forecasts:
for submission in submission_list:
    response = requests.post(url=f"https://127.0.0.1/api/v1/market/challenge/submission/{challenge_id}",
                            json=submission,
                            headers=headers)

    # Check if the request was successful
    if response.status_code == 201:
        print(f"Forecast submission successful for {submission['variable']} quantile.")
    else:
        print(f"Failed to submit forecast for {submission['variable']} quantile.")
        print(f"Status code: {response.status_code}")
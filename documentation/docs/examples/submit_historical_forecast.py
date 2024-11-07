import json
import requests
import numpy as np
import pandas as pd
import datetime as dt 

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

# Create 1month of historical data (sampled from uniform dist):
# Generate datetime values for the challenge period:
n_historical_days = 35

dt_now = pd.to_datetime(dt.datetime.utcnow()).round("15min")
hist_datetime_range = pd.date_range(start=dt_now - pd.DateOffset(days=n_historical_days),
                                    end=dt_now.replace(hour=23, minute=45, second=00),
                                    freq='15min')
hist_datetime_range = [x.strftime("%Y-%m-%dT%H:%M:%SZ") for x in hist_datetime_range]

# Generate random values for the "value" column
hist_values = np.random.uniform(low=0.0, high=1.0, size=len(hist_datetime_range))
hist_values = [round(x, 3) for x in hist_values]

# Prepare historical data for 3 different quantiles submissions Q10, Q50, Q90
hist_submission_list = []
for qt in ["q10", "q50", "q90"]:
    qt_forec = pd.DataFrame({
    'datetime': hist_datetime_range,
    'value': hist_values,
    })
    hist_submission_list.append({
        "resource": resource_id,
        "variable": qt,
        "launch_time": dt_now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "forecasts": qt_forec.to_dict(orient="records")
    })

# Submit historical forecasts:
for submission in hist_submission_list:
    response = requests.post(url=f"https://predico-elia.inesctec.pt/api/v1/data/individual-forecasts/historical",
                            json=submission,
                            headers=headers)

    # Check if the request was successful
    if response.status_code == 201:
        print(f"Forecast submission successful for {submission['variable']} quantile.")
    else:
        print(f"Failed to submit forecast for {submission['variable']} quantile.")
        print(f"Status code: {response.status_code}")
```python

```

<h1>Predico - Collaborative Forecasting Platform</h1>

<h3>Forecaster Jupyter NB</h3>

This notebook illustrates and provides Python code snippets allowing interaction between individual forecasters (aka Market participants) and Predico Platform. 

Below you can find examples for the following functionalities:

* Authentication
* Listing open sessions & challenges
* Downloading raw data for a resource (published by a market maker)
* Prepare and submit forecast for a challenge
* Preview submissions for a challenge
* Preview forecast skill scores for challenge submissions
* Preview forecast contributions (to the final ensemble models) for challenge submissions

----
## Important

### Application:
* Forecasters apply to participate by sending an email to predico@elia.be.
* Upon acceptance (by Elia Group), they receive a registration link to complete their registration. 

### Useful Links:

* MainPage: https://predico-elia.inesctec.pt/

### Contacts:
* Giovanni Buroni (giovanni.buroni@inesctec.pt)
* Carla Gonçalves (carla.s.goncalves@inesctec.pt)
* André Garcia (andre.f.garcia@inesctec.pt)
* José Andrade (jose.r.andrade@inesctec.pt)
* Ricardo Bessa (ricardo.j.bessa@inesctec.pt)

#### Last update:
2024-10-31, by José Andrade

### Install dependencies


```python
# Note: you just need to run this once - to configure your Python Interpreter:
!pip install requests pandas
```

### Imports / Helper functions


```python
# Imports
import os
import json
import getpass
import requests
import numpy as np
import pandas as pd
import datetime as dt

from pprint import pprint
```


```python
# Helper funcs:
def http_request(request_type, task_msg, verbose=1, **kwargs):
    print("-"*79)
    print(f"[{request_type}] {kwargs['url']} {task_msg} ...")
    if request_type == "GET":
        response = requests.get(**kwargs, verify="ca.crt")
        response_codes = [200]
    elif request_type == "POST":
        response = requests.post(**kwargs, verify="ca.crt")
        response_codes = [200, 201]
    elif request_type == "PUT":
        response = requests.put(**kwargs, verify="ca.crt")
        response_codes = [200, 201]
        
    if response.status_code in response_codes:
        print("Success! Response:")
        if verbose > 0:
            pprint(response.json())
        print(f"[GET] {task_msg} ... Ok!")
    else:
        print("Error! Response:")
        if verbose > 0:
            pprint(response.json())
        print(f"[GET] {task_msg} ... Failed!")
        
    return response

```

## Preparation Steps - Set Forecaster Credentials & API URL references


```python
# Settings:
predico_base_url = "https://predico-elia.inesctec.pt/api/v1"

# Credentials:
forecaster_email = input('Email:')
forecaster_pw = getpass.getpass('Password:')
```

***
***

## Step 1 - Login as Individual Forecaster


```python
# Auth request:
login_data = {"email": forecaster_email, 
              "password": forecaster_pw}
response = http_request(request_type="POST",
                        task_msg="Authenticating ...",
                        url=f"{predico_base_url}/token",
                        data=login_data)

# Save Token (to be reused in next interactions)
access_token = response.json().get('access', None)
if access_token is None:
    print("Error! Unable to retrieve access token. Do not forget to validate your account before this step!")
else:
    AUTH_TOKEN = f"Bearer {access_token}"
```

***
***

# Step 2 - Forecaster interactions w/ Predico


The basic Forecaster work flow is ilustrated in our [Quick Guide](https://predico-elia.inesctec.pt/quick-guide/):
    1. The forecaster lists open market sessions and challenges (created by the market maker)
    2. The forecaster selects a challenge and downloads raw data (to build a forecasting model)
    3. The forecaster prepares and submits its forecast

__Important__: 
***If the forecaster has never submitted a forecast, it is necessary to send at least 1month of historical forecasts data (e.g., which the forecaster used to initially evaluate the forecasting model performance). This is a requirement for the current version of the collaborative forecasting models which, if not fulfiled, will disable the submission of forecasts for a market session.***

### 2.1. List open market session
 
Market sessions are specific periods during which Market Makers can create forecasting challenges, and Forecasters can submit forecasts for the open challenges. These are managed (open/closed) by scheduled tasks (e.g., every day or hour).

**(see the official [documentation](https://predico-elia.inesctec.pt/redoc/#tag/market/operation/get_market_session) for this endpoint)**


```python
# Get currently open session
response = http_request(request_type='GET', 
                        task_msg="Listing registered sessions ...",
                        url=f"{predico_base_url}/market/session",
                        params={"status": "open"},
                        headers={"Authorization": AUTH_TOKEN})

if len(response.json()["data"]) > 0:
    open_market_session_id = response.json()["data"][0]["id"]
else:
    raise Exception("There are no open market sessions. Please open a session first.")

```

### 2.2 List collab forecasting challenges for open session

Market Challenges are opportunities, published by the Market Maker (Elia Group), with meta-data regarding a forecasting challenge that Forecasters can try to submit forecasts for.

**(see the official [documentation](https://predico-elia.inesctec.pt/redoc/#tag/market/operation/get_market_session_challenge) for this endpoint)**


```python
# Preview list of registered challenges for the currently open session id:
response = http_request(request_type='GET', 
                        task_msg=f"Listing registered challenges for session {open_market_session_id} ...",
                        url=f"{predico_base_url}/market/challenge",
                        params={"market_session": open_market_session_id},
                        headers={"Authorization": AUTH_TOKEN})

challenges = response.json()["data"]
```

### 2.3. Select a challenge and download raw observed data for the challenge resource

Market Makers send, periodically, time-series with raw measurement data for their registered resources in the platform (e.g., wind farm #1).

**(see the official [documentation](https://predico-elia.inesctec.pt/redoc/#tag/data/operation/get_raw_data) for this endpoint)**

**Note: This step can be replicated for every challenge, we'll just select the first one**

> __Important__: 15min resolution time-series are expected to be downloaded. Therefore pagination is required to enable proper access to the large volume of samples in historical data. Check the procedures below to know how to properly retrieve the datasets.


```python
# Select challenge:
selected_challenge = challenges[0]
print("Selected Challenge:")
pprint(selected_challenge)

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
    response = http_request(request_type='GET',
                            task_msg=f"Downloading challenge data for resource {resource_id} ...",
                            url=next_url,
                            params=params,
                            headers={"Authorization": AUTH_TOKEN},
                            verbose=0)
    dataset += response.json()["data"]["results"]
    next_url = response.json()["data"]["next"]

dataset_df = pd.DataFrame(dataset)

print("-"*79)
print(f"Challenge observed data for resource {resource_id}")
dataset_df
```

### 2.4. Forecaster prepares forecast

**Note: In this example we just prepare a 24h submission (15 minute random samples) but it should include the preparation of a forecasting model (e.g., using the dataset retrieved in the previous step combined with any other variables the Forecaster might have access to)**


```python
# Unpack selected challenge information
resource_id = selected_challenge["resource"]
challenge_id = selected_challenge["id"]
start_datetime = selected_challenge["start_datetime"]
end_datetime = selected_challenge["end_datetime"]

print(f"""
Challenge ID: {challenge_id}
Resource ID: {resource_id}
Start DT: {start_datetime}
End DT: {end_datetime}
""")

# Create a random 24h submission:
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
```

### 2.5. Forecaster submits forecast

Forecasters can submit forecasts for open Market Challenges, competing for the prize money available. They may commence or stop contributing to the market at any time.

**(see the official [documentation](https://predico-elia.inesctec.pt/redoc/#tag/market/operation/post_market_session_submission) for this endpoint)**

> __Important__: Before forecasters make their first submission, they must fulfil at least 1 month of historical forecast samples submitted to the Predico platform (current requirement). See the step 2.5.1 to find how to do this.


```python
# Unpack selected challenge information
for submission in submission_list:
    response = http_request(request_type='POST',
                            task_msg=f"Submiting forecast for challenge '{challenge_id}' resource '{resource_id}' -- variable '{submission['variable']}' ...",
                            url=f"{predico_base_url}/market/challenge/submission/{challenge_id}",
                            json=submission,
                            headers={"Authorization": AUTH_TOKEN})
```

#### 2.5.1 (first forecast only)

To assess their potential and define the ensemble methodology, a forecaster must submit a historical of time-series forecasts, with 15-minute time resolution, for a minimum of 30 days before the challenge start date (1st period to forecast). The forecaster should be careful with this step, as providing unrealistic historical forecasts (e.g., overfitting to historical data) might compromise its submission. The forecaster does not stand to gain more money by submitting a better historical forecast, as payment is based on ex-post performance calculations.

 * ***This step is mandatory for the first time a forecaster participates in a collaborative forecasting session and will be optional for the remaining (unless a gap of 30 days passes between participation in challenges).***

**(see the official [documentation](https://predico-elia.inesctec.pt/redoc/#tag/data/operation/post_individual_forecasts_historical) for this endpoint)**

> __Note__: The forecasts used to train the ensemble models will be a combination of historical forecasts provided by the Forecaster and forecasts submitted to actual challenges. **The former can be revised (using the same HTTP POST endpoint) until the Forecaster makes their first submission on the platform, the latter cannot be changed once the market session executes.**

> __Important__: It is recommended to avoid the transfer of high volume of samples, in a single request. Otherwise, your request might fail.



```python
# Unpack selected challenge information
resource_id = selected_challenge["resource"]

# Create 1month of historical data (sampled from uniform dist):
# Generate datetime values for the challenge period:
N_HISTORICAL_DAYS = 35

dt_now = pd.to_datetime(dt.datetime.utcnow()).round("15min")
hist_datetime_range = pd.date_range(start=dt_now - pd.DateOffset(days=N_HISTORICAL_DAYS), 
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

# Submit forecast
for submission in hist_submission_list:
    response = http_request(request_type='POST',
                            task_msg=f"Submiting forecast for challenge '{challenge_id}' resource '{resource_id}' ...",
                            url=f"{predico_base_url}/data/individual-forecasts/historical",
                            json=submission,
                            headers={"Authorization": AUTH_TOKEN})

```

### 2.6. Forecaster previews submitted forecast

Forecasters can preview their challenge submissions (list) at any point in time.

**(see the official [documentation](https://predico-elia.inesctec.pt/redoc/#tag/market/operation/get_market_session_submission) for this endpoint)**


```python
# Preview my submissions
response = http_request(request_type='GET',
                        task_msg=f"Retrieving submissions for challenge '{challenge_id}' resource '{resource_id}' ...",
                        url=f"{predico_base_url}/market/challenge/submission",
                        params={"challenge": challenge_id},
                        headers={"Authorization": AUTH_TOKEN}, 
                        verbose=0)

pd.DataFrame(response.json()["data"])
```

### 2.7. Forecaster downloads submitted forecasts

Forecasters can also preview their submitted forecast time-series.

**(see the official [documentation](https://predico-elia.inesctec.pt/redoc/#tag/market/operation/get_market_session_submission_forecasts) for this endpoint)**



```python
# Preview my submitted forecasts
response = http_request(request_type='GET',
                        task_msg=f"Retrieving submissions for challenge '{challenge_id}' resource '{resource_id}' ...",
                        url=f"{predico_base_url}/market/challenge/submission/forecasts",
                        params={"challenge": challenge_id},
                        headers={"Authorization": AUTH_TOKEN}, 
                        verbose=0)

pd.DataFrame(response.json()["data"])
```

### 2.8. Forecaster previews forecast skill scores

Every day, a scheduled task calculates the submitted forecasts skill score (error metrics) and relative rank to the remaining forecasters participating in the platform. This information can also be retrieved with a request to the service API.

**(see the official [documentation](https://predico-elia.inesctec.pt/redoc/#tag/market/operation/get_market_session_submission_scores) for this endpoint)**



```python
# Preview my skill scores
response = http_request(request_type='GET',
                        task_msg=f"Retrieving submissions scores for challenge '{challenge_id}' resource '{resource_id}' ...",
                        url=f"{predico_base_url}/market/challenge/submission-scores",
                        params={"challenge": challenge_id},
                        headers={"Authorization": AUTH_TOKEN}, 
                        verbose=1)
```

### 2.9. Forecaster previews forecasts contributions

Every day, a scheduled task calculates the submitted forecasts contribution to the final ensemble and relative rank to the remaining forecasters participating in the platform. This information can also be retrieved with a request to the service API.

**(see the official [documentation](https://predico-elia.inesctec.pt/redoc/#tag/market/operation/get_market_session_ensemble_weights) for this endpoint)**



```python
# Preview my forecast contributions
response = http_request(request_type='GET',
                        task_msg=f"Retrieving submissions contributions for challenge '{challenge_id}' resource '{resource_id}' ...",
                        url=f"{predico_base_url}/market/challenge/ensemble-weights",
                        params={"challenge": challenge_id},
                        headers={"Authorization": AUTH_TOKEN}, 
                        verbose=1)
```

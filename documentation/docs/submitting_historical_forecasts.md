# Submitting Historical Forecasts

Forecasters must submit historical forecast samples to the Predico platform before making their first forecast submission. This step is mandatory to assess the forecaster's potential and define the ensemble methodology. In this example, we'll demonstrate how to prepare and submit **1 month** of historical forecast data with a **15-minute** time resolution. Replace the random data generation with your actual forecasting model as needed.

!!! info "Prerequisites"
    - **Access Token**: Ensure you have a valid access token. Refer to the [Authentication](authentication.md) section if needed.
    - **Selected Challenge**: You should have a selected challenge from the [Listing Challenges for Open Sessions](listing_challenges_for_open_session.md) section.
    - **Prepared Historical Forecast Data**: Follow the steps outlined below to prepare your historical forecasts.

## Overview

Submitting historical forecasts is essential for new forecasters to participate in a collaborative forecasting session. 
This process involves generating or preparing a dataset of historical forecasts and submitting them to the Predico API. Proper handling of this data ensures the integrity and reliability of your submissions.

## Unpacking Selected Challenge Information

Before submitting your forecast, extract essential information from the selected challenge:

```python title="select_challenge.py"
# Unpack selected challenge information
resource_id = selected_challenge["resource"]
challenge_id = selected_challenge["id"]
```

## Preparing Historical Forecast Data

Prepare the historical forecast data for submission. In this example, we'll generate random data for 
the historical forecasts:

```python title="prepare_historical_forecast.py"

headers = {
    'Accept': 'application/json',
    'Authorization': f'Bearer {access_token}'
}
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
```

## Submitting Historical Forecast Data

After preparing your historical forecast data, submit it to the Predico platform:

```python title="submit_historical_forecast.py"
for submission in hist_submission_list:
    response = requests.post(url=f"https://predico-elia.inesctec.pt/data/individual-forecasts/historical",
                            json=submission,
                            headers=headers)

    # Check if the request was successful

    if response.status_code == 201:
        print(f"Forecast submission successful for {submission['variable']} quantile.")
    else:
        print(f"Failed to submit forecast for {submission['variable']} quantile. Status code: {response.status_code}")

``` 



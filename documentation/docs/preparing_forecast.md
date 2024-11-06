# Preparing a Forecast

After downloading the raw measurements data, the next step for Forecasters is to prepare their forecasts. This involves creating forecast submissions based on the retrieved data and any additional variables or models the Forecaster might utilize. In this example, we'll demonstrate how to prepare a simple 24-hour submission using randomly generated data. In a real-world scenario, you would replace this with your forecasting model based on the dataset retrieved in the previous step.

!!! info "Note"
    - **Example Purpose**: This example demonstrates preparing a 24-hour forecast submission with 15-minute interval samples using random data. Replace this with your forecasting model for actual use.
    - **Quantiles**: The forecast includes three quantiles: Q10, Q50, and Q90, representing the 10th, 50th, and 90th percentiles, respectively.

!!! info "Prerequisites"

    - **Python Environment**: Ensure you have Python installed with the necessary libraries (`pandas`, `numpy`, `requests`).
    - **Access Token**: A valid access token is required for authentication. Refer to the [Authentication](authentication.md) section if needed.
    - **Challenges List**: A list of challenges retrieved from the [Listing Challenges for Open Sessions](listing_challenges_for_open_session.md) section.

## Selecting a Challenge

First, select a challenge from the list of challenges you have retrieved:

```python title="select_challenge.py"
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
```

## Preparing Forecast Data

Next, prepare the forecast data for submission. In this example, we'll generate random data for the forecast:

```python title="prepare_forecast.py"
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

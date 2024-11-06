# Submitting a Forecast

Forecasters can submit forecasts for open Market Challenges, competing for the prize money available. They may commence or stop contributing to the market at any time.

!!! warning "Important"
    - **First-Time Submission Requirement**: Before making your first submission, you must fulfill at least **1 month of historical forecast samples** submitted to the Predico platform. Refer to [Historical Forecast Submission](submitting_historical_forecasts.md) below for detailed instructions.
    - **Forecast Integrity**: Ensure that your historical forecasts are realistic. Providing unrealistic historical forecasts (e.g., overfitting to historical data) may compromise your submission. Remember, payment is based on ex-post performance calculations, not on the quality of historical forecasts.
    - **Submission Volume**: Avoid transferring a high volume of samples in a single request to prevent potential request failures. It's recommended to batch your submissions appropriately.

!!! info "Prerequisites"

    - **Access Token**: Ensure you have a valid access token. Refer to the [Authentication](authentication.md) section if needed.
    - **Selected Challenge**: You should have a selected challenge from the [Listing Challenges for Open Sessions](listing_challenges_for_open_session.md) section.
    - **Prepared Forecast Data**: Follow the [Preparing a Forecast](preparing_forecast.md) section to prepare your forecast submissions.

## Unpacking Selected Challenge Information

Before submitting your forecast, extract essential information from the selected challenge:

```python title="select_challenge.py"
# Unpack selected challenge information
challenge_id = selected_challenge["id"]
```

## Submitting Forecast Data

After preparing your forecast data, submit it to the Predico platform. In this example, we'll submit the random data
generated in [Preparing a Forecast](preparing_forecast.md) section to submit forecasts for the selected challenge: 

```python title="submit_forecast.py"
# Submit the forecast data

headers = {
    'Accept': 'application/json',
    'Authorization': f'Bearer {access_token}'
}

for submission in submission_list:
    response = requests.post(url=f"https://predico-elia.inesctec.pt/api/v1/market/challenge/submission/{challenge_id}",
                            json=submission,
                            headers=headers)

    # Check if the request was successful
    if response.status_code == 201:
        print(f"Forecast submission successful for {submission['variable']} quantile.")
    else:
        print(f"Failed to submit forecast for {submission['variable']} quantile. Status code: {response.status_code}")
```


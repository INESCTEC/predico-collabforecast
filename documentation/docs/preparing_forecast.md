# Preparing a Forecast

After downloading the raw measurements data, the next step for Forecasters is to prepare their forecasts. 
This involves creating forecast submissions based on the retrieved data and any additional variables or models the Forecaster might utilize. 
In this example, we'll demonstrate how to prepare a simple 24-hour submission using randomly generated data. 
In a real-world scenario, you would replace this with your forecasting model based on the dataset retrieved in the previous step.

!!! info "Note"
    - **Example Purpose**: This example demonstrates preparing a 24-hour forecast submission with 15-minute interval samples using random data. Replace this with your forecasting model for actual use.
    - **Quantiles**: The example submission includes values for three variables, specifically 'quantiles' 10, 50, and 90.

!!! info "Prerequisites"

    - **Python Environment**: Ensure you have Python installed with the necessary libraries (`pandas`, `numpy`, `requests`).
    - **Access Token**: A valid access token is required for authentication. Refer to the [Authentication](authentication.md) section if needed.
    - **Challenges List**: A list of challenges retrieved from the [Listing Challenges](listing_challenges.md) section.

## Selecting a Challenge

First, select a challenge from the list of challenges you have retrieved:

```python title="submit_forecast.py"
--8<-- "docs/examples/submit_forecast.py:31:38"
```

## Preparing Forecast Submissions Time-series Data

Next, prepare the forecast data for submission. 

!!! important "Important"

    In this example, our submission will be exclusively composed by random samples.
    However, you should prepare your model based on the raw measurements data for the challenge `resource` (see 
    [Downloading Raw Data](downloading_raw_data.md) section), and any external information sources you might have access to.

!!! info "One variable at each time"
    
    You can only submit one forecast variable in each HTTPs request (e.g., forecasts for quantile 10 in the first request and quantile 50 in the second request).
    

```python title="submit_forecast.py"
--8<-- "docs/examples/submit_forecast.py:46:75"
```

<a href="../examples/submit_forecast.py" download="submit_forecast.py"><b>Download Full Example</b></a>


## What's next?

Learn how to submit your forecasts on the Predico platform in the [Submitting a Forecast](submitting_forecast.md) section.

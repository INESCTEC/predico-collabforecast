# Submitting Historical Forecasts

Forecasters must submit historical forecast samples to the Predico platform before making their first forecast submission. This step is mandatory to assess the forecaster's potential and define the ensemble methodology. In this example, we'll demonstrate how to prepare and submit **1 month** of historical forecast data with a **15-minute** time resolution. Replace the random data generation with your actual forecasting model as needed.

!!! info "Prerequisites"
    - **Access Token**: Ensure you have a valid access token. Refer to the [Authentication](authentication.md) section if needed.
    - **Selected Challenge**: You should have a selected challenge from the [Listing Challenges](listing_challenges.md) section.
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

Prepare the historical forecast data for submission. 

!!! important "Important"

    In this example, our submission will be exclusively composed by random samples.
    However, you should prepare your model based on the raw measurements data for the challenge `resource` (see 
    [Downloading Raw Data](downloading_raw_data.md) section), and any external information sources you might have access to.


```python title="submit_historical_forecast.py"
--8<-- "docs/examples/submit_historical_forecast.py:47:74"
```


## Submitting Historical Forecast Data

After preparing your historical forecast data, submit it to the Predico platform:

!!! warning "Important"
    - **Forecast Integrity**: Ensure that your historical forecasts are realistic (i.e., for an out-of-sample set). Providing unrealistic historical forecasts (e.g., overfitting to historical data) may compromise your submission. Remember, payment is based on ex-post performance calculations and not on the quality of this initial historical forecasts.
    - **Submission Volume**: Avoid transferring a high volume of samples in a single request to prevent potential request failures. It's recommended to batch your submissions appropriately.


```python title="submit_historical_forecast.py"
--8<-- "docs/examples/submit_historical_forecast.py:75:87"
```

<a href="../examples/submit_historical_forecast.py" download="submit_historical_forecast.py"><b>Download Full Example</b></a>

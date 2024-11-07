# Submitting Historical Forecasts

Forecasters must submit historical forecast samples to the Predico platform before making their first forecast submission. This step is mandatory to assess the forecaster's potential and define the ensemble methodology. In this example, we'll demonstrate how to prepare and submit **1 month** of historical forecast data with a **15-minute** time resolution. Replace the random data generation with your actual forecasting model as needed.


## API Endpoints:

To interact with the Predicto API and submit  
your historical forecasts,
you can use the following endpoints:

- **GET** [`/api/v1/market/session`](https://predico-elia.inesctec.pt/redoc/#tag/market/operation/get_market_session) - Retrieve list of market sessions (you can filter by 'open' sessions with query parameters)
- **GET** [`/api/v1/market/challenge`](https://predico-elia.inesctec.pt/redoc/#tag/market/operation/get_market_session_challenge) - Retrieve challenges for an open market session.
- **POST** [`/api/v1/data/individual-forecasts/historical`](https://predico-elia.inesctec.pt/redoc/#tag/data/operation/post_individual_forecasts_historical) - Publish your forecast submission for a specific challenge.


!!! info "Prerequisites"

    - **Access Token**: Ensure you have a valid access token. Refer to the [Authentication](authentication.md) section if needed.
    - **Selected Challenge**: You should have a selected challenge from the [Listing Challenges](listing_challenges.md) section.
    - **Prepared Historical Forecast Data**: Follow the steps outlined below to prepare your historical forecasts.


!!! tip "Check this out"
    Check our [Useful Links](useful_links.md) section for additional resources (Jupyter Notebook, API Specifications) to help you get started with the Predico platform.


## Overview

Submitting historical forecasts is essential for new forecasters to participate in a collaborative forecasting session. 
This process involves generating or preparing a dataset of historical forecasts and submitting them to the Predico API. Proper handling of this data ensures the integrity and reliability of your submissions.

## Unpacking Selected Challenge Information

Before submitting your forecast, extract essential information from the selected challenge:

```python title="submit_historical_forecast.py"
--8<-- "docs/examples/submit_historical_forecast.py:13:38"
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


## What's next?

Learn how to download your historical forecasts on the [Listing Historical Forecasts](listing_historical_forecasts.md) section.

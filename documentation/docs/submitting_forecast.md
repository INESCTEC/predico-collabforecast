# Submitting a Forecast

Forecasters can submit forecasts for open Market Challenges, competing for the prize money available. They may commence or stop contributing to the market at any time.


## API Endpoints:

To interact with the Predicto API and submit  
your forecasts for open challenges,
you can use the following endpoints:

- **GET** [`/api/v1/market/session`](https://predico-elia.inesctec.pt/redoc/#tag/market/operation/get_market_session) - Retrieve list of market sessions (you can filter by 'open' sessions with query parameters)
- **GET** [`/api/v1/market/challenge`](https://predico-elia.inesctec.pt/redoc/#tag/market/operation/get_market_session_challenge) - Retrieve challenges for an open market session.
- **POST** [`/api/v1/market/challenge/submission/{challenge_id}`](https://predico-elia.inesctec.pt/redoc/#tag/market/operation/post_market_session_submission) - Publish your forecast submission for a specific challenge.


!!! info "Prerequisites"

    - **Access Token**: Ensure you have a valid access token. Refer to the [Authentication](authentication.md) section if needed.
    - **Selected Challenge**: You should have a selected challenge from the [Listing Challenges](listing_challenges.md) section.
    - **Prepared Forecast Data**: Follow the [Preparing a Forecast](preparing_forecast.md) section to prepare your forecast submissions.


!!! tip "Check this out"
    Check our [Useful Links](useful_links.md) section for additional resources (Jupyter Notebook, API Specifications) to help you get started with the Predico platform.


## Submitting Forecast Data

After preparing your submissions, submit it to the Predico platform. 

In this example, we'll submit the random data generated in [Preparing a Forecast](preparing_forecast.md) section: 

!!! warning "Important"
    - **First-Time Submission Requirement**: Before making your first submission, you must fulfill at least **1 month of historical forecast samples** submitted to the Predico platform. Refer to [Historical Forecast Submission](submitting_historical_forecasts.md) for detailed instructions.

```python title="submit_forecast.py"
--8<-- "docs/examples/submit_forecast.py:76:87"
```

<a href="../examples/submit_forecast.py" download="submit_forecast.py"><b>Download Full Example</b></a>


## What's next?

Learn how to list your submissions on the Predico platform in the [Listing Submissions](listing_submissions.md) section.

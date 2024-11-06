# Submitting a Forecast

Forecasters can submit forecasts for open Market Challenges, competing for the prize money available. They may commence or stop contributing to the market at any time.

!!! info "Prerequisites"

    - **Access Token**: Ensure you have a valid access token. Refer to the [Authentication](authentication.md) section if needed.
    - **Selected Challenge**: You should have a selected challenge from the [Listing Challenges for Open Sessions](listing_challenges_for_open_session.md) section.
    - **Prepared Forecast Data**: Follow the [Preparing a Forecast](preparing_forecast.md) section to prepare your forecast submissions.


## Submitting Forecast Data

After preparing your submissions, submit it to the Predico platform. 

In this example, we'll submit the random data generated in [Preparing a Forecast](preparing_forecast.md) section: 

!!! warning "Important"
    - **First-Time Submission Requirement**: Before making your first submission, you must fulfill at least **1 month of historical forecast samples** submitted to the Predico platform. Refer to [Historical Forecast Submission](submitting_historical_forecasts.md) for detailed instructions.

```python title="submit_forecast.py"
--8<-- "docs/examples/submit_forecast.py:76:87"
```

<a href="../examples/submit_forecast.py" download="submit_forecast.py"><b>Download Full Example</b></a>

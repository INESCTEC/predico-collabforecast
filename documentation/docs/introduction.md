# Predico - Collaborative Forecasting Platform

## Overview 
Welcome to Predico, a Collaborative Forecasting Platform initiative designed to enhance forecasting accuracy through collaboration between market makers and forecasters.

This documentation is designed to help forecasters to **learn** more about the platform and **interact** with it, effectively.

!!! warning "Important"
    This platform is a proof of concept, so there might be changes to improve the outcomes for all parties.


## Documentation Outline

This platform consists exclusively of an API server, with no front-end available. 
Therefore, every interaction is done via HTTPs requests.

The following sections are designed to be followed sequentially to ensure a smooth interaction with the Predico API Platform.

1. [Authentication](authentication.md): Learn how to authenticate with the Predico API Platform.
2. [Listing Open Sessions](listing_open_sessions.md): Retrieve details on the open market sessions.
3. [Listing Challenges](listing_challenges.md): Retrieve details on the challenges published by the market maker, during open market sessions.
4. [Downloading Raw Data](downloading_raw_data.md): Download raw measurements data for a specific challenge.
5. [Preparing a Forecast](preparing_forecast.md): Prepare a forecast submission based on the retrieved data.
6. [Submitting a Forecast](submitting_forecast.md): Submit the forecast to the Predico API Platform.
7. [Submitting Historical Forecasts](submitting_historical_forecasts.md): Submit historical forecast samples to the Predico API Platform.
8. [Listing Submissions](listing_submissions.md): Retrieve a list of forecasts submitted by the forecaster.
9. [Listing Submission Scores](listing_submission_scores.md): Retrieve the forecast skill scores for your submissions.
10. [Listing Submission Contribution](listing_submission_contribution.md): Retrieve the forecast contribution for your submissions (to the final ensemble forecasts).

!!! important "Important"
    While the provided code examples are demonstrated in [**Python**](https://www.python.org/), the fundamental logic and sequential 
    processes are universally applicable. Forecasters are encouraged to develop their own clients 
    using any programming language of their choice, adapting the concepts and workflows presented here 
    to suit their preferred development environment.

# Introduction

The information below helps forecasters to understand critical definitions (vocabulary) and the general workflow of our collaborative forecasting platform.

!!! tip "Check this out"
    Check our [Useful Links](useful_links.md) section for additional resources (Jupyter Notebook, API Specifications) to help you get started with the Predico platform.


## Definitions
    
- **Market Maker**: An entity that owns resources (e.g., wind farms) or manages a grid (e.g., a TSO) and seeks forecasts by opening and funding collaborative forecasting market sessions.
- **Forecaster**: An individual or organization registered in the platform, aiming to submit forecasts to collaborative forecasting challenges opened by the Market Maker, competing for the available prize money in each session.
- **Market Session**: A specific period during which Market Makers can create forecasting challenges, and Forecasters can submit forecasts for the open challenges.
- **Market Challenge**: An opportunity, published by the Market Maker, with meta-data regarding a forecasting challenge that Forecasters can try to submit forecasts for.
- **Gate Closure Time**: The deadline by which forecasts must be submitted for a market session.
- **Forecast Variables**: Quantities to be forecasted. Currently only quantile 10, 50, 90 forecasts are accepted.
- **Ensemble Forecast**: An aggregate forecast computed from multiple forecasters’ submissions.


## Collaborative Forecasting Sessions

Below, you can find a sequence diagram illustrating the dynamics of a collaborative forecasting session, which is generally organized in four separate phases.

- **Phase 1**: A new market session is scheduled to open.
- **Phase 2**: Market Makers post new challenges, such as submitting day-ahead forecasts for specific assets (aka resources) in their portfolio.
- **Phase 3**: Forecasters log into Predico API, download raw measurements data, build their models, and submit forecasts.
- **Phase 4**: Forecasters log into Predico API, preview their skill scores and contribution importance to the final ensemble forecasts, to be delivered to the Market Maker.

!!! tip "Check this out"
    See the **<a href="../static/predico-interactions-sd.png" target="_blank">service sequence diagram</a>** for a visual representation of the collaborative forecasting session.


## Forecasting Components Breakdown

The Predico platform's forecasting process is structured into various modules, as illustrated in the diagram below. This breakdown highlights the main stages of wind power and wind power variability forecasting, and how the contributions from different forecasters are evaluated.

- **Data Value Assessment**: Using methods such as Permutation Importance and Shapley Values, this component assesses the value of data inputs, helping identify the most influential variables in forecasting accuracy.
- **Forecasting**: This is divided into two parallel processes:
    * ***Wind Power***: Forecasts are generated through a series of steps including feature engineering, hyperparameter optimization, model training, and the final forecast generation.
    * ***Wind Power Variability***: A similar process is followed here, focusing on capturing fluctuations in wind power output, which includes feature engineering, hyperparameter optimization, model training, and forecast generation.
- **Wind Ramp Detection**: Identifies sudden changes or "ramps" in wind power, which are crucial for managing grid stability and operational decisions.
- **Forecast Skill Evaluation**: This stage evaluates the performance of forecasters using metrics like Root Mean Squared Error (RMSE) and Pinball Loss. These scores help rank forecasters based on their forecast skill, per challenge participation.


!!! tip "Check this out"
    The interaction of these components with market makers and forecasters is shown in the **<a href="../static/modules-breakdown.png" target="_blank">forecasting components diagram</a>**.


## Timezone and Time Resolution

The Predico platform operates in the Central European Time (CET). Forecasters should be aware of the following requirements:

- **Timezone**: All times mentioned in the platform are in UTC.
- **Challenges Forecast Horizon**: Challenges are typically day-ahead, covering the 24-hour period. 
The start/end datetimes of the forecast are defined according to target country timezone (in this case, Belgium, CET). 

Therefore forecasted values for a specific day should cover:

- **Period from 22:00 to 21:45 UTC** (DST Time / Summer Time)
- **Period from 23:00 to 22:45 UTC** (Standard Time / Winter Time)

!!! info "Daylight Saving Time (DST)"
    - The platform adjusts for DST changes in March and October. On these days, the number of forecasted values per day will be 92 and 100, respectively.
    - Every forecasting challenge has information on the expected forecast leadtimes (start/end datetimes) to help forecasters prepare their submissions accordingly.

## Forecast Submissions

Forecasters can submit forecasts for open Market Challenges, competing for the prize money available. They may commence or stop contributing to the market at any time.

It is important that forecasters understand the following rules and guidelines when submitting forecasts:

- **Submission Timing**: Forecasts must be submitted before the gate closure time (11:00 CET) for that market session. Late submissions will not be considered.
- **Submission Period**: Market sessions are open from 10:00 to 11:00 CET daily.
- **Submission Method**: Forecasts are submitted to the platform's API via HTTPs requests. There is no front-end provided.
- **Latest Forecast Considered**: Only the latest forecast from a forecaster in a market session will be considered.
- **Unique Submissions**: A forecaster may not submit multiple forecasts for the same variable (e.g., two quantile 50 submissions) under the same or different forecaster IDs for the same challenge. A Forecaster can update their original submissions using a specific API endpoint. The latest valid submissions (before Gate Closure Time) will be considered.
- **Forecast Coverage**: Forecasts must cover the entire period mentioned in the challenge (start and end date). Given the fixed 15-minute time resolution for the submissions, Forecasters, should submit up to 96 forecasted quantities per variable (i.e., quantiles 10, 50, 90) per challenge, except for DST change days where these quantities might vary.
- **Time Resolution Compliance**: Forecasts must match the time resolution specified in the challenge.
- **Forecast Data Format**: Forecasts must be submitted in a specific format, as detailed in the [Preparing a Forecast](preparing_forecast.md) section.


## Evaluation and Scoring

The Predico platform evaluates the submitted forecasts based on both forecast skill and forecast contribution (i.e., to the final ensemble).

## What's next?

Proceed to the [Getting Started](getting_started.md) section to learn how to participate in the Predico collaborative forecasting sessions.

# Predico Collabforecast - Collaborative Forecasting Engine

-----------------------------------------------------

## Introduction

The Predico platform's forecasting process is structured into various modules, as illustrated in the diagram below. This breakdown highlights the main stages of wind power and wind power variability forecasting, and how the contributions from different forecasters are evaluated.

- **Data Value Assessment**: Using methods such as Permutation Importance and Shapley Values, this component assesses the value of data inputs, helping identify the most influential variables in forecasting accuracy.
- **Forecasting**: This is divided into two parallel processes:
    * ***Wind Power***: Forecasts are generated through a series of steps including feature engineering, hyperparameter optimization, model training, and the final forecast generation.
    * ***Wind Power Variability***: A similar process is followed here, focusing on capturing fluctuations in wind power output, which includes feature engineering, hyperparameter optimization, model training, and forecast generation.
- **Wind Ramp Detection**: Identifies sudden changes or "ramps" in wind power, which are crucial for managing grid stability and operational decisions.
- **Forecast Skill Evaluation**: This stage evaluates the performance of forecasters using metrics like Root Mean Squared Error (RMSE) and Pinball Loss. These scores help rank forecasters based on their forecast skill, per challenge participation.

**The interaction of these components with market makers and forecasters is shown in the **<a href="/documentation/docs/static/modules-breakdown.png" target="_blank">forecasting components diagram</a>**.**

## Module Structure:

The following directory structure should be considered:

``` bash
.   # Current directory
├── conf  # project settings
├── examples  # example scripts - includes simulation decoupled from remaining software stack
├── files  # log files, models, and other files
├── src  # project source codes
├── tasks.py  # CLI interface for running the forecasting modules in production
```

## Run forecasting engine decoupled from remaining services

It is possible to execute the collaborative forecasting engine in standalone mode, without the need for a REST-API or database integration.
That is useful for testing and debugging the forecasting engine in isolation.

Please check the `examples` directory, which includes a script for running the market pipeline in standalone mode.

### Requirements

* [Python ^3.11](https://www.python.org/downloads/)
* [Pip ^21.x](https://pypi.org/project/pip/)
* [Poetry ^1.8.x](https://python-poetry.org/)

###  Prepare Python environment:

### Initial setup:

> **_NOTE:_**  The commands below assume that you are running them from the root directory of the project module `forecast`

### Prepare python environment:

#### 1. Install poetry (if not already installed)

```shell
pip install poetry   
```
   
#### 2. Install the python dependencies and activate the virtual environment:

```shell
poetry install
poetry shell
```
   
> **_NOTE:_** If you're already working in a virtual environment (e.g., conda or pyenv), you can skip the `poetry shell` command. 

### The Simulator:

Our offline simulator is available on the `examples/offline_simulator` directory.
This simulator allows an execution of our collaborative forecasting pipeline on your own data.

After executing the simulator, reports will be created (i.e., in the `files/`directory) with forecasts and key KPIs from the service.

#### Offline Simulator Structure:

The following directory structure should be considered:

``` bash
.   # `offline_simulator` directory
├── main.py  # main script to execute simulations
├── simulation  # simulation helper classes
|──── SimulationManager.py  # configs / reports manager
|──── AgentsLoader.py  # loads agents information
|──── SessionGenerator.py  # creates market sessions
├── files  # I/O files
|──── datasets # directory for custom datasets
|──── reports  # directory for market runs reports (created on execution)

```

## Running the simulation

#### Inputs (Using your own datasets):

To use your own datasets, simply add them to `files/datasets/<dataset_name>` directory. 
A simulation will only be successfully executed when you have the following information:

1. `files/<dataset_name>/measurements.csv`: 
    * **Description**: Market Maker (aka Buyer) measurements data to be used during market sessions to evaluate the quality of Forecasters (aka Sellers) submissions.
    * **Structure**: Dataset disposed in tabular form with 1 column per Market Maker resource and a `datetime` column for the timestamp references (in UTC).
    * **Accepted Formats**: CSV only
2. `files/<dataset_name>/features.csv`: 
    * **Description**: Power forecasts submitted by individual Forecasters to participate in each market session challenge.
    * **Structure**: Dataset, disposed in tabular form with 1 column per user `resource`, forecast `variable` (i.e., quantile 10, 50 or 90) and a `datetime` column for the timestamp references (in UTC).
    * **Accepted Formats**: CSV only
3. `files/<dataset_name>/buyers_resources.json`: 
    * **Description**: Mapping between each Market Maker user identifier its resources. Also used to set the prefered timezone and forecast use_case (`wind_power`, `wind_power_variability`) when forecasting each specific resource.
    * **Structure**:
      * `user`: Market Maker identifier
      * `id`: Market Maker resource identifier
      * `timezone`: Market Maker timezone (see https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)
      * `use_case`: Market Maker use_case (`wind_power` or `wind_power_variability`)
    * **Accepted Formats**: JSON only
4. `files/<dataset_name>/sellers_resources.json`: 
    * **Description**: Mapping between each Forecaster user identifier and its forecasts for specific Market Maker resources.
    * **Structure**:
      * `user`: Forecaster identifier
      * `variable`: Forecast variable (i.e., quantile 'q10', 'q50' or 'q90')
      * `market_session_challenge_resource_id`: Resource identifier for the Market Maker challenge (should have a correspondence on the `buyers_resources.json` file)
    * **Accepted Formats**: JSON only

Please analyze the `files/datasets/example_elia_opendata` directory for an example of how to structure your dataset.
This example uses publicly available data from the Elia Open Data platform (https://opendata.elia.be/).

### Offline Simulator Configs:

The main script of this simulator (`main.py`) requires some initial configurations that can be adjusted according to the end-user needs:

These are:
  * `dataset_path`: Path to the dataset to be used in the simulation
  * `report_name_suffix`: Suffix to be used in the report files
  * `nr_sessions`: Number of market sessions to be executed
  * `first_lt_utc`: First market session timestamp (in universal timezone)
  * `session_freq`: Waiting period between market sessions (in hours)
  * `datetime_fmt`: Datetime format to be used in the datasets (should be the same in `features.csv` and `measurements.csv` files)
  * `delimiter`: Delimiter to be used in the CSV files (should be the same in `features.csv` and `measurements.csv` files)

Example of a configuration file:
```python
{
    "dataset_path": "files/datasets/example_elia_opendata",
    "report_name_suffix": "test",
    "nr_sessions": 10,
    "first_lt_utc": "2023-02-15T10:30:00Z",
    "session_freq": 24,
    "datetime_fmt": "%Y-%m-%d %H:%M",
    "delimiter": ","
}
```

### Running the simulation:

To run the simulation, simply run the following command:

``` bash
python main.py
```

By default simulation will run for ten sessions (`nr_sessions = 10`), every day (`session_freq = 24`) starting from the first launch time (`first_lt_utc`).)


### Outputs / Reporting:

On the end of the simulation runs, some report files will be produced and stored in `files/reports/<dataset_name>` directory.
These are:

1. `buyers.csv`: Includes market session buyers information, per resource in their portfolio. 
    It includes:
    * Estimated gain (function and value) by using market forecasts (see `gain_func` and `gain` columns)
    * Initial and final bids (see `initial_bid` and `final_bid` columns).
      * Initial bid is the bid that the agent would have made if it had no information about the market.
      * Final bid is the bid is the initial bid value adjusted according to the potential gain and the `max_payment` value initially defined by the user.
    * Maximum payment that the agent is willing to pay (see `max_payment` column).
    * Final amount that the agent has to pay for this resource

2. `forecasts.csv`: Forecasts produced by the market model, for each buyer resource.
3. `sellers.csv`: Includes market session sellers information, per resource in their portfolio. 
    It includes:
    * Final amount that the agent has to receive for this resource

### Execution considerations:

The simulation can take a while to run, depending on the number of sessions and resources in the dataset. 
To speed things up, you can increase the number of parallel processes by changing the `N_JOBS` variable in the `main.py` script.

If you want to run the simulation in a single process, set `N_JOBS = 1`. 

If you want to see all the process logs in the console, uncomment the following lines in the `main.py` script.

```python
# -- Setup logger (removes existing logger + adds new sys logger):
logger.remove()
logger.add(sys.stderr, level="DEBUG")
```


# Market Sessions Simulator

__NOTE__: This example runs decoupled from Data Market REST-API and database

## Overview

The following directory structure should be considered:

``` bash
.   # Current directory
├── README.md
├── session_sim_normal.py  # main script to execute simulations
├── simulation
|──── SimulationManager.py  # configs / reports manager
|──── AgentsLoader.py  # loads agents information
|──── SessionGenerator.py  # creates market sessions
├── files
|──── datasets # directory for custom datasets
|──── reports  # directory for market runs reports (created on execution)

```

## Requirements

* [Python 3.10+](https://www.python.org/downloads/)
* [Pip ^21.x](https://pypi.org/project/pip/)

## Install project dependencies
 
Run the following command, in the project `ROOT` directory:

``` bash
pip install -r requirements.txt
```

__WARNING__: If you are using a virtual environment, make sure it is activated before running the command above.

## Basic principles / nomenclature

* **users:** Agents participating in the market
* **resources:** Resources that the agents have in their portfolio (e.g., wind farm 1, wind farm 2, solar farm 1, etc.)
* **bids:** Offers that the agents make in the market, for each resource in their portfolio
* **market sessions**: Periods of time in which the market is open for bids acceptance. Each session is composed by a set of bids, for each user `resource` registered in the market.
* **measurements:** Historical data that the agents have for each resource in their portfolio. This data may be used to generate new inputs (lags) based on an autocorrelation analysis, per agent (if `auto_feature_engineering` is enabled).
* **features:** Future data that the agents have for each resource in their portfolio. This data may be used to complement lagged featurse (i.e., of measurements data).


## Running the simulation

#### Inputs (Using your own datasets):

To use your own datasets, simply add them to `files/datasets/<dataset_name>` directory. 
The market will only be successfully executed when you have the following information:

1. `files/<dataset_name>/measurements.csv`: 
    * **Exclusively** measurements data to be used in the market sessions (e.g., as forecast targets for buyers or as inputs in the form of lags for buyers / sellers)
    * Dataset, disposed in tabular form with 1 column per user resource and a `datetime` column for the timestamp references (in universal timezone).
    * **CSV format only**
2. `files/<dataset_name>/features.csv`: 
    * Features (future data) to be used by each agent in future market sessions. Can be used by agents to specify their own inputs (e.g., NWP) when participating in market sessions
    * Dataset, disposed in tabular form with 1 column per user `resource` and a `datetime` column for the timestamp references (in universal timezone).
    * **CSV format only**
3. `files/<dataset_name>/user_resources.json`: 
    * Mapping between each user identifier with its resources. Also allows the identification of each resource in both `measurements.csv`).
    * Should include:
      * `user_id`: User identifier
      * `id`: Resource identifier
      * `type`: Resource type "measurements" if historical measurements or "features" if this resource contains is future data (e.g., forecasts)
        *  Depending on its type, the data source will be "measurements.csv" or "features.csv"
    * **JSON format only**
4. `files/<dataset_name>/bids/<scenario>/bids.json`: 
    * Bids scenarios for this dataset. These will be the bids the buying agents will make in each market session.
    * If a user_id has a bid for a given resource, forecasts will be generated (if possible) to that resource.
    * Bids should include: 
      * `user_id`: User identifier
      * `resource_id`: Resource identifier
      * `max_payment`: Maximum payment that the agent is willing to pay for this resource
      * `gain_func`: Function to be used to calculate the potential gain for this resource ('mse' or 'mae')
      * `features_list`: List of features the `user_id` that will be used to enhance his model in the market session
    * **JSON format only**

Please analyze the `files/datasets/example_1` directory for an example of how to structure your dataset.

### Initial configs:

The main script `session_sim_normal.py` has some initial configurations that can be adjusted according to the user's needs:

These are:
  * `dataset_path`: Path to the dataset to be used in the simulation
  * `report_name_suffix`: Suffix to be used in the report files
  * `auto_feature_selection`: If `True`, the script will automatically select the best features for each user resource, based on the dataset provided (which speeds up the computation process)
  * `auto_feature_engineering`: If `True`, the script will automatically generate new features (lags) for each user resource, based on an autocorrelation analysis
  * `bids_scenario`: Scenario to be used in the simulation (e.g., `scenario_1`)
  * `nr_sessions`: Number of market sessions to be executed
  * `first_lt_utc`: First market session timestamp (in universal timezone)
  * `session_freq`: Frequency of market sessions (in hours)
  * `datetime_fmt`: Datetime format to be used in the datasets (should be the same in `features.csv` and `measurements.csv` files)
  * `delimiter`: Delimiter to be used in the CSV files (should be the same in `features.csv` and `measurements.csv` files)


Example of a configuration file:
```python
{
    "dataset_path": "files/datasets/example_1",
    "report_name_suffix": "spearman",
    "auto_feature_selection": True,
    "auto_feature_engineering": False,
    "bids_scenario": "scenario_1",
    "nr_sessions": 10,
    "first_lt_utc": "2021-01-10T00:00:00Z",
    "session_freq": 1,
    "datetime_fmt": "%Y-%m-%d %H:%M",
    "delimiter": ","
}
```


__WARNING__: Disabling `auto_feature_engineering` might affect the number of features available in the market dataset, for each buyer. To disable this, ensure that you have sellers / buyers providing their own 'features' (future available data) in their participation in the market session.


### Running the simulation:

To run the simulation, simply run the following command:

``` bash
python session_sim_normal.py
```

By default simulation will run for 10 sessions, on a hourly basis (`session_freq = 1`), with an example dataset composed by 3 agents, 
each with one resource (see `files/datasets/example_1` directory). 


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

__NOTE__: The simulation can take a while to run, depending on the number of sessions and resources in the dataset. Also, the final CSV's can be merged according to the market session or user / user resource identifiers.




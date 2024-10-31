# Data Sharing Barter Incentives - Collaborative Forecasting Engine

-----------------------------------------------------

[![version](https://img.shields.io/badge/version-0.0.1-blue.svg)]()
[![status](https://img.shields.io/badge/status-development-yellow.svg)]()
[![Python Version](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-360/)

## Requirements

* [Python 3.10+](https://www.python.org/downloads/)
* [Pip ^21.x](https://pypi.org/project/pip/)

## Project Structure:

The following directory structure should be considered:

``` bash
.   # Current directory
├── conf  # project settings
├── docs  # useful docs
├── examples  # example scripts (includes simulation decoupled from DB + REST)
├── src  # project source code
├── .coveragerc  # code coverage configs
├── .flake8  # flake8 configs
├── .gitignore  # gitignore file
├── .gitlab-ci.yml  # gitlab-ci file
├── docker-compose.yml  # docker-compose file
├── Dockerfile  # project dockerfile
├── dotenv  # template for environment variables
├── pytest.ini  # pytest configs
├── README.md
├── requirements.txt  # project dependencies
├── run_menu.py  # interactive menu for running the market
├── tasks.py  # CLI interface for running the market
```

## Running the collaborative forecasting process in standalone mode (without REST-API / Database integration):

It is possible to execute the collaborative forecasting engine in standalone mode, without the need for a REST-API or database integration.
For that, please check the `examples` directory, which includes a script for running the market pipeline in standalone mode.

**Please check the explanation and tutorial available on the [Examples README](examples/simulator_no_api/README.md) file.**


## Deploying the collaborative forecasting engine in a production environment:

### Initial setup:

> **_NOTE:_**  The commands below assume that you are running them from the root directory of the project (`data-sharing-barter-incentives-forecast/`)


### Configure environment variables:

The `dotenv` file provides a template for all the environment variables needed by this project. 
To configure the environment variables, copy the `dotenv` file to `.env` and fill in the values for each variable.

```shell
   $ cp dotenv .env
```

**_NOTE:_** In windows, just copy-paste the `dotenv` file and rename it to `.env`.


### With Docker:

To launch the docker containers stack:

```shell
   $ docker compose build
```

**_NOTE:_**  This will create the market image, which will be then executed later


### With Local Python Interpreter:

If you prefer using your local python interpreter (instead of docker), you'll need to manually perform the installation steps.
Also, only 'simulation' functionalities (i.e., without integration with the data market REST / DB) will be available.

1. Install poetry (if not already installed)

   ```shell
      $ pip install poetry   
    ```
   
2. Install the python dependencies
   ```shell
      $ poetry install
      $ poetry shell
   ```

3. Run the 'run_menu.py' script to open the interactive market menu
    ```shell
        $ poetry run python run_menu.py
    ```
   
> **_NOTE:_** If you're already working in a virtual environment (e.g., conda or pyenv), you can skip the `poetry shell` command. 


### Running the interactive menu:

An interactive menu is available to preview and execute the multiple functionalities of this module.

> **_NOTE 1:_**  The following instructions assume that the data market database and REST API are already initialized (available in other projects).

> **_NOTE 2:_**  The commands below assume that you are running them from the root directory of the project (`data-sharing-barter-incentives-forecast/`)

#### With Docker:

```shell
   $ docker compose run --rm app python run_menu.py
```

#### With local interpreter:
    
```shell
    $ python run_menu.py
  ```

### Using the Command Line Interface (CLI):

Alternatively, you can run the market pipeline directly, relying on the CLI interface. 
This is useful for running the market pipeline in a non-interactive way (e.g., in a production environment).

> **_NOTE 1:_**  The commands below assume that you are running them from the root directory of the project (`data-sharing-barter-incentives-forecast/`)

> **_NOTE 2:_**  The following instructions assume that the data market database and REST API are already initialized (available in other projects).

> **_WARNING:_**  The following command will run the market pipeline with the settings specified in the `.env` file.

#### With Docker:

#### Open market session:

```shell
   $ docker compose run --rm app python tasks.py open_session
```

#### Approve market bids:

```shell
   $ docker compose run --rm app python tasks.py approve_market_bids
```

#### Run market session:

 ```shell
    $ docker compose run --rm app python tasks.py run_session
 ```

#### Validate market-to-agents transfers:

```shell
    $ docker compose run --rm app python tasks.py validate_transfer_out
 ```


## Contacts:

If you have any questions regarding this project, please contact the following people:

Developers (SW source code / methodology questions):
  - José Andrade <jose.r.andrade@inesctec.pt>
  - André Garcia <andre.f.garcia@inesctec.pt>
  - Giovanni Buroni <giovanni.buroni@inesctec.pt>
  - Carla Gonçalves <carla.s.goncalves@inesctec.pt>

Contributors / Reviewers (methodology questions):
  - Ricardo Bessa <ricardo.j.bessa@inesctec.pt>

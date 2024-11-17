# Predico - Collaborative Forecasting Engine

-----------------------------------------------------

[![Python Version](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/release/python-360/)


## Requirements

* [Python ^3.11](https://www.python.org/downloads/)
* [Pip ^21.x](https://pypi.org/project/pip/)
* [Poetry ^1.8.x](https://python-poetry.org/)

## Module Structure:

The following directory structure should be considered:

``` bash
.   # Current directory
├── conf  # project settings
├── examples  # example scripts - includes simulation decoupled from remaining software stack
├── files  # log files, models, and other files
├── src  # project source code
├── Dockerfile  # project dockerfile
├── dotenv  # template for environment variables
├── README.md  # specific README for this module
├── tasks.py  # CLI interface for running the market in production
```

## Running the collaborative forecasting process in standalone mode (without REST-API / Database integration):

It is possible to execute the collaborative forecasting engine in standalone mode, without the need for a REST-API or database integration.
For that, please check the `examples` directory, which includes a script for running the market pipeline in standalone mode.

**Please check the explanation and tutorial available on the [Examples README](examples/simulator_no_api/README.md) file.**

## Deploying the collaborative forecasting engine in a production environment:

### Initial setup:

> **_NOTE:_**  The commands below assume that you are running them from the root directory of the project module `forecast`

### Configure environment variables:

The `dotenv` file provides a template for all the environment variables needed by this project. 
To configure the environment variables, copy the `dotenv` file to `.env` and fill in the values for each variable.

```shell
   $ cp dotenv .env
```

**_NOTE:_** In windows, just copy-paste the `dotenv` file and rename it to `.env`.

### With Docker:

Build the docker image with the following command:

```shell
   $ docker compose build
```

**_NOTE:_**  This will create the collaborative forecasting module image, which will be then executed later


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
   
  
> **_NOTE:_** If you're already working in a virtual environment (e.g., conda or pyenv), you can skip the `poetry shell` command. 



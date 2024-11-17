<div align="left">
  <img src="/documentation/docs/static/logo.svg"  align="middle" width="33%" height="auto">
</div>


# Collabforecast - A Collaborative Forecasting Platform

[![version](https://img.shields.io/badge/version-0.0.1-blue.svg)]()
[![status](https://img.shields.io/badge/status-development-yellow.svg)]()

## Table of Contents

1. [Introduction](#introduction)
2. [Requirements](#requirements)
3. [Project Structure](#project-structure)
4. [Project Setup](#project-setup)
5. [Production Deployment](#production-deployment)
6. [Development Mode](#development-mode)
7. [Schedule Tasks](#schedule-tasks)
8. [Contributing](#contributing)
9. [Contacts](#contacts)

## 1. Introduction

Predico Collabforecast is a backend service designed to facilitate collaborative forecasting. 
This document provides a comprehensive guide to setting up and deploying the backend service, including the necessary requirements, project structure, and deployment instructions.

### 1.1. Definitions / Nomenclature
    
- **Market Maker**: An entity that owns resources (e.g., wind farms) or manages a grid (e.g., a TSO) and seeks forecasts by opening and funding collaborative forecasting market sessions.
- **Forecaster**: An individual or organization registered in the platform, aiming to submit forecasts to collaborative forecasting challenges opened by the Market Maker, competing for the available prize money in each session.
- **Market Session**: A specific period during which Market Makers can create forecasting challenges, and Forecasters can submit forecasts for the open challenges.
- **Market Challenge**: An opportunity, published by the Market Maker, with meta-data regarding a forecasting challenge that Forecasters can try to submit forecasts for.
- **Gate Closure Time**: The deadline by which forecasts must be submitted for a market session.
- **Forecast Variables**: Quantities to be forecasted. Currently only quantile 10, 50, 90 forecasts are accepted.
- **Ensemble Forecast**: An aggregate forecast computed from multiple forecasters’ submissions.

### 1.2. Collaborative Forecasting Sessions

Below, you can find a sequence diagram illustrating the dynamics of a collaborative forecasting session, which is generally organized in four separate phases.

- **Phase 1**: A new market session is scheduled to open.
- **Phase 2**: Market Makers post new challenges, such as submitting day-ahead forecasts for specific assets (aka resources) in their portfolio.
- **Phase 3**: Forecasters log into Predico API, download raw measurements data, build their models, and submit forecasts.
- **Phase 4**: Forecasters log into Predico API, preview their skill scores and contribution importance to the final ensemble forecasts, to be delivered to the Market Maker.

**See the **<a href="/documentation/docs/static/predico-interactions-sd.png" target="_blank">service sequence diagram</a>** for a visual representation of the collaborative forecasting session.**

### 1.3. Service Components

The Predico Collabforecast service is composed of the following components:

1. **REST API**: The REST API is the core of the Predico Collabforecast service. It provides endpoints for managing users, data, market participation, and authentication.
2. **Forecasting Service**: The forecasting service is responsible for generating forecasts based on the data provided by users. It uses machine learning algorithms to generate accurate forecasts.
3. **Frontend**: The frontend is a web-based interface that allows users to interact with the Predico Collabforecast service. It provides a user-friendly interface for managing user data (e.g., create invite links for data providers, aka Forecasters)
4. **NGINX**: NGINX is used as a reverse proxy server to route requests and serve static files (documentation, frontend, etc.)
5. **PostgreSQL**: PostgreSQL is used as the database management system for storing user data, forecasts, and other information.
6. **Documentation**: The documentation provides detailed information about the Predico Collabforecast service, including installation instructions, API endpoints, and usage examples.


## 2. Repository Structure:


``` bash
.                             # Current directory
├── api                       # REST API server module source code
├── cron                      # Suggested CRONTAB for operational tasks
├── documentation             # Project Documentation (for service users)
├── forecast                  # Forecast module source code
├── frontend                  # Frontend module source code
├── nginx                     # NGINX configs
```


## 3. Initial Setup

This software stack can be deployed using Docker. The following steps will guide you through the process.

### 3.1. Prerequisites

#### 3.1.1. For Production Deployment:

Ensure you have the following installed on your system:

- [Docker](https://www.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)

#### 3.1.2. For local development (without Docker):

This software stack can be executed without Docker, but you will need to install specific dependencies for each module.

A separate guide is available for each module, with detailed information about it and how to perform a set up decoupled from the remaining software stack.

See the **"Development Mode"** section in the following documents:

- [API](api/README.md) for the REST API module.
- [Forecast](forecast/README.md) for the Forecasting module.
- [Frontend](frontend/README.md) for the Frontend module.

### 3.2. Environment variables:

Inside both `api`, `forecast` and `frontend` directories, you will find a file named `dotenv`. This file contains the environment variables that are used by the application. You can copy this file to `.env` and update the variables to your specifics.

```shell
cp dotenv .env
```

**Ensure you set the environment variables. If you do not create these files, the next steps will not work properly.**


## 4. Production Deployment

### 4.1. Start Docker Containers Stack

```shell
docker compose -f docker-compose.prod.yml up -d
```

This command should start the following services:
- `predico_rest_app`: Django REST API
- `predico_forecast`: Forecasting service
- `predico_frontend`: React frontend
- `predico_nginx`: NGINX server
- `predico_postgresql`: PostgreSQL database
- `predico_mkdocs`: Intermediate build to generate documentation

**Note that:**
    - Service mainpage will be available on http://0.0.0.0:80
    - Service API will be available on http://0.0.0.0/api

### 4.2. Configure service super user:

Service administrators need to be added via CLI, with the following command.

```shell  
docker exec -it predico_rest_app python manage.py createadmin
```

**Note that:**
- `createadmin` is a custom command that creates a superuser and confirms if this user should be a session manager.
- `session_manager` users have a higher level of privileges and can manage sessions (open / close / post ensemble forecasts / etc.)

### 4.3. Check functional tests:

Check if all tests pass successfully

```shell
docker exec -it predico_rest_app pytest
```

See the Swagger (http://0.0.0.0:80/swagger) for methods description.

### 4.4. Using the Command Line Interface (CLI):

Market sessions can be open/executed through the command line interface (CLI) available in the `forecast` module.

> **_NOTE:_**  The following instructions assume you have all the services running. If you don't, please refer to the previous section.

> **_WARNING:_**  The following command will run the market pipeline with the settings specified in the `.env` file.

#### 4.4.1. Open market session:

When executed, this task will open a new market session, allowing forecasters to submit their forecasts.

```shell
docker compose -f docker-compose.prod.yml run --rm forecast python tasks.py open_session
```

#### 4.4.2. Close & Run collaborative forecasting session:

When executed, this task will close the currently open market session (gate closure time) and run the collaborative forecasting models.

Remember that Forecasters will not be able to submit forecasts after the gate closure time.

 ```shell
docker compose -f docker-compose.prod.yml run --rm forecast python tasks.py run_session
 ```
 
#### 4.4.3. Run data value assessment tasks

When executed, this task will calculate individual forecasters forecast skill scores and contribution to the final ensemble forecasts.

 ```shell
docker compose -f docker-compose.prod.yml run --rm forecast python tasks.py calculate_ensemble_weights
 ```

## 5. Contributing

This project is currently under active development and we are working on a contribution guide.

### 5.1. How do I report a bug?
Please report bugs by opening an issue on our GitHub repository.

## 6. Contacts:

If you have any questions regarding this project, please contact the following people:

Developers (SW source code / methodology questions):
  - José Andrade <jose.r.andrade@inesctec.pt>
  - André Garcia <andre.f.garcia@inesctec.pt>
  - Giovanni Buroni <giovanni.buroni@inesctec.pt>

Contributors / Reviewers (methodology questions):
  - Carla Gonçalves <carla.s.goncalves@inesctec.pt>
  - Ricardo Bessa <ricardo.j.bessa@inesctec.pt>

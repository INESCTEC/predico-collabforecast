# Predico Collabforecast - A Collaborative Forecasting Platform

[![version](https://img.shields.io/badge/version-0.0.1-blue.svg)]()
[![status](https://img.shields.io/badge/status-development-yellow.svg)]()
[![Python Version](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/release/python-360/)

## Table of Contents

1. [Introduction](#introduction)
2. [Requirements](#requirements)
3. [Project Structure](#project-structure)
4. [Project Setup](#project-setup)
5. [Production Deployment](#production-deployment)
6. [Development Mode](#development-mode)
7. [Schedule Tasks](#schedule-tasks)
8. [Contacts](#contacts)
9. [Contributing](#contributing)
10. [License](#license)
11. [FAQ](#faq)
12. [Code of Conduct](#code-of-conduct)

## Introduction

Predico Collabforecast is a backend service designed to facilitate collaborative forecasting. This document provides a comprehensive guide to setting up and deploying the backend service, including the necessary requirements, project structure, and deployment instructions.

## Requirements

* [Python ^3.11](https://www.python.org/downloads/)
* [Pip ^21.x](https://pypi.org/project/pip/)


## Project Structure:

The following directory structure should be considered:

``` bash
.   # Current directory
├── api                       # REST API source code
├──── api                     # main configs
├──── authentication          # authentication endpoints
├──── files                   # system files (logging, db backups)
├──── data                    # data ops endpoints
├──── market                  # market participation endpoints
├──── users                   # users endpoints
├── cron                      # Suggested CRONTAB
├── documentation             # Project Documentation (for service users)
├── forecast                  # Forecasting source code
├── frontend                  # Frontend source code
├── nginx                     # NGINX configs
```


## Project Setup

This software stack can be deployed using Docker. The following steps will guide you through the process.

### Prerequisites

Ensure you have the following installed on your system:
- Docker
- Docker Compose

### Environment variables:

Inside both 'api', 'forecast' and 'frontend' directories, you will find a file named `dotenv`. This file contains the environment variables that are used by the application. You can copy this file to `.env` and update the variables to your specifics.

```shell
cp dotenv .env
```

!!! warning:
    Make sure you set the environment variables. If you do not create these files, the application will not work properly.

Start docker stack:

## Production Deployment

### Start Docker Stack

```shell
docker-compose -f docker-compose.prod.yml up -d
```

This command should start the following services:
- `predico_rest_app`: Django REST API
- `predico_forecast`: Forecasting service
- `predico_frontend`: React frontend
- `predico_nginx`: NGINX server
- `predico_postgresql`: PostgreSQL database
- `predico_mkdocs`: Intermediate build to generate documentation

!!! info:
    - Service mainpage will be available on http://0.0.0.0:80
    - Service API will be available on http://0.0.0.0/api


### Configure Super user:

Service administrators need to be added via CLI, with the following command.

```shell  
docker exec -it predico_rest_app python manage.py createsuperuser
```

### Check functional tests:

Check if all tests pass successfully

```shell
docker exec -it predico_rest_app pytest
```

See the Swagger (http://0.0.0.0:80/swagger) for methods description.

### Frontend

For the frontend change the `REACT_APP_API_URL` in the docker-compose.prod to the correct URL.

```yaml
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      args:
        REACT_APP_API_URL: https://predico-elia.inesctec.pt/api/v1
    container_name: predico_frontend_build
    networks:
      - predico_network
    volumes:
      - frontend_build:/app/build  # This volume will store the build output
```

## Development Mode

How to run the code in development mode, with the REST API decoupled from docker stack?

First, install the necessary project python dependencies:

```shell
cd /api
poetry install
poetry shell
```

Then, create a `.dev.env` file with environment variables used to debug and update default environment variables to your specifics.

```shell
cp dotenv .dev.env
```

**Important:** Make sure you force develop mode by using the following environment variable `DJANGO_APPLICATION_ENVIRONMENT=develop` and `POSTGRES_HOST=localhost`

Then, use docker-compose to initialize a Postgres DB:

```shell
docker-compose up -d --build postgresql
```

Once your DB is up, you can debug locally by just by uncommenting the following lines in "environment.lines: 

```python
from dotenv import load_dotenv
load_dotenv(".dev.env")
```

After this, you can easily run your application without docker container, in either an IDE or straight from the command line.

1. Migrate your DB migrations:

```shell
python manage.py migrate
```

2. Create a superuser:

```shell
python manage.py createsuperuser
```

3. Run your app using through Django runserver command:

```shell
python manage.py runserver
```

## Schedule tasks

To schedule tasks, you can use the Django management commands:

- Remove older register tokens

```shell
python manage.py delete_old_register_tokens
```

- Remove older password reset tokens

```shell
python manage.py delete_old_reset_password_tokens
```

## Contributing

This project is currently under active development and we are working on a contribution guide.

### How do I report a bug?
Please report bugs by opening an issue on our GitHub repository.

## Contacts:

If you have any questions regarding this project, please contact the following people:

Developers (SW source code / methodology questions):
  - José Andrade <jose.r.andrade@inesctec.pt>
  - André Garcia <andre.f.garcia@inesctec.pt>
  - Giovanni Buroni <giovanni.buroni@inesctec.pt>

Contributors / Reviewers (methodology questions):
  - Carla Gonçalves <carla.s.goncalves@inesctec.pt>
  - Ricardo Bessa <ricardo.j.bessa@inesctec.pt>

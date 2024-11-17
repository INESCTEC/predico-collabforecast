# Collabforecast - API (REST) Server

## Introduction

This project is a REST API that provides endpoints for Collabforecast market sessions and user management / authentication.
It is built using [Django Rest Framework](https://www.django-rest-framework.org/).

## Module Structure:

The following directory structure should be considered:

``` bash
.                             # Current directory
├── api                     # main configs
├── authentication          # authentication endpoints
├── files                   # system files (logging, db backups)
├── data                    # data ops endpoints
├── market                  # market participation endpoints
├── users                   # users endpoints
```

## Run API server decoupled from remaining services

### Requirements

* [Python ^3.11](https://www.python.org/downloads/)
* [Pip ^21.x](https://pypi.org/project/pip/)
ª [Poetry ^1.8.x](https://python-poetry.org/)

###  Prepare Python environment:
How to run the code in development mode, with the REST API decoupled from docker stack?

First, install the necessary project python dependencies:

```shell
poetry install
poetry shell
```

### Prepare the database:
In the same directory, create a `.dev.env` file with environment variables used to debug and update default environment variables to your specifics.

```shell
cp dotenv .dev.env
```

**Important:** Ensure you force develop mode by using the following environment variable `DJANGO_APPLICATION_ENVIRONMENT=develop` and `POSTGRES_HOST=localhost`

Then, initialize the service Postgres DB:

```shell
# Execute on the project root:
docker compose -f docker-compose.dev.yml up -d
```

### Run using built-in Django server:

Once your DB is up, you can debug locally by just by uncommenting the following lines in the `manage.py` file:

```python api/manage.py
from dotenv import load_dotenv
load_dotenv(".dev.env")
```

After this, you can easily run your application without docker container, in either an IDE or straight from the command line.

#### 1. Migrate DB migrations:

```shell
python manage.py migrate
```

#### 2. Create a superuser, with session management privileges:

```shell
python manage.py createadmin
```

#### 3. Run your app using through Django runserver:

```shell
# This will start the Django development server (do not use this in production):
python manage.py runserver
```

**By default the API will be available at `http://127.0.0.1:8000`. If you want to change either HOST or PORT references, please update the `SWAGGER_BASE_URL` environment variable in the `.dev.env` file.**


#### 4. Check if you can reach the test endpoint:

You can test if the API is running with a simple HTTP GET request (e.g., using CURL)

```shell
curl http://127.0.0.1:8000/api/v1/health/
```


#### 4. Access the API swagger or redoc documentation:

Default URLs:

**Swagger**
http://127.0.0.1:8000/swagger

**Redoc**
http://127.0.0.1:8000/redoc


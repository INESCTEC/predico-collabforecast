# Predico Collabforecast - Backend

-----------------------------------------------------

[![version](https://img.shields.io/badge/version-0.0.1-blue.svg)]()
[![status](https://img.shields.io/badge/status-development-yellow.svg)]()
[![Python Version](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/release/python-360/)

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
├──── data                    # data operations endpoints
|──── logs                    # logs directory
├──── market                  # market participation endpoints
├──── tests                   # unittests suite
├──── users                   # users endpoints
├── nginx                     # NGINX configs
├──── Dockerfile              # Dockerfile
├──── index.html              # Docs mainpage
├──── nginx.conf              # Nginx config
├──── project.conf            # Nginx config
├── docs                      # Docs
├── .dockerignore             # dockerignore file
├── .gitignore                # gitignore file
├── .gitlab-ci.yml            # gitlab-ci file
├── docker-compose.prod.yml   # docker-compose file (production)
├── docker-compose.test.yml   # docker-compose file (CICD)
├── docker-compose.yml        # docker-compose file (development)
├── README.md
```

## Project Setup

Create a `.env` file from a provided example (`dotenv`) and update its variables
```shell
cp dotenv .env
```

Start docker stack:

```shell
docker-compose up -d
```

Enter docker container (app):

```shell
docker exec -it predico_rest_app bash
```

Inside the container (`predico_rest_app`) apply current migrations and create superuser.

```shell
python manage.py migrate
python manage.py createsuperuser
```

Run collectstatic to serve static files (relevant if behind NGINX)
```shell
python manage.py collectstatic
```

Check if all tests pass successfully

```shell
pytest
```

See the Swagger (http://0.0.0.0:80/swagger) for methods description.


## How to easy deploy in "debug" mode (developers)?

How to run the code in development mode, with APP decoupled from docker stack?

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


## Contacts:

If you have any questions regarding this project, please contact the following people:

Developers (SW source code / methodology questions):
  - José Andrade <jose.r.andrade@inesctec.pt>
  - André Garcia <andre.f.garcia@inesctec.pt>
  - Giovanni Buroni <giovanni.buroni@inesctec.pt>

Contributors / Reviewers (methodology questions):
  - Carla Gonçalves <carla.s.goncalves@inesctec.pt>
  - Ricardo Bessa <ricardo.j.bessa@inesctec.pt>

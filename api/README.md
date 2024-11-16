
## Module Structure:

The following directory structure should be considered:

``` bash
.                             # Current directory
├── api                       # REST API source code
├──── api                     # main configs
├──── authentication          # authentication endpoints
├──── files                   # system files (logging, db backups)
├──── data                    # data ops endpoints
├──── market                  # market participation endpoints
├──── users                   # users endpoints
```

### API (REST) Decoupled

####  Prepare Python environment:
How to run the code in development mode, with the REST API decoupled from docker stack?

First, install the necessary project python dependencies:

```shell
cd /api
poetry install
poetry shell
```

#### Prepare the database:
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

#### Run the REST API:

Once your DB is up, you can debug locally by just by uncommenting the following lines in the `manage.py` file: 

```python api/manage.py
from dotenv import load_dotenv
load_dotenv(".dev.env")
```

After this, you can easily run your application without docker container, in either an IDE or straight from the command line.

1. Migrate DB migrations:

```shell
python manage.py migrate
```

2. Create a superuser, with session management privileges:

```shell
python manage.py createadmin
```

3. Run your app using through Django runserver:

```shell
# This will start the Django development server (do not use this in production):
python manage.py runserver
```

### API (Forecast) Decoupled

You can also try this service forecasting modules decoupled from the REST API and the service Database.
Check the documentation of the [Forecast](forecast/README.md) module.
FROM python:3.12-bookworm

#change working directory
WORKDIR /app

# set env variables
ENV PYTHONDONTWRITEBYTECODE=1 \
  PYTHONUNBUFFERED=1 \
  # Poetry's configuration:
  POETRY_NO_INTERACTION=1 \
  POETRY_VIRTUALENVS_CREATE=false \
  POETRY_CACHE_DIR='/var/cache/pypoetry' \
  POETRY_HOME='/usr/local'

RUN apt-get update && apt-get install -y build-essential

# install required packages
# copy requirements
COPY poetry.lock pyproject.toml /app/
RUN pip install poetry && poetry install

# copy project
COPY . /app

#CMD ["tail", "-f", "/dev/null"]

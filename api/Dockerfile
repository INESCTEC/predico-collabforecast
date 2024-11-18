FROM python:3.12-bookworm

# Change working directory
WORKDIR /usr/src/django

# Set env variables
ENV PYTHONDONTWRITEBYTECODE=1 \
  PYTHONUNBUFFERED=1 \
  # Poetry's configuration:
  POETRY_NO_INTERACTION=1 \
  POETRY_VIRTUALENVS_CREATE=false \
  POETRY_CACHE_DIR='/var/cache/pypoetry' \
  POETRY_HOME='/usr/local'

## Add the wait script to the image
ADD https://github.com/ufoscout/docker-compose-wait/releases/download/2.9.0/wait /wait
RUN chmod +x /wait

# Add PostgreSQL APT repository
RUN apt-get update && apt-get install -y wget gnupg2 lsb-release
RUN echo "deb http://apt.postgresql.org/pub/repos/apt/ $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list
RUN wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -

RUN apt-get update && apt-get install -y build-essential postgresql-client-16
RUN pip install --upgrade pip

# Install required dependencies
COPY poetry.lock pyproject.toml /usr/src/django/
RUN pip install poetry && poetry install

RUN mkdir /var/log/odoo \
    && touch /var/log/odoo/gunicorn-error.log \
    && touch /var/log/odoo/gunicorn-access.log

# Copy project
COPY . /usr/src/django/

## Launch the wait tool to wait for postgres to be up (check-compose)
CMD /wait

# Run entrypoint.sh
ENTRYPOINT ["sh","/usr/src/django/entrypoint.sh"]
# CMD ["tail", "-f", "/dev/null"]

# For security reasons the user that will run
# our software will be user and not root
# RUN adduser --disabled-login --gecos "" user
# USER user
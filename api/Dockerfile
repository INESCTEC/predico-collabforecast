FROM python:3.12-bookworm

#change working directory
WORKDIR /usr/src/django

# set env variables
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

RUN apt-get update && apt-get install -y build-essential
RUN pip install --upgrade pip

# install required dependencies
COPY poetry.lock pyproject.toml /usr/src/django/
RUN pip install poetry && poetry install

RUN mkdir /var/log/odoo \
    && touch /var/log/odoo/gunicorn-error.log \
    && touch /var/log/odoo/gunicorn-access.log

# copy project
COPY . /usr/src/django/

## Launch the wait tool to wait for postgres to be up (check-compose)
CMD /wait

# run entrypoint.sh
ENTRYPOINT ["sh","/usr/src/django/entrypoint.sh"]
# CMD ["tail", "-f", "/dev/null"]

# for security reasons the user that will run
# our software will be user and not root
# RUN adduser --disabled-login --gecos "" user
# USER user
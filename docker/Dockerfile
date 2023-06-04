FROM python:3.11-slim-buster as compile-image

ENV PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PYTHONUNBUFFERED=1

ENV PIP_DEFAULT_TIMEOUT=100 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VERSION=1.4.2


RUN apt-get update && apt-get --no-install-recommends install -y build-essential git openssh-client

RUN pip install --upgrade pip
RUN pip install --no-cache-dir "poetry==$POETRY_VERSION"

WORKDIR /pysetup
COPY pyproject.toml poetry.lock* ./

RUN poetry config virtualenvs.create false && \
    poetry install --no-root --without=dev --no-interaction --no-ansi

#######

FROM python:3.11-slim-buster as runtime-image
RUN apt-get -q update && apt-get install -y --no-install-recommends vim && apt-get clean && rm -rf /var/lib/apt

ENV TZ=Europe/Moscow
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

COPY --from=compile-image /usr/local /usr/local

COPY docker/start.sh /
RUN chmod +x /start.sh

COPY docker/gunicorn_conf.py /gunicorn_conf.py

COPY ./app /app/app
COPY ./alembic.ini /app/alembic.ini
COPY ./pyproject.toml /app/pyproject.toml

COPY docker/prestart.sh /app/prestart.sh
RUN chmod +x /app/prestart.sh

WORKDIR /app/

ENV PYTHONPATH=/app

EXPOSE 80

ARG VCS_REF
ARG BUILD_DATE
ARG TAG_NAME

ENV RELEASE=$TAG_NAME

LABEL vcs_ref=$VCS_REF \
      build_date=$BUILD_DATE \
      release=$RELEASE \
      project="telegpick-app" \
      application="telegpick-backend" \
      maintainer="clplf"


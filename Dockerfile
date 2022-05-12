FROM python:3.10.4

ARG POETRY_VERSION=1.1.12
ENV POETRY_VERSION=$POETRY_VERSION
ENV POETRY_HOME=/usr/local
ENV POETRY_VIRTUALENVS_CREATE=false
RUN curl -sSL https://install.python-poetry.org | python -

# this installs dependencies for pdf2image
RUN apt-get update && apt-get install -y --no-install-recommends poppler-utils && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/app

COPY poetry.lock pyproject.toml /usr/src/app/

RUN poetry install

COPY . /usr/src/app/

ENV PYTHONPATH /usr/src/app

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "rossum.api:app"]

FROM python:3.12-bookworm

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get install -y build-essential libpq-dev curl netcat-openbsd apt-utils

WORKDIR /app

COPY poetry.lock pyproject.toml /app/

RUN pip install --upgrade pip "poetry==2.1.1"

RUN poetry config virtualenvs.create false --local

RUN useradd -rms /bin/bash artyombn && chmod 777 /opt /run

RUN poetry install
RUN pip list

COPY . /app

RUN chmod +x /app/run_all.sh

CMD ["bash", "/app/run_all.sh"]
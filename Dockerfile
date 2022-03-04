# FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8
FROM python:3-slim

COPY ./app /app
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install system dependencies
RUN apt-get update \
  # && apt-get -y install netcat gcc postgresql nano \
  && apt-get -y install nano \
  && apt-get clean

# install python dependencies
RUN python -m pip install --upgrade pip
RUN pip install -r requirements.txt
# WTF: this works just fine outside of rquirements.txt
RUN pip install discord

CMD tail /dev/null -f

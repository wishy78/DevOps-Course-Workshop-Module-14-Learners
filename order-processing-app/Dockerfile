# Use official Python base image
FROM --platform=linux/amd64 python:3.9-slim-buster as base

ENV APP_INSTALL=/app
ENV PYTHONPATH=${APP_INSTALL}
ENV PORT=80
ENV ACCEPT_EULA=Y

# Install required tools
RUN apt-get update && apt-get install curl gnupg apt-transport-https ca-certificates -y
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
RUN curl https://packages.microsoft.com/config/debian/9/prod.list > /etc/apt/sources.list.d/mssql-release.list
RUN apt-get update && apt-get install unixodbc-dev g++ msodbcsql17 mssql-tools -y

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . /app

WORKDIR /app

####################################
# Production Image
FROM base as production

RUN pip install gunicorn

ENV FLASK_ENV=production
EXPOSE 80

# Only one worker so we don't have multiple background job schedulers
ENTRYPOINT gunicorn --bind 0.0.0.0:${PORT} --workers 1 'app:app'

####################################
# Local Development Image
FROM base as development

ENV FLASK_ENV=development
EXPOSE 80

# Use a launch script to support both env variable expansion
# And command line arguments
ENTRYPOINT flask run --host 0.0.0.0 --port "${PORT}" "$@"

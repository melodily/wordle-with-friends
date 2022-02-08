
FROM python:3.7

ENV PYTHONFAULTHANDLER=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONHASHSEED=random
ENV PYTHONDONTWRITEBYTECODE 1
ENV PIP_NO_CACHE_DIR=off
ENV PIP_DISABLE_PIP_VERSION_CHECK=on
ENV PIP_DEFAULT_TIMEOUT=100

# Env vars
ENV TELEGRAM_TOKEN ${TELEGRAM_TOKEN}
ENV DATABASE_URL ${DATABASE_URL}

RUN apt-get update
RUN apt-get install -y python3 python3-pip python-dev build-essential python3-venv

COPY requirements.txt ./requirements.txt
RUN pip install -r requirements.txt
COPY entrypoint.sh entrypoint.sh

RUN mkdir -p /src
ADD . /src
WORKDIR /src

EXPOSE 443
CMD ["sh", "entrypoint.sh"]

FROM python:3.11.5-slim
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
RUN apt-get update && apt-get upgrade -y && apt-get install sqlite3 curl libcurl4-openssl-dev libssl-dev gcc -y
RUN python -m pip install --upgrade pip
COPY requirements.txt .
RUN python -m pip install -r requirements.txt
RUN python -m pip install --compile --global-option="--with-openssl" --no-cache-dir pycurl
WORKDIR /app
COPY ./sources /app
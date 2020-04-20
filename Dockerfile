FROM python:3.8.2-alpine
WORKDIR /opt/index-royale
RUN apk add build-base libffi-dev openssl-dev python3-dev
COPY requirements.txt .
RUN pip install -r requirements.txt

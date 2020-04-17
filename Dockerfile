FROM python:3.8.2-alpine
WORKDIR /opt/index-royale
COPY requirements.txt .
RUN pip install -r requirements.txt

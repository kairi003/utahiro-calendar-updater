FROM python:3.10-slim

WORKDIR /workdir

COPY requirements.txt /workdir/requirements.txt

RUN python3 -m pip install --upgrade pip && \
    python3 -m pip install -r requirements.txt

RUN playwright install --with-deps chromium

FROM python:3.10-slim

WORKDIR /app

RUN python3 -m pip install --upgrade pip && \
    python3 -m pip install playwright==1.37.0 requests==2.28.2

RUN playwright install --with-deps chromium

CMD ["python3", "/app/main.py"]

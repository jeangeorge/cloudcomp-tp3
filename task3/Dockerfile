FROM python:3.9-slim

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY serverless_runtime.py /app/serverless_runtime.py

WORKDIR /app

CMD ["python", "serverless_runtime.py"]

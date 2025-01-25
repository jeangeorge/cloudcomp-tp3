FROM python:3.9-slim

COPY requirements.txt /opt/requirements.txt
RUN pip install --no-cache-dir -r /opt/requirements.txt

COPY serverless_runtime.py /opt/serverless_runtime.py

WORKDIR /opt

CMD ["python", "serverless_runtime.py"]

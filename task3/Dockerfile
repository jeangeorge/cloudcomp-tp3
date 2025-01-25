FROM python:3.9-slim

COPY requirements.txt /opt/requirements.txt
RUN pip install --no-cache-dir -r /opt/requirements.txt

COPY ./app /opt

WORKDIR /opt

CMD ["python", "app.py"]

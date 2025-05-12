FROM python:3.13-slim

# 1) create a group & non-root user “celery”
RUN groupadd --system celery \
 && useradd  --system --gid celery --home-dir /app celery

WORKDIR /app

# 2) install dependencies
COPY requirements.txt . 
RUN pip install --no-cache-dir -r requirements.txt

# 3) copy your code
COPY ./app ./app

# 4) make /app fully world-writable so anyone can create files here
RUN chmod -R a+rwx /app

ENV PYTHONUNBUFFERED=1

# 5) switch to non-root user for running the app
USER celery

# default for the web service; the worker will override the command only
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]





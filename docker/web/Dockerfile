FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    binutils \
    libproj-dev \
    gdal-bin \
    postgresql-client \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

COPY docker/web/gunicorn.conf.py /app/gunicorn.conf.py
RUN chmod +x /app/docker/web/entrypoint.sh

EXPOSE 8000

CMD ["bash", "-lc", "/app/docker/web/entrypoint.sh"]

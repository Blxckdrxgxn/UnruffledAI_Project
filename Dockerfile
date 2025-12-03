# ---- Base image with full Debian (TensorFlow compatible) ----
FROM python:3.10-bullseye

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# ---- System dependencies (important!) ----
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# ---- Install Python dependencies ----
COPY requirements.txt /app/

# Upgrade pip
RUN pip install --upgrade pip

# Install your Django + TensorFlow packages
RUN pip install --no-cache-dir -r requirements.txt

# ---- Copy project files into container ----
COPY . /app/

# ---- Collect static files ----
RUN python manage.py collectstatic --noinput

# ---- Expose port ----
EXPOSE 8000

# ---- Run Gunicorn (production server) ----
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]



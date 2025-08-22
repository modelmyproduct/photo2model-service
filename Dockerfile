# Lightweight, reliable base so the build won't fail
FROM python:3.10-slim

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y \
    build-essential git wget curl unzip \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip setuptools wheel
RUN python -m pip install --no-cache-dir -r /app/requirements.txt

# Copy code
COPY api.py /app/api.py
COPY .gitignore /app/.gitignore

# Expose for RunPod / testing
EXPOSE 8000

# Start the FastAPI server
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]

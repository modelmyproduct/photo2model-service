# === Base image ===
FROM nvidia/cuda:11.8.0-runtime-ubuntu20.04

# Avoid timezone & interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# === System dependencies ===
RUN apt-get update && \
    apt-get install -y \
    git \
    wget \
    curl \
    unzip \
    build-essential \
    cmake \
    ninja-build \
    python3 \
    python3-pip \
    python3-dev \
    ffmpeg \
    colmap && \
    rm -rf /var/lib/apt/lists/*

# === Set Python ===
RUN ln -s /usr/bin/python3 /usr/bin/python

# === Python dependencies ===
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Pin numpy < 2 because PyTorch / gsplat may break with numpy 2.x
RUN pip install --no-cache-dir "numpy<2"

# Install PyTorch (CPU for now, can be changed to GPU wheels later)
RUN pip install --no-cache-dir torch torchvision torchaudio

# === Install gsplat ===
RUN git clone https://github.com/nerfstudio-project/gsplat.git /tmp/gsplat && \
    cd /tmp/gsplat && pip install --no-cache-dir . && \
    rm -rf /tmp/gsplat

# === Copy service code ===
WORKDIR /app
COPY . /app

# Install API dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose API port
EXPOSE 8000

# Run API with uvicorn
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]

# Use NVIDIA CUDA base image with Python
FROM nvidia/cuda:11.8.0-devel-ubuntu22.04

# Avoid interactive prompts during package installs
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-dev python3-venv \
    build-essential git cmake ninja-build wget unzip \
    libgl1-mesa-dev libboost-all-dev libeigen3-dev \
    && rm -rf /var/lib/apt/lists/*

# --- Install COLMAP (prebuilt binaries instead of source build) ---
RUN wget https://demuc.de/colmap/releases/colmap-3.8-linux.tar.gz && \
    tar -xvzf colmap-3.8-linux.tar.gz && \
    mv colmap-3.8-linux /opt/colmap && \
    ln -s /opt/colmap/bin/colmap /usr/local/bin/colmap && \
    rm colmap-3.8-linux.tar.gz

# --- Python dependencies ---
RUN pip install --upgrade pip
RUN pip install --no-cache-dir "numpy<2" torch torchvision torchaudio \
    Pillow tqdm requests scikit-image opencv-python-headless

# --- Clone and install gsplat ---
RUN git clone https://github.com/nerfstudio-project/gsplat.git /tmp/gsplat && \
    cd /tmp/gsplat && pip install --no-cache-dir . && \
    rm -rf /tmp/gsplat

# --- Copy your service code into container ---
WORKDIR /app
COPY . /app

# --- Expose HTTP for RunPod endpoint ---
EXPOSE 5000

# --- Start API ---
CMD ["python3", "api.py"]

# === Base image with CUDA + PyTorch ===
FROM nvidia/cuda:11.8.0-devel-ubuntu20.04

# === System deps ===
RUN apt-get update && apt-get install -y \
    git wget curl unzip ninja-build build-essential \
    cmake python3 python3-pip python3-dev \
    && rm -rf /var/lib/apt/lists/*

# === Set Python alias ===
RUN ln -s /usr/bin/python3 /usr/bin/python

# === Upgrade pip & setuptools ===
RUN pip install --upgrade pip setuptools wheel

# === Install Python deps ===
RUN pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
RUN pip install --no-cache-dir "numpy<2" scipy scikit-image opencv-python tqdm requests flask

# === Install COLMAP (prebuilt binary v3.8) ===
RUN apt-get update && apt-get install -y wget && \
    wget https://demuc.de/colmap/releases/colmap-3.8-linux.tar.gz && \
    tar -xvzf colmap-3.8-linux.tar.gz && \
    mv colmap-3.8-linux /opt/colmap && \
    ln -s /opt/colmap/bin/colmap /usr/local/bin/colmap && \
    rm colmap-3.8-linux.tar.gz

# === Install gsplat from GitHub ===
RUN git clone https://github.com/nerfstudio-project/gsplat.git /tmp/gsplat && \
    cd /tmp/gsplat && pip install --no-cache-dir . && \
    rm -rf /tmp/gsplat

# === App setup ===
WORKDIR /app
COPY . /app

# === Expose port for API ===
EXPOSE 8000

# === Default start command ===
CMD ["python", "api.py"]

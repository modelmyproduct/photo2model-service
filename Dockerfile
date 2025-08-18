# ===== Base image =====
FROM nvidia/cuda:11.8.0-devel-ubuntu20.04

# Avoid timezone config hanging during build
ENV DEBIAN_FRONTEND=noninteractive

# ===== Install base deps =====
RUN apt-get update && apt-get install -y \
    git wget unzip build-essential ninja-build cmake python3 python3-pip python3-dev \
    && rm -rf /var/lib/apt/lists/*

# ===== Install COLMAP (prebuilt release) =====
WORKDIR /opt
RUN wget https://github.com/colmap/colmap/releases/download/3.9/colmap-3.9-linux-cuda11.8.tar.gz && \
    tar -xvzf colmap-3.9-linux-cuda11.8.tar.gz && \
    mv colmap-3.9-linux /opt/colmap && \
    ln -s /opt/colmap/bin/colmap /usr/local/bin/colmap && \
    rm colmap-3.9-linux-cuda11.8.tar.gz

# ===== Install Python deps =====
RUN pip3 install --upgrade pip setuptools wheel
RUN pip3 install "numpy<2" torch torchvision Pillow flask

# Optional: gsplat if needed
# RUN git clone https://github.com/nerfstudio-project/gsplat.git /tmp/gsplat && \
#     pip3 install /tmp/gsplat && rm -rf /tmp/gsplat

# ===== Add API script =====
WORKDIR /workspace
COPY api.py /workspace/api.py

CMD ["python3", "api.py"]

# === Base image ===
FROM nvidia/cuda:11.8.0-devel-ubuntu22.04

# === Set noninteractive mode for apt ===
ENV DEBIAN_FRONTEND=noninteractive

# === Install base dependencies ===
RUN apt-get update && apt-get install -y \
    python3.10 python3.10-dev python3-pip python3.10-venv \
    git wget curl build-essential \
    libboost-all-dev libeigen3-dev libsuitesparse-dev \
    libfreeimage-dev libgoogle-glog-dev libgflags-dev \
    libglew-dev qtbase5-dev libqt5opengl5-dev \
    libcgal-dev libceres-dev unzip \
    && rm -rf /var/lib/apt/lists/*

# === Set python3.10 as default ===
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.10 1 && \
    update-alternatives --install /usr/bin/pip pip /usr/bin/pip3 1

# === Install Python dependencies ===
RUN pip install --upgrade pip setuptools wheel
RUN pip install "numpy<2"

# === Install PyTorch (CUDA 11.8 build) ===
RUN pip install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu118

# === Install COLMAP (prebuilt binary) ===
RUN wget https://github.com/colmap/colmap/releases/download/3.9/colmap-3.9-linux-cuda11.8.tar.gz && \
    tar -xvzf colmap-3.9-linux-cuda11.8.tar.gz && \
    mv colmap-3.9-linux /opt/colmap && \
    ln -s /opt/colmap/bin/colmap /usr/local/bin/colmap && \
    rm colmap-3.9-linux-cuda11.8.tar.gz

# === Build and install gsplat ===
RUN git clone https://github.com/nerfstudio-project/gsplat.git /tmp/gsplat && \
    cd /tmp/gsplat && pip install --no-cache-dir . && \
    rm -rf /tmp/gsplat

# === Set working directory ===
WORKDIR /workspace

# === Default command ===
CMD ["bash"]

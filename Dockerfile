# Use NVIDIA base image with CUDA + PyTorch
FROM nvidia/cuda:11.8.0-devel-ubuntu20.04

# Avoid interactive timezone prompt
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git wget curl unzip build-essential cmake ninja-build \
    python3 python3-pip python3-dev python3-setuptools \
    libboost-all-dev libeigen3-dev libfreeimage-dev \
    libgoogle-glog-dev libgflags-dev libflann-dev \
    libatlas-base-dev libsuitesparse-dev \
    && rm -rf /var/lib/apt/lists/*

# === Install COLMAP (prebuilt release from GitHub) ===
RUN apt-get update && apt-get install -y wget && \
    wget https://github.com/colmap/colmap/releases/download/3.9/colmap-3.9-linux.tar.gz && \
    tar -xvzf colmap-3.9-linux.tar.gz && \
    mv colmap-3.9-linux /opt/colmap && \
    ln -s /opt/colmap/bin/colmap /usr/local/bin/colmap && \
    rm colmap-3.9-linux.tar.gz

# Upgrade pip + install Python dependencies
RUN pip3 install --upgrade pip
RUN pip3 install "numpy<2" torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu118
RUN pip3 install fastapi uvicorn pillow tqdm scikit-image

# Copy your app code into container
WORKDIR /app
COPY . /app

# Expose API port
EXPOSE 8000

# Run API when container starts
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]

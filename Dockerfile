# Dockerfile for photo2model-service
# Base image with build tools and CUDA support for OpenMVS if RunPod provides GPU
FROM nvidia/cuda:12.2.0-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /workspace

# System packages needed for COLMAP & OpenMVS + Python
RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl ca-certificates wget unzip zip build-essential cmake pkg-config \
    libboost-all-dev libeigen3-dev libfreeimage-dev libgoogle-glog-dev libgflags-dev \
    libsuitesparse-dev libmetis-dev libjpeg-dev libpng-dev libtiff-dev \
    libatlas-base-dev libblas-dev liblapack-dev libxxhash-dev libtbb-dev \
    libglew-dev libopencv-dev qtbase5-dev libqt5opengl5-dev libcgal-dev \
    python3 python3-pip python3-dev python3-venv ninja-build \
    && rm -rf /var/lib/apt/lists/*

# Install COLMAP (build from source)
RUN git clone https://github.com/colmap/colmap.git /opt/colmap && \
    cd /opt/colmap && git submodule update --init --recursive && \
    mkdir build && cd build && \
    cmake .. -DCMAKE_BUILD_TYPE=Release && \
    make -j$(nproc) && make install && \
    cd / && rm -rf /opt/colmap

# Install OpenMVS (build from source)
RUN git clone https://github.com/cdcseacave/openMVS.git /opt/openMVS && \
    cd /opt/openMVS && git submodule update --init --recursive && \
    mkdir build && cd build && \
    cmake .. -DCMAKE_BUILD_TYPE=Release -DOpenMVS_USE_CUDA=ON && \
    make -j$(nproc) && make install && \
    cd / && rm -rf /opt/openMVS

# Python dependencies
COPY requirements.txt /workspace/requirements.txt
RUN python3 -m pip install --upgrade pip && pip install --no-cache-dir -r /workspace/requirements.txt

# Copy scripts
COPY handler.py /workspace/handler.py
COPY photogrammetry.sh /workspace/photogrammetry.sh
COPY utils.py /workspace/utils.py
RUN chmod +x /workspace/photogrammetry.sh

# Expose nothing; this is a serverless worker
CMD ["python3", "-u", "handler.py"]

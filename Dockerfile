# Dockerfile
FROM nvidia/cuda:11.8.0-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive

# --- Install dependencies ---
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    wget \
    unzip \
    ninja-build \
    libboost-all-dev \
    libeigen3-dev \
    libsuitesparse-dev \
    libfreeimage-dev \
    libgoogle-glog-dev \
    libgflags-dev \
    libglew-dev \
    qtbase5-dev \
    libqt5opengl5-dev \
    libopencv-dev \
    python3-dev \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# --- Build COLMAP ---
RUN git clone --recursive https://github.com/colmap/colmap.git /opt/colmap && \
    cd /opt/colmap && \
    mkdir build && cd build && \
    cmake .. -DCMAKE_BUILD_TYPE=Release -GNinja && \
    ninja && ninja install && \
    cd / && rm -rf /opt/colmap

# --- Install Python packages ---
RUN pip3 install --upgrade pip && \
    pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118 && \
    pip3 install "numpy<2" pillow

# --- Copy app ---
WORKDIR /app
COPY . /app

# --- Default command (RunPod will override if needed) ---
CMD ["python3", "app.py"]

# Copy FastAPI app
COPY app.py /app/app.py
WORKDIR /app

# Install FastAPI + Uvicorn + SendGrid
RUN pip install --no-cache-dir fastapi uvicorn python-multipart sendgrid

# Expose port for RunPod
EXPOSE 8000

# Start server
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]

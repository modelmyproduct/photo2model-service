# === Base image ===
FROM nvidia/cuda:11.8.0-devel-ubuntu22.04

# Avoid timezone prompts
ENV DEBIAN_FRONTEND=noninteractive

# === System dependencies ===
RUN apt-get update && apt-get install -y \
    git wget curl unzip build-essential \
    cmake ninja-build libboost-all-dev \
    libeigen3-dev libsuitesparse-dev \
    && rm -rf /var/lib/apt/lists/*

# === Python setup ===
RUN apt-get update && apt-get install -y python3 python3-pip && \
    python3 -m pip install --upgrade pip

# === Install COLMAP ===
RUN apt-get update && apt-get install -y wget cmake ninja-build build-essential git && \
    ( \
      echo "🔹 Trying to download prebuilt COLMAP binary..." && \
      wget -O colmap.tar.gz https://github.com/colmap/colmap/releases/download/3.9/colmap-3.9-linux.tar.gz && \
      tar -xvzf colmap.tar.gz && \
      mv colmap-3.9-linux /opt/colmap && \
      ln -s /opt/colmap/bin/colmap /usr/local/bin/colmap && \
      rm colmap.tar.gz \
    ) || ( \
      echo "⚠️ Prebuilt COLMAP not found, compiling from source..." && \
      git clone --recursive https://github.com/colmap/colmap.git /opt/colmap && \
      cd /opt/colmap && mkdir build && cd build && \
      cmake .. -GNinja -DCMAKE_BUILD_TYPE=Release && \
      ninja && ninja install \
    )

# === Python requirements ===
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# === Copy API code ===
COPY . /app

# === Expose FastAPI port ===
EXPOSE 8000

# === Run the API ===
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]

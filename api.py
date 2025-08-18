import os
import runpod
import subprocess
import shutil
import zipfile
from pathlib import Path

# === Directories inside container ===
UPLOAD_DIR = "/workspace/uploads"
OUTPUT_DIR = "/workspace/output"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

def run_colmap_pipeline(upload_path: str, output_path: str):
    """
    Runs COLMAP + gsplat on the uploaded images.
    For now this is simplified: it zips input images to mimic a 3D model.
    Later you can replace with the full photogrammetry pipeline.
    """
    # TODO: replace with your actual pipeline
    zip_path = os.path.join(output_path, "model.zip")
    with zipfile.ZipFile(zip_path, "w") as zf:
        for file in Path(upload_path).glob("*.jpg"):
            zf.write(file, file.name)
    return zip_path

def handler(job):
    """
    RunPod handler — executes per job request.
    """
    job_input = job["input"]

    # Get job ID for unique workspace
    job_id = job["id"]
    job_dir = os.path.join(UPLOAD_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)

    # === Download input images ===
    image_urls = job_input.get("images", [])
    if not image_urls:
        return {"error": "No images provided."}

    local_images = []
    for i, url in enumerate(image_urls):
        local_path = os.path.join(job_dir, f"image_{i}.jpg")
        subprocess.run(["curl", "-s", "-o", local_path, url], check=True)
        local_images.append(local_path)

    # === Run reconstruction ===
    result_path = run_colmap_pipeline(job_dir, OUTPUT_DIR)

    # === Return result ===
    return {
        "status": "success",
        "model_zip": result_path
    }

# Register handler with RunPod
runpod.serverless.start({"handler": handler})

import os
import shutil
import subprocess
import uuid
<<<<<<< HEAD
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse

# Make upload + output dirs
UPLOAD_DIR = "/app/uploads"
OUTPUT_DIR = "/app/outputs"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

app = FastAPI(title="Photo2Model API")

@app.post("/reconstruct")
async def reconstruct(files: list[UploadFile] = File(...)):
    """Takes multiple images -> returns reconstructed 3D model (zip)."""

    # Make unique run folder
    run_id = str(uuid.uuid4())
    run_input = os.path.join(UPLOAD_DIR, run_id)
    run_output = os.path.join(OUTPUT_DIR, run_id)
    os.makedirs(run_input, exist_ok=True)
    os.makedirs(run_output, exist_ok=True)

    # Save uploaded files
    for file in files:
        file_path = os.path.join(run_input, file.filename)
        with open(file_path, "wb") as f:
            f.write(await file.read())

    # Run COLMAP reconstruction
    try:
        subprocess.check_call([
            "colmap", "automatic_reconstructor",
            "--workspace_path", run_output,
            "--image_path", run_input,
            "--dense", "1"
        ])
    except subprocess.CalledProcessError as e:
        return {"error": f"COLMAP failed: {str(e)}"}

    # Zip results
    zip_path = f"{run_output}.zip"
    shutil.make_archive(run_output, "zip", run_output)

    return FileResponse(zip_path, media_type="application/zip", filename="model.zip")

@app.get("/")
async def root():
    return {"message": "Photo2Model API is running 🚀"}
=======
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse

app = FastAPI()

# Directory for processing
BASE_DIR = "/app/data"
os.makedirs(BASE_DIR, exist_ok=True)

@app.post("/process")
async def process_photos(files: list[UploadFile] = File(...)):
    """Accept multiple photos, run COLMAP, return a zip model."""
    # Unique job ID
    job_id = str(uuid.uuid4())
    job_dir = os.path.join(BASE_DIR, job_id)
    images_dir = os.path.join(job_dir, "images")
    os.makedirs(images_dir, exist_ok=True)

    # Save uploaded images
    for file in files:
        contents = await file.read()
        file_path = os.path.join(images_dir, file.filename)
        with open(file_path, "wb") as f:
            f.write(contents)

    # COLMAP working dirs
    sparse_dir = os.path.join(job_dir, "sparse")
    dense_dir = os.path.join(job_dir, "dense")
    os.makedirs(sparse_dir, exist_ok=True)
    os.makedirs(dense_dir, exist_ok=True)

    # Run COLMAP
    try:
        subprocess.check_call([
            "colmap", "automatic_reconstructor",
            "--workspace_path", job_dir,
            "--image_path", images_dir,
            "--sparse", sparse_dir,
            "--dense", dense_dir
        ])
    except subprocess.CalledProcessError as e:
        return {"error": f"COLMAP failed: {e}"}

    # Zip the result
    zip_path = os.path.join(BASE_DIR, f"{job_id}.zip")
    shutil.make_archive(zip_path.replace(".zip", ""), "zip", job_dir)

    return {"download_url": f"/download/{job_id}"}

@app.get("/download/{job_id}")
def download_result(job_id: str):
    """Download the generated 3D model ZIP."""
    zip_path = os.path.join(BASE_DIR, f"{job_id}.zip")
    if os.path.exists(zip_path):
        return FileResponse(zip_path, media_type="application/zip", filename=f"{job_id}.zip")
    return {"error": "File not found"}
>>>>>>> c13a868 (Clean Dockerfile, remove gsplat)

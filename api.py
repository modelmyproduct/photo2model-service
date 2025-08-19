import os
import shutil
import subprocess
import uuid
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

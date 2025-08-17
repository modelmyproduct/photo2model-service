import os
import runpod
import subprocess
import uuid
import shutil
from fastapi import FastAPI, UploadFile
from fastapi.responses import JSONResponse
from pathlib import Path

# === Setup FastAPI ===
app = FastAPI()

OUTPUT_DIR = "/workspace/output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# === Helper: run shell command ===
def run_cmd(cmd, cwd=None):
    process = subprocess.run(
        cmd, cwd=cwd, shell=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    if process.returncode != 0:
        raise RuntimeError(f"Command failed: {cmd}\n{process.stderr}")
    return process.stdout

# === API endpoint: upload photos ===
@app.post("/process")
async def process_photos(files: list[UploadFile]):
    job_id = str(uuid.uuid4())
    job_dir = Path(OUTPUT_DIR) / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    # Save uploaded photos
    image_dir = job_dir / "images"
    image_dir.mkdir()
    for file in files:
        contents = await file.read()
        with open(image_dir / file.filename, "wb") as f:
            f.write(contents)

    # === Run COLMAP reconstruction ===
    sparse_dir = job_dir / "sparse"
    dense_dir = job_dir / "dense"
    model_file = job_dir / "model.ply"

    try:
        # Feature extraction + matching
        run_cmd(f"colmap feature_extractor --database_path {job_dir}/db.db --image_path {image_dir}")
        run_cmd(f"colmap exhaustive_matcher --database_path {job_dir}/db.db")

        # Sparse reconstruction
        sparse_dir.mkdir()
        run_cmd(f"colmap mapper --database_path {job_dir}/db.db --image_path {image_dir} --output_path {sparse_dir}")

        # Dense reconstruction
        dense_dir.mkdir()
        run_cmd(f"colmap image_undistorter --image_path {image_dir} --input_path {sparse_dir}/0 --output_path {dense_dir} --output_type COLMAP --max_image_size 2000")
        run_cmd(f"colmap patch_match_stereo --workspace_path {dense_dir} --workspace_format COLMAP --PatchMatchStereo.geom_consistency true")
        run_cmd(f"colmap stereo_fusion --workspace_path {dense_dir} --workspace_format COLMAP --input_type geometric --output_path {model_file}")

        # Optional: Convert to glb (Meshroom/meshlabserver if installed)
        # run_cmd(f"meshlabserver -i {model_file} -o {job_dir}/model.glb")

    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)})

    return JSONResponse({
        "status": "success",
        "job_id": job_id,
        "download_url": f"/download/{job_id}"
    })

# === API endpoint: download model ===
@app.get("/download/{job_id}")
def download_model(job_id: str):
    model_path = Path(OUTPUT_DIR) / job_id / "model.ply"
    if not model_path.exists():
        return JSONResponse({"status": "error", "message": "Model not found"})
    return JSONResponse({
        "status": "ready",
        "file": str(model_path)
    })

# === RunPod handler ===
def handler(job):
    return {"message": "Use /process endpoint with photos."}

runpod.serverless.start({"handler": handler})

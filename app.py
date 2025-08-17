import os
import shutil
import subprocess
import tempfile
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse
import sendgrid
from sendgrid.helpers.mail import Mail
from typing import List

# === Config ===
OUTPUT_DIR = "/outputs"
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
SENDER_EMAIL = "modelmyproduct@gmail.com"  # Change if you want

os.makedirs(OUTPUT_DIR, exist_ok=True)

app = FastAPI(title="Photo2Model Service")

def run_command(cmd, cwd=None):
    """Helper to run shell commands and raise error if fail."""
    print("Running:", " ".join(cmd))
    subprocess.check_call(cmd, cwd=cwd)

@app.post("/process")
async def process_photos(
    files: List[UploadFile] = File(...),
    customer_email: str = Form(...)
):
    # Step 1. Save uploaded photos
    temp_dir = tempfile.mkdtemp()
    photos_dir = os.path.join(temp_dir, "images")
    os.makedirs(photos_dir, exist_ok=True)

    for i, file in enumerate(files):
        file_path = os.path.join(photos_dir, f"img_{i}.jpg")
        with open(file_path, "wb") as f:
            f.write(await file.read())

    # Step 2. Run COLMAP (SfM + MVS)
    sparse_dir = os.path.join(temp_dir, "sparse")
    dense_dir = os.path.join(temp_dir, "dense")
    os.makedirs(sparse_dir, exist_ok=True)
    os.makedirs(dense_dir, exist_ok=True)

    run_command(["colmap", "automatic_reconstructor",
                 "--workspace_path", temp_dir,
                 "--image_path", photos_dir,
                 "--dense", "1"])

    # Step 3. Run Gaussian Splatting (gsplat)
    model_out = os.path.join(OUTPUT_DIR, "model.ply")
    run_command(["python3", "-m", "gsplat.scripts.train",
                 "--data", dense_dir,
                 "--output", model_out])

    # Step 4. Email the result
    if SENDGRID_API_KEY:
        sg = sendgrid.SendGridAPIClient(SENDGRID_API_KEY)
        message = Mail(
            from_email=SENDER_EMAIL,
            to_emails=customer_email,
            subject="Your 3D Model is Ready",
            plain_text_content="Here is your 3D model!",
        )
        with open(model_out, "rb") as f:
            data = f.read()
        import base64
        message.add_attachment(
            base64.b64encode(data).decode(),
            "application/octet-stream",
            "model.ply",
            "attachment"
        )
        sg.send(message)

    return FileResponse(model_out, filename="model.ply")

# api.py
# Minimal, stable automated pipeline:
# - accepts multi-file upload + email
# - saves images to job folder
# - generates a small .glb placeholder model via trimesh (replaceable)
# - zips/attaches, splits if needed, and sends email via SendGrid

import os
import uuid
import shutil
import base64
from pathlib import Path
from typing import List

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition

import trimesh
import numpy as np

# -------- CONFIG via ENV VARS (set these in RunPod)
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "modelmyproduct@gmail.com")
SENDER_NAME = os.getenv("SENDER_NAME", "ModelMyProduct")
MAX_ATTACHMENT_MB = int(os.getenv("MAX_ATTACHMENT_MB", "18"))  # safe chunk size (~18MB -> after base64 ~24MB)

# -------- SERVER
app = FastAPI(title="Photo2Model - Email Attachments Service")

BASE_WORK = Path("/tmp/photo2model_jobs")
BASE_WORK.mkdir(parents=True, exist_ok=True)

# -------- helpers
def make_job_dirs(job_id: str) -> Path:
    d = BASE_WORK / job_id
    (d / "input").mkdir(parents=True, exist_ok=True)
    (d / "output").mkdir(parents=True, exist_ok=True)
    return d

def generate_placeholder_glb(output_path: Path):
    """
    Create a small glb using trimesh (a single textured cube).
    Replace the contents of this function with your real photogrammetry pipeline.
    """
    # create a colored box
    box = trimesh.creation.box(extents=(1.0, 1.0, 1.0))
    # add simple vertex colors
    colors = np.tile([200, 120, 80, 255], (len(box.vertices), 1))
    box.visual.vertex_colors = colors
    # export glb
    glb_bytes = trimesh.exchange.gltf.export_glb(box)
    output_path.write_bytes(glb_bytes)
    return output_path

def split_file(file_path: Path, chunk_mb: int) -> List[Path]:
    chunk_size = chunk_mb * 1024 * 1024
    parts = []
    with open(file_path, "rb") as f:
        idx = 1
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            part = file_path.with_name(f"{file_path.name}.part{idx:02d}")
            with open(part, "wb") as pf:
                pf.write(chunk)
            parts.append(part)
            idx += 1
    return parts

def send_email_with_attachments(to_email: str, subject: str, html: str, files: List[Path]):
    if not SENDGRID_API_KEY:
        raise RuntimeError("SENDGRID_API_KEY not set in environment.")

    message = Mail(
        from_email=(SENDER_EMAIL, SENDER_NAME),
        to_emails=to_email,
        subject=subject,
        html_content=html
    )

    for p in files:
        data = p.read_bytes()
        encoded = base64.b64encode(data).decode()
        att = Attachment()
        att.file_content = FileContent(encoded)
        att.file_type = FileType("application/octet-stream")
        att.file_name = FileName(p.name)
        att.disposition = Disposition("attachment")
        message.add_attachment(att)

    sg = SendGridAPIClient(SENDGRID_API_KEY)
    resp = sg.send(message)
    return resp.status_code

# -------- API endpoint
@app.post("/process")
async def process(email: str = Form(...), files: List[UploadFile] = File(...)):
    # Basic validation
    if not email:
        raise HTTPException(status_code=400, detail="Missing email.")
    if not files or len(files) < 3:
        # keep threshold small for early testing, recommended: 12+
        raise HTTPException(status_code=400, detail="Please upload at least 3 photos for testing (12+ recommended).")

    job_id = uuid.uuid4().hex[:8]
    job_dir = make_job_dirs(job_id)
    input_dir = job_dir / "input"
    output_dir = job_dir / "output"

    # Save uploaded files
    allowed = {".jpg", ".jpeg", ".png"}
    try:
        for i, upload in enumerate(files, start=1):
            ext = Path(upload.filename).suffix.lower()
            if ext not in allowed:
                raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")
            out = input_dir / f"{i:03d}{ext}"
            with open(out, "wb") as f:
                f.write(await upload.read())
    except Exception as e:
        shutil.rmtree(job_dir, ignore_errors=True)
        raise

    # Generate model (placeholder). Replace this call with your real pipeline later.
    try:
        model_glb = output_dir / "model.glb"
        generate_placeholder_glb(model_glb)
    except Exception as e:
        shutil.rmtree(job_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=f"Model generation failed: {e}")

    # If small enough, send single email
    size_mb = model_glb.stat().st_size / (1024*1024)
    attachments = []
    if size_mb <= MAX_ATTACHMENT_MB:
        attachments = [model_glb]
        subject = "Your 3D Model is Ready 🎉"
        html = "<p>Thanks — your 3D model is attached as <b>model.glb</b>.</p>"
        send_email_with_attachments(email, subject, html, attachments)
    else:
        # split into chunks and send multiple emails with part instructions
        parts = split_file(model_glb, MAX_ATTACHMENT_MB)
        total = len(parts)
        for idx, part in enumerate(parts, start=1):
            subject = f"Your 3D Model — Part {idx}/{total}"
            html = (
                f"<p>We split the model into {total} attachments. Download all parts, then concatenate:</p>"
                f"<pre>cat {model_glb.name}.part* > model_glb.zip</pre>"
                "<p>Unzip the file to get model.glb</p>"
            )
            send_email_with_attachments(email, subject, html, [part])

    # Cleanup and return
    shutil.rmtree(job_dir, ignore_errors=True)
    return JSONResponse({"status": "ok", "job_id": job_id, "message": "Email(s) sent with attachment(s)."})

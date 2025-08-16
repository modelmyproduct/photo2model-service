import os, json, subprocess, traceback
import runpod
import requests
from utils import new_job_dir, ensure_dir, download_images, zip_dir, upload_transfer_sh, clean_dir

# Handler input schema:
# {
#   "image_urls": [...],
#   "email": "customer@example.com",
#   "order_id": "ABC123",
#   "webhook_url": "https://bubbleapp.../api/1.1/wf/runpod_done",
#   "max_image_size": 2000
# }

def process(event):
    try:
        inp = event.get("input", {}) if isinstance(event, dict) else event
        image_urls = inp.get("image_urls") or []
        email = inp.get("email", "")
        order_id = inp.get("order_id", "")
        webhook_url = inp.get("webhook_url", "")
        max_image_size = int(inp.get("max_image_size", 2000))

        if len(image_urls) < 8:
            return {"ok": False, "error": "Need at least 8 image URLs.", "order_id": order_id}

        job_dir, job_id = new_job_dir()
        images_dir = os.path.join(job_dir, "images")
        output_dir = os.path.join(job_dir, "output")
        ensure_dir(output_dir)

        # 1) Download images
        download_images(image_urls, images_dir)

        # 2) Run photogrammetry script
        cmd = ["/workspace/photogrammetry.sh", job_dir, str(max_image_size)]
        run = subprocess.run(cmd, capture_output=True, text=True)
        logs = run.stdout + "\n" + run.stderr
        if run.returncode != 0:
            res = {"ok": False, "error": "Reconstruction failed", "logs": logs, "order_id": order_id}
            if webhook_url:
                try: requests.post(webhook_url, json=res, timeout=60)
                except Exception: pass
            return res

        # 3) Zip results
        zip_path = os.path.join(job_dir, "model.zip")
        zip_dir(output_dir, zip_path)

        # 4) Upload to transfer.sh
        download_url = upload_transfer_sh(zip_path)

        res = {
            "ok": True,
            "order_id": order_id,
            "email": email,
            "download_url": download_url
        }

        # 5) Notify webhook (Bubble), if provided
        if webhook_url:
            try:
                requests.post(webhook_url, json=res, timeout=60)
            except Exception:
                pass

        # Optional: clean to save disk
        # clean_dir(job_dir)

        return res

    except Exception as e:
        tr = traceback.format_exc()
        return {"ok": False, "error": str(e), "trace": tr}

def handler(event):
    # RunPod calls with {"input": {...}} sometimes, handle both
    payload = event.get("input", event) if isinstance(event, dict) else event
    return process(payload)

runpod.serverless.start({"handler": handler})

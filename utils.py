import os, zipfile, subprocess, requests, shutil, uuid

def ensure_dir(p):
    os.makedirs(p, exist_ok=True)
    return p

def download_images(urls, dst_dir):
    ensure_dir(dst_dir)
    out_paths = []
    for i, u in enumerate(urls):
        ext = os.path.splitext(u.split("?")[0])[-1].lower()
        if ext not in [".jpg", ".jpeg", ".png", ".tif", ".tiff"]:
            ext = ".jpg"
        p = os.path.join(dst_dir, f"img_{i:04d}{ext}")
        r = requests.get(u, timeout=300)
        r.raise_for_status()
        with open(p, "wb") as f:
            f.write(r.content)
        out_paths.append(p)
    return out_paths

def zip_dir(folder_path, zip_path):
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(folder_path):
            for fn in files:
                fp = os.path.join(root, fn)
                arc = os.path.relpath(fp, folder_path)
                zf.write(fp, arc)

def upload_transfer_sh(file_path):
    fname = os.path.basename(file_path)
    cmd = ["curl", "--silent", "--show-error", "--upload-file", file_path, f"https://transfer.sh/{fname}"]
    url = subprocess.check_output(cmd, text=True).strip()
    return url

def clean_dir(path):
    if os.path.exists(path):
        shutil.rmtree(path, ignore_errors=True)

def new_job_dir():
    jid = str(uuid.uuid4())
    base = os.path.join("/workspace", "jobs", jid)
    os.makedirs(base, exist_ok=True)
    return base, jid

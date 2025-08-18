import os
import subprocess
import shutil
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/process", methods=["POST"])
def process():
    try:
        # === 1. Prepare dirs ===
        input_dir = "/workspace/input"
        output_dir = "/workspace/output"
        os.makedirs(input_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)

        # Clear old runs
        shutil.rmtree(input_dir, ignore_errors=True)
        shutil.rmtree(output_dir, ignore_errors=True)
        os.makedirs(input_dir)
        os.makedirs(output_dir)

        # === 2. Save uploaded images ===
        files = request.files.getlist("files")
        for i, file in enumerate(files):
            file.save(os.path.join(input_dir, f"img_{i}.jpg"))

        # === 3. Run COLMAP automatic pipeline ===
        subprocess.run([
            "colmap", "automatic_reconstructor",
            "--image_path", input_dir,
            "--workspace_path", output_dir,
            "--dense", "1"
        ], check=True)

        # === 4. Zip result ===
        zip_path = "/workspace/model.zip"
        shutil.make_archive("/workspace/model", "zip", output_dir)

        # === 5. Return response ===
        return jsonify({"status": "success", "result": zip_path})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

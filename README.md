# photo2model-service

This repo builds a Docker image that runs COLMAP + OpenMVS and a small RunPod worker to generate textured 3D models from photos.

IMPORTANT: Replace placeholders (Docker Hub username, RunPod API keys) in the deployment steps below.

## Repo files
- Dockerfile
- requirements.txt
- photogrammetry.sh
- utils.py
- handler.py
- .github/workflows/build-and-push.yml

## Quick start (copy-paste)
1. Create a Docker Hub repo: `yourdockerhubusername/photo2model`
2. In GitHub repo settings -> Secrets -> add `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN`
3. Push this repo to GitHub main branch. GitHub Actions will build and push the image to Docker Hub.
4. In RunPod, create a Serverless endpoint using image `docker.io/PASTE_DOCKERHUB_USERNAME/photo2model:latest`.
5. In Bubble, create backend workflows and connect to RunPod start-job URL (see master plan).

## Placeholders to edit
- GitHub Actions uses secrets `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` (add these in repo Settings -> Secrets)
- In Bubble, use the RunPod Start Job URL and API Key from your RunPod dashboard.

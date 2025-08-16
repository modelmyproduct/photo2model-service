#!/usr/bin/env bash
set -euo pipefail

JOB_DIR="$1"
MAX_SIZE="${2:-2000}"

IMAGES_DIR="$JOB_DIR/images"
WORK_DIR="$JOB_DIR/work"
DB="$WORK_DIR/database.db"
SPARSE="$WORK_DIR/sparse"
UNDIST="$WORK_DIR/undistorted"
MVS="$WORK_DIR/mvs"
OUT="$JOB_DIR/output"

mkdir -p "$WORK_DIR" "$SPARSE" "$UNDIST" "$MVS" "$OUT"

echo "===> COLMAP: feature extraction"
colmap feature_extractor \
  --database_path "$DB" \
  --image_path "$IMAGES_DIR" \
  --SiftExtraction.use_gpu 1 \
  --SiftExtraction.gpu_index 0 \
  --SiftExtraction.max_image_size $MAX_SIZE

echo "===> COLMAP: exhaustive matcher"
colmap exhaustive_matcher --database_path "$DB" --SiftMatching.use_gpu 1 --SiftMatching.gpu_index 0

echo "===> COLMAP: mapper"
mkdir -p "$SPARSE"
colmap mapper \
  --database_path "$DB" \
  --image_path "$IMAGES_DIR" \
  --output_path "$SPARSE" \
  --Mapper.num_threads 16

MODEL_DIR=$(ls -1 "$SPARSE" | head -n 1)
if [ -z "$MODEL_DIR" ]; then
  echo "No sparse model created."
  exit 2
fi

echo "===> COLMAP: undistort"
colmap image_undistorter \
  --image_path "$IMAGES_DIR" \
  --input_path "$SPARSE/$MODEL_DIR" \
  --output_path "$UNDIST" \
  --max_image_size $MAX_SIZE

echo "===> OpenMVS: convert COLMAP -> MVS"
InterfaceCOLMAP -i "$UNDIST" -o "$MVS/scene.mvs"

echo "===> OpenMVS: densify"
DensifyPointCloud "$MVS/scene.mvs" -o "$MVS/scene_dense.mvs"

echo "===> OpenMVS: mesh reconstruction"
ReconstructMesh "$MVS/scene_dense.mvs" -o "$MVS/scene_dense_mesh.mvs" --remove-spurious 50

echo "===> OpenMVS: refine mesh"
RefineMesh "$MVS/scene_dense_mesh.mvs" -o "$MVS/scene_dense_mesh_refine.mvs" --scales 2

echo "===> OpenMVS: texture"
TextureMesh "$MVS/scene_dense_mesh_refine.mvs" -o "$MVS/textured.obj" --export-type obj

# Copy outputs
cp "$MVS/textured.obj" "$OUT/model.obj" || true
[ -f "$MVS/textured.mtl" ] && cp "$MVS/textured.mtl" "$OUT/model.mtl" || true
for t in "$MVS"/*.{png,jpg,jpeg,tif,tiff}; do
  [ -e "$t" ] || continue
  cp "$t" "$OUT/"
done

echo "===> Done"

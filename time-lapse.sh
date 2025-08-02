#!/usr/bin/env bash

set -euo pipefail

# Configuration
INTERVAL=60         # seconds between screenshots
DURATION=$((60 * 60))  # total time in seconds (e.g., 1 hour)
OUT_DIR="screenshots"
VIDEO_OUT="timelapse.mp4"

# Ensure dependencies are installed
command -v scrot >/dev/null || { echo "Install scrot"; exit 1; }
command -v ffmpeg >/dev/null || { echo "Install ffmpeg"; exit 1; }

# Create output dir
mkdir -p "$OUT_DIR"

echo "📸 Taking screenshots every $INTERVAL seconds for $DURATION seconds..."
for ((i = 0; i < DURATION; i += INTERVAL)); do
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    scrot "$OUT_DIR/screenshot_$TIMESTAMP.png"
    sleep "$INTERVAL"
done

echo "🎞️ Creating video..."
ffmpeg -framerate 30 -pattern_type glob -i "$OUT_DIR/screenshot_*.png" -c:v libx264 -pix_fmt yuv420p "$VIDEO_OUT"

echo "✅ Timelapse created: $VIDEO_OUT"


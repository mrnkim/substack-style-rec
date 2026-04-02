"""Download video files from YouTube for video segment embeddings.

Reads YouTube IDs from scripts/videos_metadata.csv and downloads each video
into backend/data/videos/ using yt-dlp.

Usage:
    pip install yt-dlp
    python download_videos.py
"""
import csv
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
CSV_PATH = SCRIPTS_DIR / "videos_metadata.csv"
OUTPUT_DIR = Path(__file__).resolve().parent / "data" / "videos"


def main():
    if not CSV_PATH.exists():
        print(f"ERROR: {CSV_PATH} not found")
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"Found {len(rows)} videos in {CSV_PATH}")

    for i, row in enumerate(rows, 1):
        yt_id = row.get("video_id", "").strip()
        title = row.get("title", "unknown").strip()
        if not yt_id:
            continue

        output_path = OUTPUT_DIR / f"{yt_id}.mp4"
        if output_path.exists():
            print(f"  [{i}/{len(rows)}] SKIP (exists): {title[:60]}")
            continue

        print(f"  [{i}/{len(rows)}] Downloading: {title[:60]} ...")
        url = f"https://www.youtube.com/watch?v={yt_id}"

        try:
            subprocess.run(
                [
                    "yt-dlp",
                    "--js-runtimes", "node",
                    "-f", "bestvideo[vcodec^=avc1][height<=720]+bestaudio[ext=m4a]/bestvideo[height<=720]+bestaudio/best[height<=720]",
                    "--merge-output-format", "mp4",
                    "--postprocessor-args", "ffmpeg:-c:v libx264 -crf 23 -preset fast",
                    "-o", str(output_path),
                    "--no-playlist",
                    url,
                ],
                check=True,
                timeout=600,
            )
            print(f"           OK: {output_path.name}")
        except subprocess.CalledProcessError as e:
            print(f"           FAILED: {e}")
        except subprocess.TimeoutExpired:
            print(f"           TIMEOUT after 600s")

    print(f"\nDone. Videos saved to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()

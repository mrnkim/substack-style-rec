"""Download video files from YouTube for Pixeltable pxt.Video embedding.

Downloads each video referenced in the Twelve Labs index to a local
directory. These files are then referenced by their local paths when
inserting into the Pixeltable `videos` table.

Uses the yt-dlp Python API directly (no subprocess).

Usage:
    uv run download_videos.py          # download 3 quick-start videos
    uv run download_videos.py --full   # download all 30 videos
"""

import argparse
import csv
import logging
import sys
from pathlib import Path

import yt_dlp

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

QUICK_YOUTUBE_IDS = {"sO4te2QNsHY", "ntPGl8UyIq4", "QpKypvDjiPM"}

SCRIPT_DIR = Path(__file__).resolve().parent
DOWNLOAD_DIR = SCRIPT_DIR / "video_files"
VIDEOS_CSV = SCRIPT_DIR.parent / "scripts" / "videos_metadata.csv"

YDL_OPTS = {
    "format": "bestvideo[ext=mp4][vcodec^=avc1]+bestaudio[ext=m4a]/best[ext=mp4]",
    "merge_output_format": "mp4",
    "noplaylist": True,
    "socket_timeout": 30,
    "quiet": True,
    "no_warnings": True,
}


def download_video(youtube_id: str, output_dir: Path) -> Path | None:
    """Download a single video from YouTube via yt-dlp Python API.

    Returns the path to the downloaded .mp4, or None on failure.
    Requests h264 codec to avoid ffmpeg issues with AV1.
    """
    output_path = output_dir / f"{youtube_id}.mp4"

    if output_path.exists() and output_path.stat().st_size > 0:
        logger.info("  Already downloaded: %s", output_path.name)
        return output_path

    url = f"https://www.youtube.com/watch?v={youtube_id}"
    opts = {**YDL_OPTS, "outtmpl": str(output_path)}

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])

        if output_path.exists() and output_path.stat().st_size > 0:
            size_mb = output_path.stat().st_size / 1e6
            logger.info("  Downloaded: %s (%.1f MB)", output_path.name, size_mb)
            return output_path

        logger.warning("  Download produced empty file for %s", youtube_id)
        return None

    except yt_dlp.utils.DownloadError as e:
        logger.warning("  Failed to download %s: %s", youtube_id, str(e)[:200])
        return None
    except Exception as e:
        logger.warning("  Error downloading %s: %s", youtube_id, e)
        return None


def main():
    parser = argparse.ArgumentParser(description="Download video files from YouTube")
    parser.add_argument("--full", action="store_true", help="Download all videos (slow)")
    args = parser.parse_args()

    if not VIDEOS_CSV.exists():
        logger.error("videos_metadata.csv not found at %s", VIDEOS_CSV)
        sys.exit(1)

    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

    with open(VIDEOS_CSV) as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    youtube_ids = [r["video_id"].strip() for r in rows if r.get("video_id")]
    if not args.full:
        youtube_ids = [yt_id for yt_id in youtube_ids if yt_id in QUICK_YOUTUBE_IDS]
        logger.info("Quick-start: downloading %d videos (pass --full for all)", len(youtube_ids))
    else:
        logger.info("Full mode: downloading %d videos", len(youtube_ids))

    success = 0
    failed = 0
    for i, yt_id in enumerate(youtube_ids, 1):
        logger.info("[%d/%d] Downloading %s ...", i, len(youtube_ids), yt_id)
        path = download_video(yt_id, DOWNLOAD_DIR)
        if path:
            success += 1
        else:
            failed += 1

    logger.info("\nDone: %d downloaded, %d failed", success, failed)

    downloaded = list(DOWNLOAD_DIR.glob("*.mp4"))
    logger.info("Video files in %s: %d", DOWNLOAD_DIR, len(downloaded))
    for vf in sorted(downloaded):
        logger.info("  %s (%.1f MB)", vf.name, vf.stat().st_size / 1e6)


if __name__ == "__main__":
    main()

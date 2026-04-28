"""Download video files from Cloudflare R2 for Pixeltable scene embedding.

Downloads each video referenced in the Twelve Labs index from a
Cloudflare R2 bucket. These files are then referenced by their local
paths when inserting into the Pixeltable `videos` table.

Usage:
    uv run download_videos.py          # download 3 quick-start videos
    uv run download_videos.py --full   # download all 25 videos
"""

import argparse
import logging
import sys
from pathlib import Path
from urllib.parse import quote

import httpx

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

QUICK_YOUTUBE_IDS = {"sO4te2QNsHY", "ntPGl8UyIq4", "QpKypvDjiPM"}

SCRIPT_DIR = Path(__file__).resolve().parent
DOWNLOAD_DIR = SCRIPT_DIR / "video_files"

R2_BASE_URL = "https://pub-3d90ba141b2a453d9ada94f279c78419.r2.dev"

# Mapping: YouTube ID → R2 filename
# Only the 25 videos that are in the Twelve Labs index.
YOUTUBE_TO_R2 = {
    "j9Qm6_lEdcQ": "Dakota Johnson Is Not Okay While Eating Spicy Wings ｜ Hot Ones.webm",
    "5DDB_DNWGYE": "KPop Demon Hunters ｜ Hot Ones Versus.webm",
    "d5uhih_I7Jw": "Madison Beer Lives Out Her Dream While Eating Spicy Wings ｜ Hot Ones.webm",
    "sO4te2QNsHY": "What Is Branding 4 Minute Crash Course.mp4",
    "d18ud-4epP8": "Why the Biggest YouTube Family Just Went to Netflix： Jordan Matter.webm",
    "WcHWQnoE95w": "Why You Don't Trust Tap Water.mp4",
    "WYQxG4KEzvo": "The Problem With Elon Musk.mp4",
    "jITKnb0tYaM": "How to legislate AI.webm",
    "_Ux13UEqIYo": "Yikes.webm",
    "shB7wRZ2h5Y": "Are We Really Ready for AI Coding？.mp4",
    "ntPGl8UyIq4": "The Metaverse Only Has 900 Users.webm",
    "TBDWomgRgWU": "How smooth jazz took over the '90s.webm",
    "8A1Aj1_EF9Y": "The sound that connects Stravinsky to Bruno Mars.mp4",
    "QpKypvDjiPM": "Why more pop songs should end with a fade out.mp4",
    "j4KlMiMgVLM": "30 years fine-tuning micro-homestead oasis nothing missing little extra.webm",
    "dG2b_Klf5R4": "Couples traditional underground home hides in magical Nordic forest.webm",
    "LPUMrjwJgGs": "Nordic homestead near Russian border couples no-bank no-phone life.mp4",
    "wjZofJX0v4M": "Transformers, the tech behind LLMs ｜ Deep Learning Chapter 5.mp4",
    "IQqtsm-bBRU": "This open problem taught me what topology is.webm",
    "BHdbsHFs2P0": "The Hairy Ball Theorem.webm",
    "RRHU-fvsNo0": "5 Rules That Will Change Your Life Immediately.mp4",
    "AjwaE0WozfE": "Do THIS to Boost Your Metabolism, Lose Fat, & Feel Better Now With Dr. William Li.webm",
    "XhBp6GZzH6k": "How To Handle Difficult People & Take Back Your Peace and Power.mp4",
    "LB01v___wO4": "BTS： The ARIRANG Interview with Zane Lowe ｜ Apple Music.mp4",
    "jV_RuCyRCjs": "Olivia Dean： On Recent Success, The Art of Loving, and Being Vulnerable ｜ Zane Lowe Interview.mp4",
}


def download_video(youtube_id: str, output_dir: Path) -> Path | None:
    """Download a single video from R2.

    Returns the path to the downloaded file, or None on failure.
    """
    r2_filename = YOUTUBE_TO_R2.get(youtube_id)
    if not r2_filename:
        logger.warning("  No R2 mapping for YouTube ID %s", youtube_id)
        return None

    ext = Path(r2_filename).suffix
    output_path = output_dir / f"{youtube_id}{ext}"

    if output_path.exists() and output_path.stat().st_size > 0:
        logger.info("  Already downloaded: %s", output_path.name)
        return output_path

    url = f"{R2_BASE_URL}/{quote(r2_filename)}"

    try:
        with httpx.stream("GET", url, follow_redirects=True, timeout=300.0) as resp:
            resp.raise_for_status()
            with open(output_path, "wb") as f:
                for chunk in resp.iter_bytes(chunk_size=8192):
                    f.write(chunk)

        if output_path.exists() and output_path.stat().st_size > 0:
            size_mb = output_path.stat().st_size / 1e6
            logger.info("  Downloaded: %s (%.1f MB)", output_path.name, size_mb)
            return output_path

        logger.warning("  Download produced empty file for %s", youtube_id)
        return None

    except Exception as e:
        logger.warning("  Failed to download %s: %s", youtube_id, str(e)[:200])
        if output_path.exists():
            output_path.unlink()
        return None


def main():
    parser = argparse.ArgumentParser(description="Download video files from R2")
    parser.add_argument("--full", action="store_true", help="Download all 25 videos")
    args = parser.parse_args()

    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

    youtube_ids = list(YOUTUBE_TO_R2.keys())
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

    downloaded = list(DOWNLOAD_DIR.glob("*.*"))
    logger.info("Video files in %s: %d", DOWNLOAD_DIR, len(downloaded))
    for vf in sorted(downloaded):
        logger.info("  %s (%.1f MB)", vf.name, vf.stat().st_size / 1e6)


if __name__ == "__main__":
    main()

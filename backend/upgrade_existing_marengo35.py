"""Rebuild the two embedding indexes of an existing database with Marengo 3.5.

This is for the migrated 0.6.x database that uses app_existing.py, with indexes
named title_marengo and scene_marengo. Run migrate_existing.py first.

By default the script only prints the plan. Pass --apply to drop the two indexes
and build them again with Marengo 3.5. Rows, Analyze tags, scene cuts, and scene
clips are kept. The script refuses any other schema change.

Search and recommendations cannot use the scene index while it is rebuilt, so run
--apply in a maintenance window. You can run the script again if it stops partway.
"""

import argparse
import os
import time
from pathlib import Path

# Each table may only rebuild its one named index.
EXPECTED_INDEX = {"videos": "title_marengo", "video_scenes": "scene_marengo"}


def validate_plan(diffs) -> bool:
    """Return True if there is work to do, and False if the database is already on Marengo 3.5.

    Raise RuntimeError for any change other than rebuilding title_marengo and scene_marengo.
    A table may show "drop and add" (normal) or only "add" (a rerun after a stopped build).
    """
    if set(diffs) != {"creators", "videos", "video_scenes"}:
        raise RuntimeError("Expected the complete existing application schema")
    work = False
    for name, diff in diffs.items():
        if not diff.exists:
            raise RuntimeError(f"Refusing: table {name} does not exist")
        if diff.resolution == "up_to_date" and not diff.ops:
            continue
        if name not in EXPECTED_INDEX or diff.resolution not in {"update_destructive", "update_additive"}:
            raise RuntimeError(f"Refusing unexpected change to {name}: {diff.resolution}")
        index = EXPECTED_INDEX[name]
        ops = {(op.target, op.op, op.name) for op in diff.ops}
        if ops not in ({("index", "drop", index), ("index", "add", index)}, {("index", "add", index)}):
            raise RuntimeError(f"Refusing unexpected schema operations on {name}: {sorted(ops)}")
        work = True
    return work


def report(pxt, namespace: str) -> None:
    scenes = pxt.get_table(f"{namespace}.video_scenes")
    videos = pxt.get_table(f"{namespace}.videos")
    vecs = [r["e"] for r in scenes.select(e=scenes.video_segment.embedding(idx="scene_marengo")).collect()]
    missing = sum(v is None for v in vecs)
    print(f"videos: {videos.count()}  scene clips: {len(vecs)}  clips without a vector: {missing}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--home", type=Path, required=True, help="Explicit Pixeltable home")
    parser.add_argument("--apply", action="store_true", help="Drop and rebuild the two indexes with Marengo 3.5")
    parser.add_argument(
        "--max-buffered-rows",
        type=int,
        default=64,
        help="Rows Pixeltable works on at once (default 64). Lower it only if memory runs out; "
        "values below 64 can stall.",
    )
    args = parser.parse_args()
    home = args.home.resolve()
    if not (home / "pgdata" / "PG_VERSION").is_file():
        parser.error("--home must contain an existing pgdata/PG_VERSION")

    # config loads dotenv with override=True; pin the explicit target afterwards.
    import config

    os.environ["PIXELTABLE_HOME"] = str(home)

    # Pixeltable's default buffer (2048 rows) ran the Render box out of memory on the
    # last scene index build. Cap it before any query runs.
    from pixeltable.exec.expr_eval.expr_eval_node import ExprEvalNode

    ExprEvalNode.MAX_BUFFERED_ROWS = args.max_buffered_rows

    import pixeltable as pxt
    from pixeltable.config import Config

    import app_existing_marengo35

    pxt.list_dirs()
    if Config.get().home.resolve() != home:
        raise RuntimeError(f"Pixeltable opened {Config.get().home}, not {home}")
    print(f"Target: {home}; namespace: {config.APP_NAMESPACE}; pixeltable {pxt.__version__}")

    base = app_existing_marengo35.TableModel
    if not validate_plan(base.get_model_diff(config.APP_NAMESPACE)):
        print("Both indexes already use Marengo 3.5. Nothing to do.")
        report(pxt, config.APP_NAMESPACE)
        return
    base.diff_all(config.APP_NAMESPACE)
    if not args.apply:
        print("Dry run only. Pass --apply after confirming the backup and the maintenance window.")
        return

    start = time.time()
    base.update_all(config.APP_NAMESPACE, allow_destructive=True)
    remaining = base.get_model_diff(config.APP_NAMESPACE)
    if any(d.resolution != "up_to_date" for d in remaining.values()):
        raise RuntimeError("Index rebuild incomplete. Run the script again.")
    print(f"Rebuilt title_marengo and scene_marengo with Marengo 3.5 in {time.time() - start:.0f} s.")
    report(pxt, config.APP_NAMESPACE)


if __name__ == "__main__":
    main()

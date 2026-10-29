# PR #18: Existing Database Compatibility Test

Tested on 2026-10-27 against PR head `67abbdf`, with the local zero-score
recommendation fix on branch `fix/pr18-zero-score`.

## Isolation

- Production access was limited to a read-only inventory and `pg_dump`.
- No production restart, schema update, data load, file deletion, or ownership
  change was performed.
- The dump was restored into two local databases under
  `/tmp/pr18-production-home`: `pr18_baseline` (unmodified metadata) and
  `pixeltable` (opened by Pixeltable 0.7.18).
- Provider credentials were not copied. Recommendation tests blocked text/title
  fallbacks, so they could only succeed using stored scene vectors.
- Video/media files were not copied. This tests existing-data/vector serving,
  not playback, new uploads, Analyze, or re-embedding.

## Results

- Backend regression tests: 7 passed, including 3 new zero/missing-score tests.
- Opening the restored database upgraded its metadata from version 50 to 56.
- Preserved 10 creators, 25 videos, and 476 scene rows.
- All physical creator/video/scene rows, including stored vectors, were identical
  between the baseline and upgraded databases after opening and querying.
- 365 of 476 scene vectors were non-null. The 111 missing vectors already
  existed in the production snapshot; they were not caused by the upgrade.
- Similar recommendations passed for 24 of 25 videos without provider fallback.
  Each returned 8 recommendations, excluded the reference video, and had positive
  scores. Local function timings were approximately 0.065-0.222 seconds;
  these are not production HTTP latency measurements.
- Video `69c381f654ac9ecced9ced11` has one scene and no stored vector. Its
  video-to-video path cannot be verified successfully without repairing existing
  embeddings. Actual provider fallback was intentionally not exercised.
- For You with watch history returned 10 recommendations using stored vectors.
- Creator catalog with watch history returned 3 recommended and 3 popular videos.

## Original Blocker: Declarative Schema Conversion

`app.TableModel.diff_all('substack_rec')` against the upgraded copy reports:

- `has_default_idxs`: existing `True`, model `False`, for all three models.
- Incompatible computed-column types: untyped JSON becomes typed JSON for
  `raw_attributes` and `scenes`; `topic`, `style`, and `tone` also change types.
- Changed computed expressions, including the new Analyze UDF.
- The model would add a new scene embedding index and drop `scene_marengo`.

The diff labels table/column incompatibilities `FATAL`. No schema update was
applied. Successful package/metadata upgrade and vector queries do NOT establish
that the new declarative schema can be applied in place.

Before production rollout, provide and test a non-destructive schema migration,
or build the new schema in a separate namespace with a deliberate cutover plan.
Do not run `--drop-dir`, drop the existing index, or re-embed production data as
an implicit part of this upgrade. Those require a separate approved plan.

## Compatibility Migration: Resolved on the Copy

`backend/app_existing.py` is a separate class-based schema for existing 0.6.x
databases. Fresh installations continue to use `app.py`. The compatibility
schema intentionally keeps the original JSON types, `has_default_idxs=True`,
and named `title_marengo` / `scene_marengo` indexes. It retains the original
Marengo embedding function, rather than replacing it with the retry UDF and
implicitly re-embedding all scenes. Future re-embedding is a separate task.

`backend/migrate_existing.py` requires an explicit existing home, defaults to a
plan-only run, and refuses missing tables, incompatible types, index changes,
column additions, or removals. Its apply mode uses the SDK's non-destructive
schema update: computed expressions are updated without recomputing their
stored values. Existing Analyze attributes remain unchanged; future rows use
the new Analyze function with a compatibility JSON cast.

Verified on `/tmp/pr18-production-home`, not production:

- Migration succeeded; all three compatibility models report `up_to_date`.
- Repeating migration/schema update is a no-op, including the actual CLI:
  `pxt schema update app_existing.py substack_rec`.
- All physical stored rows and vectors still exactly match `pr18_baseline`.
- FastAPI TestClient: Similar returned 8 positive recommendations for all 24
  videos with stored vectors, with text/title fallback blocked.
- For You returned 10; creator catalog returned HTTP 200; CORS headers passed.
- Local in-process Similar request times were 0.060-0.148 seconds. These are not
  Render performance measurements.
- Ten unit tests passed, including migration refusal cases and zero-score cases.
- Repeated data equality, HTTP recommendation/CORS checks, and all ten unit
  tests on Python 3.13.3 as well as Python 3.14.6. Python 3.13 matches the Docker
  image's minor version, but macOS does not reproduce the Linux container.
- Production PostgreSQL major version was read-only checked as 16, matching the
  local restore server. No production schema changes or restart were performed.

## Merge and Deployment Decision

The original schema-conversion blocker is resolved **with these compatibility
changes**, not by merging PR #18 unchanged. Use `app_existing.py` for an existing
database, never the fresh-install `app.py` schema-update/load procedure.

Before deployment:

1. Include the zero-score fix, compatibility schema, migration tool, and tests.
2. Keep an offline backup of the complete production home and a database dump.
   Restore the backup to roll back; older Pixeltable cannot safely open upgraded
   metadata. A dump alone does not back up media files.
3. Rehearse on a separate Render service/disk with the production Docker image,
   Python 3.13, and provider credentials before changing the live service.
4. Verify live Similar/For You, text search, playback, cold-start memory, and the
   missing-vector video's provider fallback. These were not established by this
   local, credential-free test. Do not claim every video uses video-to-video.
5. Only after approval, upgrade production and run the compatibility migration
   against its explicitly selected home. Do not reload data or replace indexes.

PR head was rechecked as `67abbdf`, OPEN and MERGEABLE. Its Vercel status still
fails with an authorization URL; this is not evidence of a successful frontend
build. The fixes in this report are local and have not been added to the PR.

No merge, push, deployment, production migration, or missing-vector repair was
performed. This validates the existing-data migration path, not a complete
production rollout or the provider-dependent new-ingestion path.

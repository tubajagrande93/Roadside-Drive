# Preservation and Invariants

## Verified protected paths / privacy categories

Preserve observed `apps/unreal/RoadsideDrive/`, `.env`, `.venv/`, `assets/`, `data/`, `pyproject.toml`, `uv.lock`, `.python-version`, `.gitattributes` and original root `.gitignore`. Saved, Intermediate, DerivedDataCache and geographic cache/processed directories are local. Keep secrets and private payloads out of scans and reports.

## Dirty/untracked/ignored state protection

Capture actual status and hashes for existing source under edit or at risk. Stage an explicit allowlist. Treat untracked source as user work and ignored data as irreplaceable until verified. Preserve nested instructions and symlink targets.

## Canonical data/state ownership

The Unreal descriptor owns engine association and project plugin settings. DefaultGame.ini owns the recorded ProjectID. Engine default config owns the configured map. uv.lock resolves the Python dependency declaration. Geographic writer and persistence are TO_VERIFY.

## No destructive Git / migrations / deploys

Never reset hard, clean, auto-stash, rewrite history, force push or migrate without authorization. Work in an authorized isolated checkout only when needed, otherwise scope edits tightly.

## Negative controls / no hidden behavior changes

Compare before/after bytes of existing files and exercise out-of-root paths, dirty fixtures, stale SHA and malformed evidence. Generated evidence belongs under output/agentops.

## Project-specific invariants with source anchors

Preserve existing ProjectID in `Config/DefaultGame.ini`, engine association in `RoadsideDrive.uproject`, and LFS filters in `.gitattributes`. Future metric conventions require source and native validation.

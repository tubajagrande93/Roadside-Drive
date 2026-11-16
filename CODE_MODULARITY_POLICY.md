# Roadside Drive — Permanent Code Modularity Policy

**Policy ID:** RD-ARCH-001 · **Status:** OPERATOR-APPROVED / STANDING · **Applies to:** all new and resumed Codex, Cline and other coding-agent sessions that load this repository.

**Startup binding:** The root [AGENTS.md](AGENTS.md) instructs an agent to read this document before adding, extending or refactoring hand-maintained source. A fresh session must verify the actual current Git branch/HEAD and source layout first. The [GRAND_MASTER.md](GRAND_MASTER.md) records the durable decision; this file owns the actionable modularity thresholds. Do not create a competing policy.

## 1. Goal and hard boundaries

Prevent large, multi-responsibility files and context-heavy changes **before** they become difficult for developers or coding agents to reason about. Prefer cohesive modules with explicit interfaces, stable ownership, and narrowly scoped edits. Smaller files are **not** automatically faster at runtime; performance of Unreal scenes depends on actual measured rendering, loading, geometry and simulation behavior.

This policy is **proactive on any relevant edit**, not a request to refactor the whole repository immediately. Preserve user work, public interfaces, Unreal assets, object IDs, geographic source/correction/generated separation, and the UAOS-B1 source-first / non-destructive rules. A numerical threshold never authorizes destructive or unrelated rewrites.

## 2. Thresholds — hand-maintained production code

| Current file size | Required response |
| --- | --- |
| 0–400 physical lines | Preferred zone; do not fragment cohesive code just to reduce size. |
| 401–600 lines | Soft review: inspect single responsibility, dependency direction, largest functions, and likely growth. New features may proceed if cohesive. |
| 601–800 lines | Active refactor candidate: identify ownership seams **before** adding a meaningful new feature. Extract the growing responsibility when safely separable; otherwise record the justification and next trigger. |
| More than 800 lines | **Hard growth gate.** Do not add substantial functionality to the same file until it has been split, or record a narrowly justified exception tied to source evidence and a bounded follow-up. Do not disguise growth by reformatting or removing checks. |

These thresholds apply to non-generated Python (\`.py\`), C/C++ (\`.c\`, \`.cc\`, \`.cpp\`, \`.h\`, \`.hpp\`) and analogous hand-maintained application source. Use physical line counts consistently; additional function complexity, responsibility overlap or large diffs can trigger earlier separation even under 400 lines.

**Hand-maintained test files:** soft review at 800 lines; hard growth gate above 1,200 lines. Split tests by behavior/domain while preserving fixtures and actual assertions.

**Do not line-limit or manually split** dependency lockfiles (\`uv.lock\`), generated files, third-party/vendor sources, Unreal \`.uasset\`/\`.umap\` binaries, serialized scenes, geographic data, static datasets, config files, embedded large assets or generated schemas. Review their size through appropriate storage/performance measures instead.

## 3. Required agent behavior before a relevant source edit

1. Inspect the *live* file, its direct callers/consumers, tests and Git status. Never rely on an old line count or invented source owner.
2. Determine whether the proposed change adds a **new responsibility** or expands the file's established responsibility.
3. Review size thresholds, dependency direction, public interfaces, persistence semantics, and how a new session will locate the code through Context Shark.
4. If splitting: identify existing cohesive functions/classes and extract into clearly named modules **within the actual package structure**. Keep an explicit entry-point/facade when consumers depend on the old import path. Fix imports deliberately and prevent circular dependencies.
5. Use the narrowest meaningful verification: import/syntax or existing targeted tests; for Unreal runtime changes, a relevant native/editor smoke test when feasible. Report \`NOT_RUN\` without calling it \`PASS\` or \`FAIL\`. Do not launch unrelated 24-test suites for a documentation-only change.
6. Record a short architecture note only when ownership or a durable boundary actually changes. Checkpoint and push under the existing standing GitHub publication rules.

**Priority:** Architecture-first, fast visible functionality, proportional validation. Do not create unnecessary abstraction scaffolding or dozens of microfiles.

## 4. Roadside Drive ownership guidelines

For the *actual* World Builder implementation, maintain clean responsibility boundaries between:

- **Source acquisition / licensing / provenance** — bounded OpenStreetMap ingestion, acquisition record, raw snapshots.
- **Coordinate systems** — WGS84/projection, fixed local origin, metres-to-Unreal-centimetres, axis convention.
- **Road geometry / topology** — road centerlines, junction connectivity, widths, carriageway meshes.
- **Buildings** — footprints, elevations/placeholders, mesh generation.
- **Terrain / floor** — elevation evidence, floor/road classification, designated spectator floor samples.
- **Corrections / identity** — stable IDs, source hash, non-destructive overlays, stale/conflicting patch detection.
- **ScenePackage / export** — validated catalogs/manifests, serializer(s), artifact hashes, deterministic outputs.
- **Unreal import / runtime** — editor import, placement, materials and collision, runtime spectator and inspector.

Do **not** infer that each list item requires its own file today. Split only when the actual implementations justify it. Keep the canonical writer and ownership direction explicit.

**Observed review candidates at Gate 01 (examples, not permanent locations or mandates):**
\`src/roadside_drive/world/exports.py\` (scene assembly versus serialization/validation),
\`pipelines/unreal/import_world.py\` (import logic versus actor/runtime behavior),
\`tools/agentops_repo.py\` (repository access versus policy/validation),
\`tools/agentops_state.py\` (checkpoint persistence versus publication/reporting).
Verify their existence and actual line counts against the checked-out branch before any action.

Preserve \`SOURCE → CORRECTIONS → GENERATED\`, source provenance, metric precision, object IDs and replayability through all extractions.

## 5. Unreal-specific measures (not line counts)

Blueprints use graphs/components, not source lines. Review oversized Event Graphs, unrelated responsibility clusters, expensive Event Tick logic, cross-component coupling and overgrown widget controllers. Put spectator movement, floor sampling, inspection, vehicle physics and map generation in appropriately separate components/owners. A Spectator with floor-only collision must not change future vehicle collision rules.

For large worlds, separate data by bounded geographic regions and support selective regeneration/streaming **when the measured scale warrants it**. Do not split an intersection or geographic feature across files/tiles in a way that breaks stable identity, topology, provenance or user corrections. Investigate actor counts, meshes, draw calls, texture footprint, loading and actual frame time rather than assuming source line count controls FPS.

## 6. Lightweight monitoring — no major QA bureaucracy

Before extending a source file near the soft threshold, use a narrow line-count inspection of relevant **tracked, hand-maintained** files (e.g. \`wc -l\` on explicit paths or a small stdlib scanner). Optionally implement a read-only, changed-file-scoped report in AgentOps later; **no new global packages or mandatory heavyweight CI** are required for this policy.

A useful report states: \`PATH | LINES | PRIMARY_OWNER | CHANGE_SCOPE | ACTION: KEEP / REVIEW / EXTRACT / EXCEPTION\`.

- Existing oversized untouched files are **not** automatic failures. Review them when they are actively modified.
- Crossing 600 lines calls for an architectural decision, not an automatic rewrite.
- At 800+ production lines, do not keep appending features without a safe split or a recorded, evidence-based exception.
- Do not auto-edit user data, rewrite Git history, or split source blindly.
- Record tests actually executed, unexecuted checks and regressions honestly; unexecuted optional tests alone do not mean implementation failure.

## 7. Cold-start and concurrency contract

On each **new** task or Codex/chat session with repository access:
\`AGENTS.md → current-state/agent rules → this policy before code edits → Context Shark targeted source → implement → scoped checks → checkpoint/handoff\`.

If the agent is working on an older feature branch, it must **fetch and reconcile** the latest remote policy through its normal, non-destructive branch workflow before materially changing code. Do not assume a newly committed file on \`main\` magically appears in an already checked-out older branch or an active agent session.

**Do not** interrupt another agent's uncommitted work, force-push, reset, clean or replace protected source. If policy adoption and a concurrent feature branch conflict, record the divergence and integrate the policy through the next safe merge/checkpoint.

**Operator acceptance** remains separate from implementation and automated verification. Code splitting is a maintainability operation; never claim it improves runtime speed without measured evidence.

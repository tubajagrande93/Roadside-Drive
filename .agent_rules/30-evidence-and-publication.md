# Evidence and Publication

## Report status vocabulary

COMPLETE_VERIFIED means task-owned gates passed. PARTIAL retains unclosed work. INTERRUPTED is a session boundary. BLOCKED needs a stated external condition. CHECKPOINT is an interim handoff. Operator acceptance is independently PENDING absent sign-off.

## Source branch vs remote verified equality

Record exact commit, ref and observed remote result. A local commit, matching remote tip, QA result and operator acceptance are distinct gates.

## Separate handoff branch and worktree

Remote handoff publication is optional and currently unconfigured. With separate authorization use an isolated worktree with only AgentOutput/{README.md,LATEST.md,INDEX.md,history/}. Fetch and verify tip and report bytes independently after a normal push.

## LATEST / INDEX / immutable history

Local reports store timestamped immutable history and mutable LATEST and INDEX under output/agentops/handoff. History is authoritative for recovery. Each write uses a same-directory temporary file. A shared lock serializes writers.

## Concurrent publish and no-force resolution

After a remote rejection preserve the attempt and bytes, fetch a fresh authorized output checkout, replay only the report over latest immutable history and retry normally. Older evidence may enter INDEX but must not replace newer LATEST.

## Local fallback / HANDOFF_NOT_PUBLISHED

Local-only output records REMOTE_UNAVAILABLE_OR_UNAUTHORIZED. Retry only after the output ref and isolated publication path are explicitly authorized. A clone elsewhere can read tracked routing only.

## Secrets and private data exclusions

Use repository-relative paths, redacted diagnostics and command metadata. Exclude secrets, home paths, private payloads and generated trees. Keep detailed evidence local.

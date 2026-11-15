# Evidence and Publication

## Standing repository authority

The operator authorizes verified development and routine publication to the canonical origin, `https://github.com/tubajagrande93/Roadside-Drive.git`. Routine commits, pushes, development branches and verified fast-forward integration need no separate approval. Define the product task and its scope before editing. Releases, deployment, paid services, destructive operations and publication of sensitive or unlicensed material need their own authorization.

## Source checkpoint and remote equality

At each meaningful completed phase run its quality gates, inspect an explicit staged allowlist, commit with the repository-configured GitHub noreply address for both identities, and push. Use `main` for completed integration-ready changes. Use a dedicated `codex/` development branch for experiments, higher-risk changes or incomplete work, marked PARTIAL or BLOCKED in evidence. Publish useful partial commits there after safety checks. Compare the advertised remote tip and ancestry before pushing or integrating. Use normal fast-forwards. Preserve concurrent work, existing refs and history. Verify the remote SHA independently after push. Report ref, local and remote SHA, executed tests, remaining gates and one next action.

## Separate handoff branch and worktree

Publish a sanitized checkpoint summary to the permanently authorized `agent-output` ref for each source checkpoint. Read [public LATEST](https://github.com/tubajagrande93/Roadside-Drive/blob/agent-output/AgentOutput/LATEST.md) for GitHub-only continuation. The public branch contains only `AgentOutput/README.md`, `AgentOutput/LATEST.md`, `AgentOutput/INDEX.md` and `AgentOutput/history/*.md`. Its first commit starts on an orphan branch in a disposable isolated worktree. For subsequent publications query the remote ref, fetch it, then use `git worktree add --detach` at the observed output tip. Never merge output history into source. Stage only the new immutable history file and updated pointers. Verify the complete tree allowlist and compare remote ref and published blob IDs independently after push.

## Immutable history and concurrent publication

Use a unique UTC name plus task ID and source SHA for each immutable report. Append its index entry and update LATEST only if it is the newest checkpoint. After a rejected push preserve the draft, fetch the observed winner into a fresh detached output worktree, carry forward all existing history, and retry normally. If there is a name collision, keep the prior file byte-for-byte and choose another name for the new report. Confirm source worktree preservation before removing the clean temporary worktree.

## Report status and local fallback

COMPLETE_VERIFIED means task-owned gates passed. PARTIAL retains unclosed work. INTERRUPTED is a session boundary. BLOCKED names an external condition. CHECKPOINT marks an interim report. Operator acceptance is PENDING until sign-off. Record executed commands, exit codes and source SHA. Keep the unabridged local checkpoint and AgentOps report in ignored storage. The `report` command stages local evidence only. If remote publication is blocked, record HANDOFF_NOT_PUBLISHED and the exact retry action, and preserve the local draft.

## Public content and Git LFS

Write public summaries from verified facts and safe relative references. Exclude credentials, private paths, personal data, raw logs, local environments, generated caches, unauthorized proprietary datasets and third-party assets. Check license, repository capacity and LFS attributes before publishing large assets. Attach full logs and private inputs only to local evidence. Public history records source publication separately from the handoff branch’s independent equality check.

<!-- AGENTOPS:BEGIN -->
## Repository Agent Operating Contract (UAOS-B1)

Newest explicit operator authorization controls scope. Live source, Git and observed runtime control facts. Approved durable invariants guide intended behavior. Preserve unmanaged and nearest applicable child instructions. Stop the affected change if an instruction or ownership conflict remains unresolved.

1. Run `python3 tools/agentops.py doctor --json` and inspect actual Git branch, HEAD, upstream, status (including ignored categories), and protected changes.
2. Read the five files under [.agent_rules](.agent_rules) in numeric order and [_agent_context/CURRENT_STATE.md](_agent_context/CURRENT_STATE.md).
3. Read [_agent_state/CURRENT_TASK_CHECKPOINT.md](_agent_state/CURRENT_TASK_CHECKPOINT.md) and [local LATEST](output/agentops/handoff/LATEST.md) if present. ACTIVE, INTERRUPTED and PARTIAL require the same authorized task and matching live source before resuming its NEXT_EXACT_ACTION. Missing or COMPLETE checkpoint means NEW_TASK unless the operator specifies otherwise. Stale or BLOCKED state requires verification.
4. Pick the relevant anchors from [_agent_context/GRAND_MASTER_INDEX.md](_agent_context/GRAND_MASTER_INDEX.md). Run `python3 tools/agentops.py route --task "literal task" --json`. Read [Context Shark](_agent_modules/CONTEXT_SHARK.md).
5. Before complex edits, read [MAX POWERBRAIN](_agent_modules/MAX_POWERBRAIN.md) and run `python3 tools/agentops.py powerbrain --task "literal task" --out output/agentops/powerbrain_task.md`. Resolve its preconditions from source.
6. Run targeted positive, negative and regression checks. Run `python3 tools/agentops.py verify`. Before closeout or interruption, record exact executed commands and results, local checkpoint, and queued factual handoff through `checkpoint --help` and `report --help`. Use [.agentops/manifest.json](.agentops/manifest.json) and [_agent_templates](_agent_templates).
7. Operator acceptance stays PENDING until explicit sign-off. No implicit native QA, publication, deployment or cross-machine checkpoint visibility.
<!-- AGENTOPS:END -->

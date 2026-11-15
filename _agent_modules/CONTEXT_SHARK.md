# CONTEXT SHARK

## S0 fingerprint / S1 routing / S2 bounded retrieval

`python3 tools/agentops.py route --task "checkpoint resume" --json` fingerprints Git and reads the current state, architecture map, issue map, index and local checkpoint. It scores a bounded source inventory using literal task tokens. Git mode searches indexed paths, including their current safe working copies. Non-Git mode uses a bounded directory walk. Review omitted/dirty paths from doctor when necessary.

## S3 owner-caller-consumer triangle

Manifest edges verify source tokens in owner, call site and consumer, including a consumer read anchor. Each verified edge has path, line, excerpt and hash. Matches outside those reviewed relationships remain candidates. Read each function end to end and follow actual data before changing it.

## S4 first divergence / negative control

Find the first writer/reader where known input yields an observed difference. Reproduce using minimal input and use an invalid or deliberately stale input as falsifier. Treat a sole symptom as HYPOTHESIS. A reopened bug requires comparing old QA and the new reproducer.

## S5 stop-vs-escalate policy / S6 checkpoint handoff

Stop expanding once the authoritative writer, caller, consumer and focused test are established. Widen with a specific cross-system, risk, migration or reopened-defect reason. Route is read-only. For continuing work, persist NEXT_EXACT_ACTION through checkpoint.

## Source evidence schema / CLI / context budget and confidentiality

Read named candidate files only within a bounded scan, with at most twelve paths and three short excerpts per path. Exclude secret, private, vendored, binary and generated content. Refuse symlink traversal. Output uncertainty, first divergence, falsifier and exact next action. No semantic inference from lexical matches alone.

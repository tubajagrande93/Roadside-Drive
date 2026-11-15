---
CHECKPOINT_SCHEMA: UAOS-B1
TASK_ID: "<stable id>"
TASK_TITLE: "<literal scope>"
STATUS: "IDLE|ACTIVE|INTERRUPTED|PARTIAL|COMPLETE|BLOCKED"
OPERATOR_AUTHORIZATION: "<exact scope>"
BASELINE_BRANCH: "<ref or UNKNOWN>"
BASELINE_SHA: "<sha or UNKNOWN>"
CURRENT_BRANCH: "<ref or UNKNOWN>"
CURRENT_SHA: "<sha or UNKNOWN>"
WORKTREE: "."
DIRTY_AT_ENTRY: "<status and protected paths>"
FILES_CHANGED: "<relative paths>"
WORKSTREAMS_COMPLETE: "<IDs>"
WORKSTREAMS_PARTIAL: "<IDs and status>"
WORKSTREAMS_NOT_STARTED: "<IDs>"
TESTS_EXECUTED: []
TESTS_NOT_EXECUTED: "<checks and why>"
KNOWN_FAILURES: "<IDs and earliest divergence>"
LATEST_SOURCE_DELIVERY: "<commit/ref/remote status>"
LATEST_HANDOFF_PUBLICATION: "<status>"
NEXT_EXACT_ACTION: "<one step>"
UPDATED_UTC: "<UTC>"
---

CLI-generated front matter also records CURRENT_STATUS_SHA256, CHECKPOINT_REVISION,
OPEN_REOPENED_GATES, REOPENED_UTC, PRESERVATION and LOCAL_EVIDENCE. Use
`checkpoint --help` for fields, `record-test` for test evidence and report for immutable closeout.

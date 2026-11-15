# MAX POWERBRAIN

## Trigger and when NOT to use

Use on interconnected, uncertain or high-risk changes. A small, clear edit can use a short plan.

## Verified baseline / reference & source-owner matrices

Run `python3 tools/agentops.py powerbrain --task "checkpoint resume" --out output/agentops/powerbrain_task.md`. It fills the checked-in task template from route provenance. Verify the live diff, each caller/consumer, baseline hashes and the prior handoff. Reference evidence conveys only what was observed at its source.

## First-divergence and alternative-cause analysis

Write expected and observed behavior at the earliest authoritative boundary. Test a stale input, configuration path or caller mismatch as alternatives. Reproduce before blaming a writer.

## Minimal implementation architecture and ordered phases

Fill PB-00 through PB-07 with exact files, preconditions, edits, persistence, failures, tests, artifacts and STOP decisions. Confirm compatibility and recovery before changing persistent data.

## QA gates, preservation, failure and publication contracts

Record gate IDs, exit codes and exact source. Include targeted positive, negative, reopen, native, security, performance and compatibility checks as applicable. Confirm protected bytes and explicit publication authority. Use the QA ledger and checkpoint.

## CLI / example / anti-generic-prompt examples

For checkpoint work a verified writer line and actual report consumer are a starting point. An unknown symbol gives VERIFY_FIRST. A generated plan leaves implementation and unverified requirements open.

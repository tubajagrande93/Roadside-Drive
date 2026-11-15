# Bounded context

Read CURRENT_STATE first. Route relevant topics through GRAND_MASTER_INDEX. REPO_PROFILE records observed boundaries. ARCHITECTURE_MAP links canonical writers and consumers. RECENT_MILESTONES and KNOWN_ISSUES are bounded indexes. Live source and Git outrank these summaries. GRAND_MASTER is the sole canonical durable document. Local ignored state and evidence are visible only in the originating workspace.

The CLI requires Python 3.11+ on Unix. It has no third-party Python dependencies. Run doctor for live
Git and verification freshness. A release snapshot records the last inspected commit or UNKNOWN for
an unborn baseline. A commit cannot embed its own SHA. A repo-only clone uses the tracked routing
and re-derives current Git. Checkpoints and handoffs require access to the originating local workspace.

## Local continuity commands

```sh
python3 tools/agentops.py record-test --gate INFRA -- python3 -m unittest discover -s tests -p test_agentops_contract.py
python3 tools/agentops.py checkpoint --task-id TASK-001 --status INTERRUPTED --next 'Run python3 tools/agentops.py verify'
python3 tools/agentops.py report --task-id TASK-001 --status INTERRUPTED --next 'Run python3 tools/agentops.py verify'
```

Pass the evidence path returned by record-test through checkpoint's repeatable `--evidence`. Use
`--set FIELD=VALUE` for task scope, workstreams, skipped gates and preservation. Add the exact relative
changed paths with `--changed`. On a reopened gate, record a fresh passing rerun and provide
`--close-gate ID=FIRST-DIVERGENCE-EVIDENCE` together with its evidence file. The local evidence store
is under the operator's control. Its validation is a consistency check, not an attestation against local tampering.

`bootstrap --dry-run` previews reconciliation of the one managed AGENTS block against the checked-in
contract and reports missing inputs. With an already provisioned valid manifest, `--apply` updates only
that block. Preserve unmanaged text and nested rules. For a new manifest schema, add an explicit
migration with a dry run and byte preservation checks. Unknown schemas fail closed.

# Open issues

| ID | Status | Owner | Reproduction / next evidence |
| --- | --- | --- | --- |
| UE-01 | NOT_RUN | Unreal owner TO_VERIFY | Verify native launcher and safe workspace first, then launch an authorized scoped smoke test and capture exact result. Engine Build.version is static evidence. |
| DATA-01 | OPEN | World Builder owner TO_VERIFY | Source-license and phase intent review before any real geodata ingestion. |

## Resolved infrastructure issues

- PUB-01. The first push was rejected by GitHub with GH007. The unpublished root was amended with the verified GitHub `noreply` identity and the same source tree. Git and GitHub queries independently verified the published `main`.
- T16. The failure fixture resolved `python` through the caller's PATH and could run a pyenv shim. Use explicit POSIX exit statuses so the fixture tests rejected and accepted command evidence without depending on a second interpreter lookup.

# Reopened defects

None established. On operator regression, record the gate and first authoritative boundary.

# Negative controls

Run the infrastructure contract harness for sentinel preservation, stale checkpoint, false-PASS and local handoff recovery. Native checks must have an independent negative control before declaring runtime PASS.

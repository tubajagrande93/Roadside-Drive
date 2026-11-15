# Open issues

| ID | Status | Owner | Reproduction / next evidence |
| --- | --- | --- | --- |
| PUB-01 | OPEN | Source publisher/operator | `git ls-remote --symref origin HEAD refs/heads/main`; GitHub's default main name existed without a ref. Obtain authorization for initial ref creation if still absent. |
| UE-01 | NOT_RUN | Unreal owner TO_VERIFY | Verify native launcher and safe workspace first, then launch an authorized scoped smoke test and capture exact result. Engine Build.version is static evidence. |
| DATA-01 | OPEN | World Builder owner TO_VERIFY | Source-license and phase intent review before any real geodata ingestion. |

# Reopened defects

None established. On operator regression, record the gate and first authoritative boundary.

# Negative controls

Run the infrastructure contract harness for sentinel preservation, stale checkpoint, false-PASS and local handoff recovery. Native checks must have an independent negative control before declaring runtime PASS.

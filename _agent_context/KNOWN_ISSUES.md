# Open issues

| ID | Status | Owner | Reproduction / next evidence |
| --- | --- | --- | --- |
| UE-01 | NOT_RUN | Unreal owner TO_VERIFY | Follow the README manual smoke test in a disposable checkout. Engine Build.version, the Intel slice, plugins and map were verified statically. Test the configured Metal SM6 profile on Intel. |
| G01-INTERACTIVE | LIMITED | Gate 01 Unreal | Metal viewport and native PIE movement and floor checks passed. Full manual input coverage and quantitative Intel profiling are optional and remain unexecuted. |
| DATA-01 | OPEN | World Builder owner TO_VERIFY | Source-license and phase intent review before any real geodata ingestion. |

## Resolved infrastructure issues

- Gate 01 editor automation. NullRHI viewport hit-testing failed while placing the native inspection actor. Use the Metal full editor for import and PIE. Single-threaded UE Python wrapper generation resolved an observed parallel startup abort. Use `get_controlled_pawn` in UE Python to read possession.
- INIT 00B publication audit. Removed the Android File Server token from the public configuration and disabled the server and its network connection. The original was preserved locally.

- PUB-01. The first push was rejected by GitHub with GH007. The unpublished root was amended with the verified GitHub `noreply` identity and the same source tree. Git and GitHub queries independently verified the published `main`.
- T16. The failure fixture resolved `python` through the caller's PATH and could run a pyenv shim. Use explicit POSIX exit statuses so the fixture tests rejected and accepted command evidence without depending on a second interpreter lookup.

# Reopened defects

None established. On operator regression, record the gate and first authoritative boundary.

# Negative controls

Run the infrastructure contract harness for sentinel preservation, stale checkpoint, false-PASS and local handoff recovery. Native checks must have an independent negative control before declaring runtime PASS.

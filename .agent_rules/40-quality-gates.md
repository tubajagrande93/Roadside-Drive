# Verification Rules

## Reproducer and first divergence

Record expected vs observed at the actual writer/read path and include a falsifying control. Find callers and consumers before a change.

## Positive / negative / regression / native gates

Cover normal execution, invalid or stale input, data preservation and affected downstream behavior. Native tests need verified launcher and reproduction. Never shift a prototype's gate or change expected output to pass.

## Exact source SHA and executed command

Log argv or reproducible command, exit code, source SHA and dirty state. UNKNOWN is allowed for unborn/non-Git evidence with explicit limits. Report PASS only with an executed exit-zero command at the correct source and gate.

## No tests-as-operator-acceptance

Product acceptance is an operator decision.

## Critical findings reopen earlier PASS

On contradictory runtime evidence reopen the QA gate, record a reproducer and identify first divergence before repair.

## Preservation exit and honest partial result

Inspect staged names and protected hashes, compare actual outputs, and mark unrun checks NOT_RUN with reasons. A refused push or missing evidence remains an explicit gate.

## Proportionate development QA

Use the smallest checks that establish usability at the changed boundary. For the World Builder and pilot, default to a source import and a synthetic build, plus targeted Unreal/PIE movement and floor smoke when the native path changes. Reserve broad regression for shared architecture, destructive changes, persistence or coordinate changes, observed regressions, release candidates and explicit requests.

Record implementation, verification and operator acceptance independently. A test that was not run has verification NOT_RUN. Use LIMITED for bounded observations, VERIFIED for executed criteria with evidence and FAILED for an observed failure. Reserve PARTIAL implementation for omitted required functionality. UAOS-B1 COMPLETE_VERIFIED still requires the task-owned gates to pass.

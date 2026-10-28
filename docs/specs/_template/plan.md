---
ticket: <TICKET>
status: draft            # draft | approved | implemented
spec: ./spec.md
---

# Plan: <TICKET> <short title>

## Facts

Current state with file references (`path:line`): what is wrong or missing, how similar things are done nearby, existing compatibility layers found (AGENTS.md section 3), constraints from the ADRs the spec lists.

## Proposal

The chosen approach and, if several existed, why this one. Open trade-offs are listed for the reviewer. Every compatibility layer the change adds or keeps (AGENTS.md section 3) is named here with its purpose and place; a layer not named here is not approved.

## Files to change

| File | Change |
|---|---|
| `<path>` | |

## Preservation of existing data and behavior

How stored data and user state, running experiments, other callers of the changed code and analytics stay intact. For a production-risky or irreversible change (AGENTS.md section 8): the recovery scenario, what is watched and when to stop, then how the previous state is restored or, when it cannot be, the fix forward with its end state and what is lost for good, and how the reached state is confirmed.

## Verification

Commands (AGENTS.md section 9) and expected results, scoped to the change:

- Type check:
- Lint:
- Tests (scoped):
- Manual check: feature, environment, steps.

## Tasks

Ordered, each mapped to requirements and acceptance criteria from the spec.

- [ ] T1 (R1, AC1):
- [ ] T2 (R2, AC2):

## Sessions

The tasks in order, split into sessions: one `/implement` run each, started by a person after checking the previous one (`docs/specs/README.md`, "Sessions"). Every task is in exactly one session. "Check" is what the person verifies before the next session; the person records the check in "Checked" with name and date.

- S1 (T1–T2): <what works after it>.
  - Check: <what the person verifies>.
  - Checked:

## Results and deviations

Filled during implementation: what was verified and how (commands, results), what was not verified and why, deviations from the plan and their reason, out-of-scope findings.

---
name: plan
description: Write the implementation plan for a ticket from its approved spec in docs/specs, following AGENTS.md section 2.3. Use only when invoked explicitly.
argument-hint: "<TICKET>"
disable-model-invocation: true
---

Write the implementation plan for the ticket given with the invocation (`$ARGUMENTS`: `<TICKET>`).

1. Find the ticket folder `docs/specs/<TICKET>-*/`; unless exactly one matches, stop and say so. Read `AGENTS.md` (sections 2.3, 3, 4 and 9), `docs/specs/README.md`, the folder's `spec.md` and the ADRs it lists.
2. If the spec status is not `approved`, stop and say so. A plan is written only from an approved spec.
3. Investigate the code in scope: the files that will change and the ones that call them (AGENTS.md section 5), the configs per environment, the tests nearby, and existing compatibility layers (AGENTS.md section 3). A conflict with an accepted ADR found here stops the plan: report it (`docs/specs/README.md`, "ADRs").
4. Create `plan.md` next to the spec from `docs/specs/_template/plan.md`, or update the existing one after a change of the spec or of the approach: facts with `path:line` references, proposal (with alternatives if several exist, and every compatibility layer the change adds or keeps), files to change, preservation of existing data and behavior (with the recovery scenario of AGENTS.md section 8 for a production-risky or irreversible change), verification commands scoped to the change, ordered tasks mapped to requirements and acceptance criteria, and the tasks split into sessions (`docs/specs/README.md`, "Sessions"): in order, every task in exactly one session; each ending in a state the person can check, with the checks passing and a slice of the change working; sized for one run, usually three to five tasks, a plan of up to five tasks being one session unless a check is needed in the middle; a production-risky task (AGENTS.md section 8) last in its session; and "Check" naming what the person verifies before the next session, from the manual checks of "Verification". On an update, untick every task whose finished work no longer matches the new plan, because its requirements, its approach or its verification changed, clear the "Checked" of its session, and keep "Results and deviations" as the history of earlier runs. Keep `status: draft`, with one exception: regrouping sessions that have not started, when asked for, changes neither requirements, approach nor verification, so it is done on the approved plan with its status kept (`docs/specs/README.md`, "Sessions").
5. No code changes. Report the path of the plan, the proposed sessions and the trade-offs the reviewer must decide, then stop.

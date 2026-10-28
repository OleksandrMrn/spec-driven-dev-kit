---
name: spec
description: Create or update the spec (what and why) for a ticket in docs/specs, following docs/specs/README.md. Use only when invoked explicitly.
argument-hint: "<TICKET> [short title]"
disable-model-invocation: true
---

Write or update the spec for the ticket given with the invocation (`$ARGUMENTS`: `<TICKET>` and an optional short title), following the spec-driven process of this repository.

1. Read `AGENTS.md` (sections 1, 2 and 9), `docs/specs/README.md` and the accepted ADRs in `docs/adr/` that apply to the ticket's scope.
2. Investigate what the ticket touches: the code, configs and tests in scope (AGENTS.md section 5). Do not change any file outside `docs/specs/`.
3. Find the ticket folder: `docs/specs/<TICKET>-*/`. None → create `docs/specs/<TICKET>-<slug>/spec.md` from `docs/specs/_template/spec.md`; `<slug>` is the branch title in snake_case. One → update its `spec.md`, or create it from the template if missing. Several → stop and ask which one belongs to the ticket. A folder is never renamed, even when the branch is. A spec that is `done` or `rejected` is not updated: stop and say so; the person reopens it by setting it, and its plan if there is one, to `status: draft`, and new work on a done ticket is as a rule a new ticket (`docs/specs/README.md`, "Statuses"). An approved spec whose requirements or scope change goes back to `status: draft`, together with its `plan.md` if one exists; both are approved again (`docs/specs/README.md`, "Statuses"). Small corrections (typos, wording, links) keep the status.
4. Fill every section with facts and file references. Requirements and acceptance criteria are numbered and testable. "Contracts touched" lists concrete files and keys per environment. "ADRs" lists the accepted ADRs that apply; a requirement that would contradict one is named there and in "Open questions" (`docs/specs/README.md`, "ADRs"). A new spec has `status: draft`.
5. Put everything only the reviewer can decide into "Open questions". Do not guess.
6. Report the path of the spec and the open questions, then stop. Approval is given by a person by setting `status: approved` in the file.

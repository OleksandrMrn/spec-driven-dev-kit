---
name: review
description: Review the uncommitted changes, the current branch or a named branch against the ticket's spec and plan in docs/specs, or against the project rules when there is no spec; report findings, change nothing. Use only when invoked explicitly.
argument-hint: "[<TICKET>] [local | HEAD | <branch>] [what the change is for]"
disable-model-invocation: true
---

Review a change: the uncommitted work, the current branch or a named branch, against the ticket's spec and plan or, without a spec, against the project rules. Read-only: modify no file, `plan.md` included; the findings are the report.

1. Read `AGENTS.md` (sections 2.3, 2.6, 3, 4 and 9) and `docs/specs/README.md`. Read the arguments (`$ARGUMENTS`): a first word in the ticket key format of AGENTS.md section 9 is the ticket; a next word that is `local`, `HEAD` or the name of an existing branch (`git branch --list <name>`) is the revision; the rest is what the change is for, in the person's words. With a ticket the review is against its spec (step 4) and the revision defaults to `HEAD`; without one it is against the project rules (step 5) and the revision defaults to `local`.
2. Fix the revision and its diff.
   - `local`: the working tree. The diff is `git diff HEAD` (staged and unstaged) plus the untracked files from `git ls-files --others --exclude-standard`, read in full. No fetch and no base branch are needed.
   - `HEAD` or a branch: that revision against the integration branch `<base>` of AGENTS.md section 9. Run `git fetch origin <base>` first, which updates `origin/<base>` and leaves the local `<base>` untouched; if the fetch fails, say so and diff against the local `<base>`, naming it in the report. The diff is `git diff origin/<base>...HEAD` or `git diff origin/<base>...<branch>`.
   The ticket folder, spec, plan, ADRs and code are read at the revision, with `git ls-tree --name-only <revision> <folder>/` and `git show <revision>:<path>`, or from the working tree for `local`. Uncommitted changes are not part of a `HEAD` or branch review. Checks and tests run in the working tree, so they are run only when the working tree is the revision: `local`, or `HEAD` with a clean tree (`git status --porcelain` prints nothing); for any other revision they are reported as not run for it.
3. With a ticket, find its folder `docs/specs/<TICKET>-*/` at the revision. Several → stop and say so. One → review against the spec (step 4). None → say so in the report and review without a spec (step 5). Without a ticket, step 5; no folder is looked for.
4. Review against the spec. Read `spec.md`, `plan.md`, the ADRs the spec lists and any other accepted ADR in `docs/adr/` whose subject the change touches. If the spec is neither `approved` nor `done`, or the plan is neither `approved` nor `implemented`, say so first: the review is then against a document that is not approved. Check, with file references:
   - every requirement and acceptance criterion of the spec is covered, and nothing beyond the spec was changed (scope creep); a requirement whose tasks are in a session not yet done ("Sessions" in the plan) is pending, not a finding;
   - compatibility layers (normalizers, adapters, fallbacks, default substitutions; AGENTS.md section 3): none that the plan does not name, and those it names are built as the plan describes;
   - the change follows the ADRs read above;
   - a production-risky or irreversible change has the recovery scenario of AGENTS.md section 8 in the plan;
   - duplicated code: a shared pattern changed in one copy is changed in every copy in scope, or the spec limits the scope;
   - configs changed in every environment the spec lists, with keys consistent between environments;
   - tests updated or added for the changed behavior; no test weakened or skipped;
   - the verification of every session done was run, passed (the known baseline of AGENTS.md section 9 excepted) and is recorded in "Results and deviations"; the whole verification of the plan only once every session is done.
5. Review without a spec. Read the accepted ADRs in `docs/adr/` whose subject the change touches. Check, with file references:
   - the change meets none of the triggers in `docs/specs/README.md`, "When a spec is required"; if it meets one, that is the first finding, and the way forward is a spec;
   - the change does what the person said it is for, when that was given, and nothing beyond it;
   - the change follows AGENTS.md sections 3, 4 and 9 and the ADRs read above; a new or extended compatibility layer is a finding, since adding one needs an approved plan (AGENTS.md sections 2.3 and 3);
   - the checks of AGENTS.md section 9 pass for the changed scope: run the scoped ones when the working tree is the revision (step 2), the known baseline excepted; otherwise report them as not run for the revision;
   - tests updated or added for the changed behavior; no test weakened or skipped.
6. Report the findings as `docs/specs/README.md`, "Review findings", defines them: ordered by severity P0 to P3, each with the file and place, what is wrong, what the spec, the rule or the stated purpose expects, and the evidence, a test run or a scenario traced through the code; assumptions and wishes apart from the defects, and what must be fixed before the merge, which the severity alone does not say. State the revision and the base used, the kind of review (against the spec or without one) and, against a spec, the sessions done and checked; say explicitly what was verified and what was not. Fixes are not made here: after a review against a spec they go through `/implement`; after a review without a spec the person gives them as the next task and runs `/review` again (`docs/specs/README.md`, "Without a spec").

# Spec-driven development

How ticketed work is specified, planned and implemented in this repository, by people and AI agents alike. The rules for agents are in [AGENTS.md](../../AGENTS.md); this document describes the process those rules refer to.

## Before a ticket

An idea that has no ticket yet, or a ticket that turns out to be a project, is investigated first with `/investigate <slug>` (`$investigate` in Codex): rounds of questions and research that end in recorded decisions and a roadmap under `docs/investigations/<slug>/`, from which tickets are cut. The process is in [docs/investigations/README.md](../investigations/README.md). An investigation is input for specs, not an instruction for agents.

## When a spec is required

A ticket gets a spec when any of these applies:

- a generic trigger from AGENTS.md section 2.3: a public contract changes (API, data schema, config or file format, CLI, protocol, a module signature used by others), layers disagree, a dependency is added or upgraded, several materially different solutions exist, more than one module is affected or data must migrate, the change is irreversible or production-risky;
- a project trigger listed in AGENTS.md section 9 (Conventions);
- the person or the reviewer asks for one.

Everything else (small bug fixes, text changes, visual tweaks) goes without a spec, the way described next. Both ways follow the same rules of AGENTS.md; they differ only in the documents written.

## Without a spec

A change that needs no spec is given to the agent as a task in chat, with or without a ticket, and done under AGENTS.md: pre-flight check (section 2.1), investigation, minimal change, verification, self-review and report. Nothing is written under `docs/specs/`. The change is reviewed with `/review` (`$review` in Codex), which without a ticket takes the uncommitted changes (`/review what the change is for`) or, with `HEAD` or a branch name, committed work: the review checks the diff against the project rules, the accepted ADRs that apply and the stated purpose, runs the scoped checks when the working tree is the revision and reports them as not run otherwise, and checks that the change meets none of the triggers above. Fixes after the review are given as the next task, verified the same way and reviewed again. The moment a trigger appears, in the task or in the review, the work stops and a spec is written (`/spec <TICKET>`); what was done so far is input for it, not an instruction.

## Folder layout

```
docs/specs/
  README.md                    this file
  _template/spec.md            what and why
  _template/plan.md            how
  _example/<TICKET>-<slug>/    a finished ticket, fictional, for reference
  _tools/                      checks of this kit (see Tooling)
  <TICKET>-<slug>/spec.md      one folder per ticket
  <TICKET>-<slug>/plan.md
```

`<TICKET>` is the ticket key (format in AGENTS.md section 9) and `<slug>` is the branch title in snake_case when the folder is created, so the folder for branch `ABC-123/fix_login_redirect` is `ABC-123-fix_login_redirect`.

The folder is found by its ticket, `docs/specs/<TICKET>-*/`: none → `/spec` creates it; one → every skill uses it; several → the skills stop and ask. Its name is fixed at creation and does not follow later branch renames.

## Steps

1. **Spec.** The developer creates the ticket folder from `_template/spec.md` and fills it, with an agent (`/spec <TICKET>` in Claude Code, `$spec <TICKET>` in Codex) or by hand. The spec says what changes and why, not how, and lists the accepted ADRs that apply. Status `draft`.
2. **Spec approval.** The reviewer (a lead or a designated reviewer) reads the spec, resolves the open questions and any conflict with an accepted ADR (see ADRs) and sets `status: approved`, `approved_by` and `date`. From this point agents treat the spec as an instruction (AGENTS.md section 0).
3. **Plan.** From the approved spec an agent (`/plan`, `$plan`) or the developer writes `plan.md` from `_template/plan.md`: facts with file references, proposal (naming every compatibility layer the change adds or keeps), files to change, how existing data and behavior are preserved, verification, ordered tasks, and the tasks split into sessions with what a person checks after each (see Sessions). Status `draft`.
4. **Plan approval.** The reviewer sets `status: approved`. Until then there are no code changes (AGENTS.md section 2.3).
5. **Implementation.** `/implement`, `$implement` or by hand, one session of the plan per run (see Sessions): its tasks in order, or a single task with `T<n>`, scoped verification after each task, self-review (AGENTS.md section 2.6) against the session's requirements at the end of the run and against the whole spec after the last session. A task is ticked only when its verification has passed. Results and deviations are written into `plan.md`, one entry per run. After the run the agent stops: the person checks the result, records the check in the session's "Checked", and starts the next session with a new run. The plan becomes `implemented` only when every task is done and the verification has passed; the only failures allowed are the known baseline of AGENTS.md section 9, named in the results. Agents do not commit or open PRs. Whether and when to commit is the developer's call, between sessions too; after the last session `/implement` asks whether to commit and open a PR, and either happens only on an explicit yes (AGENTS.md section 6). If a PR is opened, it targets the integration branch (AGENTS.md section 9) and links the spec folder.
6. **Review.** `/review` or `$review` takes the diff of the current branch or of a named branch against the integration branch on the remote, or, with `local`, the uncommitted changes, and reads the spec, plan and code at the same revision (the working tree for `local`). It checks coverage of requirements and acceptance criteria, scope creep, compatibility layers against the plan, the ADRs the spec lists, consistency across duplicated code and tests; between sessions the requirements of the sessions not yet done are reported as pending, not as findings. Then a person reviews the change. Fixes requested by the review stay within the approved scope and go through `/implement` again; the plan is `implemented` again only when the fixes are in and the checks pass, otherwise it goes back to `approved` with the affected tasks unticked, the approval itself staying. A finding that changes requirements, scope or approach goes back to the spec or plan (see Statuses).
7. **Done.** After the merge the developer sets the spec to `status: done`. A decision that outlives the ticket (architecture, contracts, conventions) becomes an ADR in `docs/adr/`.

## Sessions

A plan is implemented in sessions: one `/implement` run each, in the order of the plan, with a person's check between them. The split keeps one run within what an agent can hold in its context, and the person sees the work in pieces instead of once at the end.

- `/plan` proposes the split in the plan's "Sessions" section and the reviewer approves it with the plan. The tasks are taken in order, every task in exactly one session. A session ends in a state the person can check: the project's checks pass and a slice of the change works, not half a function. A session is sized for one run, usually three to five tasks; a plan of up to five tasks is one session unless a check is needed in the middle. A production-risky task (AGENTS.md section 8) is the last of its session, so it is checked right after it.
- Every session names in "Check" what the person verifies before the next session starts: the manual steps of "Verification" that apply, and whatever else the person should look at.
- `/implement` runs one session: the first with an unticked task, or the one named with `S<n>`. It starts a session only when every earlier session has "Checked" filled; a single task `T<n>` runs without that. A ticked task that a run changes, by `T<n>`, in a fixes run or after the review, is unticked first and the "Checked" of its session cleared, and ticked again when the fix is verified. A fixes run after the review or the person's check may name findings in several sessions: it is the one exception to one session per run, and every session it touches is checked again. When every task is ticked and the plan is still `approved`, the run finishes the plan: the whole verification, the self-review against the spec and, when all passes, `implemented`. After the run it reports what the person checks and stops. The next session is the person's call, with a new run, as a rule in a fresh conversation with the agent, so it starts from the plan and not from the earlier context.
- The person checks the result and records it in the session's "Checked" with name and date. Whether to commit at that point is the person's call. A problem found in the check goes back to the agent as a fixes run on that session (`/implement <TICKET> S<n>`), which unticks the affected tasks and clears "Checked", so the session is checked again; a problem that changes requirements, scope or approach goes back to the spec or plan (see Statuses).
- Regrouping sessions that have not started changes neither requirements, approach nor verification, so it resets nothing (see Statuses); the person does it, or asks `/plan` to.
- Statuses do not change between sessions: the plan stays `approved`, and the ticked tasks show what is done.
- A run interrupted before its report is resumed from what is on disk, the plan's ticks, its results and the diff, not from memory (AGENTS.md section 2.4); nothing is approved again unless requirements, scope or approach changed. A run that stops on purpose before its work is done writes the unfinished action and the next command or check into "Results and deviations".

## Review findings

A finding of a review, by `/review` or by a person, names the file and place, what is wrong, what the spec, the rule or the stated purpose expects, and the evidence: a test that was run or a scenario traced through the code. Assumptions and wishes are listed apart from the defects. Severity says what the consequence is and how far it reaches; what must be fixed is a separate question, answered below the table:

| Severity | Meaning |
|---|---|
| P0 | data loss, a security hole or an outage for the users |
| P1 | wrong behavior for users or for other code: a requirement or an acceptance criterion is not met, a contract is broken |
| P2 | wrong behavior with a limited effect: an edge case, a wrong text, something a workaround covers |
| P3 | no effect on behavior: a comment, a name, dead code, the structure of the code |

Fixed before the merge: every P0 and P1, and every finding of any severity that is a requirement, an acceptance criterion or a rule of AGENTS.md not met, a P3 too. A P2 or P3 that breaks no rule may go into a named follow-up or stay; the author decides. A check of AGENTS.md section 9 that fails because of the change blocks the merge whatever the severity of its cause; the failures of the known baseline of section 9 do not. Wishes, improvements and a reviewer's stylistic preference are not defects and get no severity, whatever they are called: they are listed apart.

## Statuses

The spec and the plan have separate statuses.

### Spec statuses

| Status | Meaning |
|---|---|
| `draft` | being written, or changed after approval; not an instruction for agents |
| `approved` | approved by the reviewer; agents follow it |
| `done` | the change is merged into the integration branch; set by the developer |
| `rejected` | will not happen; kept for history |

### Plan statuses

| Status | Meaning |
|---|---|
| `draft` | being written, or reset by a spec change; not an instruction for agents |
| `approved` | approved by the reviewer; agents implement it. Also the state between sessions and of an unfinished implementation or fix: the approval stays and the unticked tasks show what is open |
| `implemented` | every task ticked and every verification of the plan passed, the known baseline of AGENTS.md section 9 excepted; the approval stays in force for fixes within the approved scope, and an unfinished fix puts the plan back to `approved` |

Editing an approved spec or plan resets it to `draft`; the edited version is approved again. A spec change that affects requirements or scope also resets its plan to `draft`: the plan was derived from the old spec and must be checked against the new one, and `/implement` refuses a plan whose spec is not approved. When a plan is updated after a change of the spec or of the approach, every task whose finished work no longer matches the new plan (changed requirements, approach or verification) is unticked and the "Checked" of its session is cleared, so `/implement` does it again and the person checks it again. Small corrections that do not change requirements, scope or approach (typos, wording, links) reset nothing. Neither does the bookkeeping of implementation: ticking tasks and filling "Results and deviations" in `plan.md` do not touch the approval. Before approval, drafts under `docs/specs/` are created and edited freely; writing them is how approval is requested, not a code change (AGENTS.md section 2.3). `done` and `rejected` are final for the skills: `/spec` stops on them, and `/plan` and `/implement` need an approved spec. The person reopens a ticket by setting its spec, and its plan if there is one, to `draft`; new work on a done ticket is as a rule a new ticket with its own folder. `/review` reads a `done` spec as approved.

## ADRs

Accepted ADRs in `docs/adr/` are instructions for agents and rank after the approved spec and plan of a ticket (AGENTS.md section 0). A file is named `0001-<slug>.md` (AGENTS.md section 9).

- The spec lists in "ADRs" the accepted ADRs that apply to its scope; `/spec`, `/plan`, `/implement` and `/review` read them.
- An approved spec and plan agree with the accepted ADRs. A spec that would contradict one names it in "ADRs" and in "Open questions". Before approval the reviewer either changes the spec or accepts a new ADR that supersedes the old one: the new ADR has `supersedes: <old id>`, the old one gets `status: superseded`.
- A conflict found later, while planning, implementing or reviewing, stops the work until it is resolved the same way.

## Tooling

- **Claude Code.** Skills `/spec`, `/plan`, `/implement`, `/review` and `/investigate` live in `.claude/skills/`; `/investigate` runs before a ticket exists ([docs/investigations/README.md](../investigations/README.md)). Shared permissions are in `.claude/settings.json`; personal overrides go to `.claude/settings.local.json` (not tracked).
- **`AGENTS.md` in Claude Code.** By default, Claude Code v2.1.277 and later reads `AGENTS.md` itself only when there is no `CLAUDE.md`, `.claude/CLAUDE.md` or `CLAUDE.local.md` in the working directory or any directory above it; `~/.claude/CLAUDE.md` does not count, and the **Project instructions** setting in `/config` can make it read both. Some sessions do not read it at all: an older version, the built-in plugin that reads `AGENTS.md` disabled, sometimes the first session after an upgrade, and before v2.1.281 some sessions on Amazon Bedrock or with telemetry disabled ([docs](https://code.claude.com/docs/en/memory#when-claude-code-reads-agents-md)). After installing the kit, open a new session in the repository: an interactive session prints `no CLAUDE.md found; AGENTS.md loaded: <path>` at the start, and from v2.1.280 `/memory` and `/context` list an `AGENTS.md` read directly ([docs](https://code.claude.com/docs/en/memory#troubleshoot-memory-issues)). If it is not read, import it: a `CLAUDE.md` next to `AGENTS.md` whose first line is `@AGENTS.md` (tracked, for everyone), or the same line in an untracked `CLAUDE.local.md` (for you only). An imported `AGENTS.md` is not read twice. Check with `/context` again: `CLAUDE.md` must now be listed under "Memory files".
- **Permissions.** The deny rules in `.claude/settings.json` cover the usual forms of force pushes (`--force*`, `-f`, `+<refspec>`, `--mirror`), pushes to `main` (`main`, `<src>:main`, `refs/heads/main`, `--all`), deletion of remote and local branches, `reset --hard`, `commit --amend`, `rebase`, `clean`, `rm -rf` in its common spellings, and reads of `.env` files. They match the command text ([docs](https://code.claude.com/docs/en/permissions#bash)), so they are a safety net for the commands an agent usually writes, not a protection boundary. They do not catch: `git push` with no refspec or with `HEAD` while `main` is checked out; git started another way (`git -C <dir> push`, `git -c <key>=<value> push`, `/usr/bin/git`, `sh -c '…'`, git aliases); combined short flags such as `-uf`; other commands with a similar effect (`git restore`, `git checkout -- <path>`, `git stash drop`, `rm -r`). `Read` rules cover Claude's file tools, the file commands Claude Code recognizes in Bash (`cat`, `head`, `tail`, `sed`, `tee`) and the targets of redirections, not a command that reads files without naming them or a script that opens them itself ([docs](https://code.claude.com/docs/en/permissions#read-and-edit)). Protected branches need branch protection on the remote; limits on files and network that do not depend on the command text need sandboxing. For each protected branch of AGENTS.md section 9 other than `main`, add the same rules as for `main`.
- **Codex.** The same skills live in `.agents/skills/` and are invoked as `$spec <TICKET>` (or picked from `/skills`). `AGENTS.md` is read natively; Codex caps the combined size of `AGENTS.md` files at 32 KiB by default, so the root file stays well under that.
- The skill bodies in both folders are identical: a change to one is mirrored to the other.
- **Checks.** `python3 docs/specs/_tools/validate.py` (Python 3.8 or later, standard library only) checks that the five skills of this kit exist in both folders and their copies match (bodies, names, descriptions, Claude and Codex metadata); other skills of the project are not checked. It checks that the statuses in the templates, in this README, in `docs/investigations/README.md` and in every ticket folder and ADR are allowed and consistent, for example no approved plan next to a draft spec and no `implemented` plan with unticked tasks, without a ticked task or without results; that every spec, plan and ADR has the template's front matter keys; that an `approved` or `done` spec has `approved_by` and `date`; that a ticket folder is named after the spec's ticket and its plan carries the same ticket; that a `done` spec has an `implemented` plan; that a plan has `spec: ./spec.md`; that the tasks of a plan are `T1`, `T2`, … in order; that every plan has a "Sessions" section whose entries `- S<n> (T<a>–T<b>): …` are numbered from S1 in order, take every task of "Tasks" exactly once and in order, and each have one "Check" line with text and one "Checked" line, filled as `<name>, <YYYY-MM-DD>` only when every task of the session is ticked; that no two folders share a ticket; that ADR file names match their ids, no two ADRs share a number, and a `supersedes` names an existing ADR, which is `superseded` once the new one is `accepted`; that the example follows the templates; and that every investigation folder under `docs/investigations/` has the template's front matter keys, an allowed status, a `slug` equal to the folder name, a "Coverage" section with every area of the template listed once, a `roadmap.md`, when present, with the template's keys, the folder's slug and `investigation: ./investigation.md`, and, when `ready`, a date, no open area, a decision and a `roadmap.md` with a step and a candidate ticket. Run it after changing skills, templates or statuses. It reads front matter in a restricted format, not as YAML: one `key: value` per line, unindented; the value is plain text without quotes, up to an optional comment that starts with ` #`. Quoted values (`status: "approved"`; write `status: approved`) and indented lines (nested, list or multi-line values) are reported as problems in documents, while a skill's metadata may quote a value; flow values such as `[a, b]` are read as plain text. A value that contains `: ` or ends with `:` is reported too, in documents and skills alike: the format is a subset of YAML, and the YAML parsers that load skill metadata in Claude Code and Codex reject such a value. `python3 -m unittest discover -s docs/specs/_tools` runs its tests, which also walk through a spec changed after approval, a failed verification, a partial implementation, a fix after review, a plan implemented in two sessions, and an investigation from draft to ready. These checks are structural: they do not run the process. After changing a skill, walk through its steps once on a real change in Claude Code and in Codex.

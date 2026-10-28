# Investigations

How an idea without a ticket is investigated before anything is specified, by a person with an agent. The rules for agents are in [AGENTS.md](../../AGENTS.md); the ticketed process that follows is in [docs/specs/README.md](../specs/README.md).

An investigation turns a raw idea (an app, a feature, a process, anything) into recorded decisions, findings and assumptions, and a roadmap from which tickets are cut. It is written with `/investigate <slug>` in Claude Code (`$investigate <slug>` in Codex) in rounds: the agent researches what needs no decision, asks the questions only the user can answer, records the answers and derives the next round, until the roadmap can be written.

An investigation is input for the specs that follow, not an instruction for agents: it is not among the sources of commands in AGENTS.md section 0, and nothing is implemented from it directly. Tickets are cut from its roadmap; a ticket gets a spec (`/spec <TICKET>`) when the triggers of `docs/specs/README.md` apply, and that spec, which links the folder in "Context", is what gets approved; a ticket that needs no spec is done under the project rules, with the investigation as its background.

## When to investigate

- An idea has no ticket yet and no spec can be written: the goal, the scope or the constraints are not decided.
- A ticket turns out to be a project: several specs would be needed and their order is not clear.

A change that already has a ticket with a clear goal needs no investigation: it goes through `docs/specs/README.md`, with a spec when its triggers apply or the person asks for one, without one otherwise.

## Folder layout

```
docs/investigations/
  README.md                       this file
  _template/investigation.md      idea, coverage, decisions, findings, assumptions, open questions
  _template/roadmap.md            open points, phases, steps, candidate tickets
  <slug>/investigation.md         one folder per idea
  <slug>/roadmap.md
```

`<slug>` is a short name of the idea in snake_case, fixed at creation; the front matter of both files carries it.

## How a run goes

1. **Start.** `/investigate <slug> <the idea in one sentence>` creates the folder with `investigation.md` from its template, `status: draft` and the idea in the user's words. The same command without the idea continues an existing folder.
2. **Research.** The agent looks up what needs no decision: the code and docs the idea touches, platforms, libraries, services, markets, limits and prices. Each result is a finding with its source and date, `verified` when read from the source and `unverified` when from memory. Every external dependency (an API, a service, an exchange, a payment provider) gets an entry with the status of what is needed, the access requirements, the limits and fees, and what is unknown, before the roadmap builds on it.
3. **A round of questions.** Up to 15 questions in one block, as many as the open areas need, grouped by area, the decisive ones first. Each says what in the roadmap depends on it and, where options exist, which is recommended and which is taken by default. The user answers in chat (`Q3: b`, or in words) or in the file under "Answer"; "don't know" and "later" are answers too.
4. **Recording.** Every answer is written down before the next round: decisions with their options and reason, facts as findings, "don't know" as an assumption with the step that verifies it. A decision that changes an earlier one is added, and the earlier one marked superseded. "Coverage" shows which areas are closed; "Log" lists the rounds. Everything is on disk after each round, so a run can end at any point and continue later with the same command.
5. **Roadmap.** When no open question blocks it, or the user says so, the agent writes `roadmap.md`: the open points it does not decide yet, each with the step that closes it; phases with exit criteria; ordered steps with what they realize and how they are verified; candidate tickets; what the decisions excluded. For each external dependency the first step is one real operation end to end with real credentials, before anything is built on it. A roadmap written with open points is a draft: the investigation stays `draft` while an area of "Coverage" is open.
6. **Ready.** The user reads the roadmap and sets `status: ready`; tickets are created from "Candidate tickets" and go through the ticketed process of `docs/specs/README.md`, with a spec when its triggers apply. A decision that binds architecture becomes an ADR through the ticket that implements it (`docs/specs/README.md`, "Steps", step 7).

## Areas

Every investigation covers these areas; one that does not apply is closed with `n/a` and the reason.

| Area | Covered when |
|---|---|
| Problem and users | who has the problem, how they solve it today and why now are decided |
| Value and success | what is measured after launch, and which number or event says it worked |
| Non-goals | what the idea does not do, even when asked |
| First version | the smallest version worth shipping, and what is cut to later |
| Constraints | time, budget, people and skills, legal and compliance, platforms, assets to reuse |
| Domain and data | entities, their lifecycle and invariants, volumes, sources of truth, what is stored and for how long |
| External dependencies | every service the idea relies on has its entry: status, access, limits, fees, unknowns |
| Architecture and stack | the options considered, the one chosen and what it rules out |
| Risks and spikes | what can kill the idea and the cheapest check for each |
| Operations | hosting, cost, monitoring, backups, security, privacy, support |
| Delivery | the order of work, the exit criterion of each step, who verifies |

## Statuses

| Status | Meaning |
|---|---|
| `draft` | being investigated; rounds continue |
| `ready` | the user agreed the roadmap; tickets are cut from it. Set by the user, with the date |
| `parked` | set aside; kept to continue later |
| `rejected` | will not happen; kept for history |

`date` in the front matter is the date of the last status change. `ready` needs the date, every area of "Coverage" `covered` or `n/a`, at least one decision, and a `roadmap.md` with steps and candidate tickets. `/investigate <slug>` continues a `draft`, offers to resume a `parked` one (it goes back to `draft`, with a line in "Log"), and stops on `ready` or `rejected`: those are reopened only by the user setting `status: draft`, after which new decisions supersede the old ones. After `ready` what changes is decided in the tickets, in their specs where they have one.

## Tooling

- **Claude Code.** The skill `/investigate` lives in `.claude/skills/investigate/` and is invoked explicitly only. **Codex.** The same skill lives in `.agents/skills/investigate/` and is invoked as `$investigate <slug>`. The bodies are identical: a change to one is mirrored to the other.
- **Checks.** `python3 docs/specs/_tools/validate.py` checks the two copies of the skill like the other skills of the kit, and every folder here: `investigation.md` has the template's front matter keys, an allowed status, a `slug` equal to the folder name, and, in every status, a "Coverage" section that lists every area of the template exactly once (a project may add areas) with `open`, `covered` or `n/a` as its status; `roadmap.md`, when present, has the template's keys, the folder's slug and `investigation: ./investigation.md`; a `ready` investigation has a date, no open area, at least one decision (`- D<n>`) and a `roadmap.md` with at least one step (`- S<n>.`) and one candidate ticket. The content itself is not checked: whether the decisions are sound is the user's call when setting `ready`. The front matter format is the restricted one described in `docs/specs/README.md`, "Checks".
- Communication in chat follows AGENTS.md section 7; the files are in English like the rest of the repository.

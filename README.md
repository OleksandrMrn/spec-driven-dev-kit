# Spec-driven development kit

A drop-in kit for working on a code repository with AI agents under explicit rules. It targets Claude Code and Codex, and consists of:

- `AGENTS.md`: the rules for agents, independent of language, platform or stack, with a project-specific section to fill in;
- five skills that drive the process: `/investigate`, `/spec`, `/plan`, `/implement` and `/review` (the same five as `$investigate`, `$spec`, … in Codex);
- templates for specs, plans, ADRs and investigations, and a finished fictional example;
- a validator with tests that checks the structure of the kit and of every ticket, ADR and investigation in the repository.

The kit holds no code of its own beyond the validator: it is documents, skills and conventions, and it works with any language or stack.

## How it works

Work on a ticket goes through documents that a person approves before the agent changes code. A change that touches a public contract, several modules, data, a dependency or production, that has several materially different solutions or that exposes a mismatch between layers needs a spec and a plan (AGENTS.md section 2.3 lists the triggers); small changes go without documents, under the same rules. The flow:

1. `/investigate <slug> <the idea in one sentence>`: an idea with no ticket yet is researched and decided in rounds of questions; the result is a record of decisions and a roadmap in `docs/investigations/<slug>/`, from which tickets are cut.
2. `/spec <TICKET> [short title]`: what changes and why, in `docs/specs/<TICKET>-<slug>/spec.md`. A person approves it by setting `status: approved`.
3. `/plan <TICKET>`: how it changes, in `plan.md` next to the spec: facts with file references, the proposal, the files to change, how existing data and behavior are preserved, verification, and the tasks split into sessions. A person approves it.
4. `/implement <TICKET> [S<n> | T<n>] [what to fix]`: one session of the plan per run, with scoped verification after each task, a self-review at the end and the results written into the plan. A person checks the result between sessions.
5. `/review [<TICKET>] [local | HEAD | <branch>] [what the change is for]`: the change against the spec and the plan, or against the project rules when there is no spec. It reports findings and changes nothing.

Agents never commit, push or open pull requests on their own. Approval is recorded in the files, so it survives sessions and tools.

The rules are in [AGENTS.md](AGENTS.md); the ticketed process, statuses, sessions and review findings in [docs/specs/README.md](docs/specs/README.md); investigations in [docs/investigations/README.md](docs/investigations/README.md); a finished ticket in [docs/specs/_example/](docs/specs/_example/).

## Layout

```
AGENTS.md                         rules for agents; section 9 is project-specific
.claude/settings.json             shared Claude Code permissions (allow and deny rules)
.claude/skills/<skill>/SKILL.md   the five skills for Claude Code
.agents/skills/<skill>/           the same skills for Codex (identical bodies)
docs/adr/_template.md             architecture decision records
docs/specs/README.md              the ticketed process
docs/specs/_template/             spec.md and plan.md
docs/specs/_example/              a finished fictional ticket
docs/specs/_tools/                validate.py and its tests
docs/investigations/README.md     investigations before a ticket
docs/investigations/_template/    investigation.md and roadmap.md
```

## Installation

1. Copy `AGENTS.md`, `.claude/`, `.agents/` and `docs/` into the root of your repository. Merge `.gitignore` with yours: it ignores `.DS_Store`, `.env` files except `.env.example`, `.claude/settings.local.json`, `CLAUDE.local.md` and `__pycache__/`.
2. Fill the placeholders in `AGENTS.md`:
   - section 7: replace `<chat language>` with the language the agent should use in chat (for example `English`); everything in the repository stays in English, which the skills and the validator assume;
   - section 9: stack and versions, commands (linter, type check, tests, build, and the scoped test command), the known baseline of failing checks, layout, conventions and project-specific spec triggers, the ticket key format, the integration branch, the protected branches, what not to touch, environments.
3. For each protected branch other than `main`, add the same deny rules as for `main` to `.claude/settings.json` (see "Permissions" in `docs/specs/README.md`).
4. In Claude Code, open a new session in the repository and check that `AGENTS.md` was read: the session prints `AGENTS.md loaded: <path>` at the start, and `/memory` lists its path. If it was not read, import it from a `CLAUDE.md` whose first line is `@AGENTS.md`; the details are under "Tooling" in `docs/specs/README.md`. Codex reads `AGENTS.md` natively and caps it at 32 KiB by default.
5. Run the validator (see Checks).

Existing tickets, ADRs and investigations of the project live next to the templates: `docs/specs/<TICKET>-<slug>/`, `docs/adr/0001-<slug>.md`, `docs/investigations/<slug>/`. The validator checks them all.

## Checks

Python 3.8 or later with the standard library only.

```bash
python3 docs/specs/_tools/validate.py
```

```bash
python3 -m unittest discover -s docs/specs/_tools
```

The validator checks the two copies of each skill, the statuses and front matter of every document, the tasks and sessions of every plan, and the ADR and investigation folders; it prints every problem and exits with 1, or prints `ok`. The tests run it on a copy of the kit through the lifecycle scenarios of the process. Run both after changing skills, templates or statuses. These checks are structural: they do not run the process itself.

## Changing the kit

A rule has one home (AGENTS.md, section 0): `AGENTS.md` for the rules, the two READMEs for the process, the templates for the document formats. A skill applies them and a README explains them; neither redefines them. A change to a rule includes the places that apply or explain it, the templates, the example and the validator, and the skill bodies in `.claude/skills/` and `.agents/skills/` stay identical.

## Author and license

Made by OleksandrMrn. Released under the MIT License, see [LICENSE](LICENSE).

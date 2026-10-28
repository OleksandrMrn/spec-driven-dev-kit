"""Checks of the spec-driven kit: skill copies, statuses, ticket folders and their sessions, investigation folders and ADRs.

Usage: python3 docs/specs/_tools/validate.py [repository root]
Prints every problem found and exits with 1, or prints "ok" and exits with 0.
The rules checked here are described in docs/specs/README.md.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

SPEC_STATUSES = ("draft", "approved", "done", "rejected")
PLAN_STATUSES = ("draft", "approved", "implemented")
ADR_STATUSES = ("proposed", "accepted", "superseded", "deprecated")
INVESTIGATION_STATUSES = ("draft", "ready", "parked", "rejected")
COVERAGE_STATUSES = ("open", "covered", "n/a")

KIT_SKILLS = ("spec", "plan", "implement", "review", "investigate")
CLAUDE_SKILL_KEYS = {"name", "description", "argument-hint", "disable-model-invocation"}
CODEX_SKILL_KEYS = {"name", "description"}
CODEX_POLICY = "policy:\n  allow_implicit_invocation: false\n"

SPEC_TEMPLATE = "docs/specs/_template/spec.md"
PLAN_TEMPLATE = "docs/specs/_template/plan.md"
ADR_TEMPLATE = "docs/adr/_template.md"
INVESTIGATION_TEMPLATE = "docs/investigations/_template/investigation.md"
ROADMAP_TEMPLATE = "docs/investigations/_template/roadmap.md"
README = "docs/specs/README.md"
INVESTIGATIONS_README = "docs/investigations/README.md"
FORMAT_NOTE = "front matter format: docs/specs/README.md, Checks"

ADR_FILE_NAME = re.compile(r"(\d{4})-.+\.md")
STATUS_ROW = re.compile(r"\| `([a-z]+)` \|")
HEADING = re.compile(r"(#+) ")
QUOTED = re.compile(r"""(["']).*\1""")
DECISION = re.compile(r"- D\d+\b")
STEP = re.compile(r"- S\d+\.")
ITEM = re.compile(r"- \S")
TASK = re.compile(r"- \[([ x])\] T(\d+)\b")
SESSION = re.compile(r"- S(\d+) \((.*?)\):")
TASK_RANGE = re.compile(r"T(\d+)(?:\s*[–-]\s*T(\d+))?")
CHECK = re.compile(r"\s+- Check:(.*)")
CHECKED = re.compile(r"\s+- Checked:(.*)")
CHECKED_VALUE = re.compile(r".+, \d{4}-\d{2}-\d{2}")


class Document:
    """A Markdown file whose front matter has one `key: value` per line.

    This is a restricted format, not YAML: a value is read as plain text up to an
    optional ` #` comment; quoting, lists, nesting and multi-line values are not parsed.
    """

    def __init__(self, path: Path):
        lines = path.read_text().split("\n")
        if not lines or lines[0] != "---" or "---" not in lines[1:]:
            raise ValueError("no front matter between two '---' lines")
        end = lines.index("---", 1)
        self.fields: dict[str, str] = {}
        self.comments: dict[str, str] = {}
        for number, line in enumerate(lines[1:end], start=2):
            key, sep, rest = line.partition(":")
            if not sep or not key.strip() or line != line.lstrip():
                raise ValueError(f"line {number} {line!r} is not 'key: value' ({FORMAT_NOTE})")
            value, _, comment = rest.partition(" #")
            self.fields[key.strip()] = value.strip()
            self.comments[key.strip()] = comment.strip()
        self.body = "\n".join(lines[end + 1:])

    def section(self, heading: str) -> list[str] | None:
        return section(self.body, heading)

    def headings(self) -> list[str]:
        return [line for line in self.body.split("\n") if line.startswith("## ")]


def section(text: str, heading: str) -> list[str] | None:
    """Lines under `heading` up to the next heading of the same or a higher level."""
    lines = text.split("\n")
    if heading not in lines:
        return None
    level = len(HEADING.match(heading).group(1))
    content = []
    for line in lines[lines.index(heading) + 1:]:
        match = HEADING.match(line)
        if match and len(match.group(1)) <= level:
            break
        content.append(line)
    return content


def filled_lines(document: Document, template: Document, heading: str) -> list[str]:
    """Lines under `heading` that are neither empty nor copied from the template; empty when the section is missing."""
    template_lines = template.section(heading) or []
    return [line for line in document.section(heading) or [] if line.strip() and line not in template_lines]


def entries(document: Document, template: Document, heading: str, pattern: re.Pattern[str]) -> list[str]:
    """The filled lines under `heading` that start like `pattern`: the entries of a list section."""
    return [line for line in filled_lines(document, template, heading) if pattern.match(line)]


def relative(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def load(root: Path, path: Path, problems: list[str]) -> Document | None:
    if not path.is_file():
        problems.append(f"{relative(root, path)}: missing")
        return None
    try:
        return Document(path)
    except ValueError as error:
        problems.append(f"{relative(root, path)}: {error}")
        return None


def check_plain_values(where: str, document: Document) -> list[str]:
    problems = [
        f"{where}: the value of {key} is quoted; write '{key}: {value[1:-1]}' ({FORMAT_NOTE})"
        for key, value in document.fields.items()
        if QUOTED.fullmatch(value)
    ]
    return problems + check_yaml_safe_values(where, document)


def check_yaml_safe_values(where: str, document: Document) -> list[str]:
    """A plain value with ': ' inside, or ':' at the end, is rejected by the YAML parsers that load skill metadata."""
    return [
        f"{where}: the value of {key} contains ': ' or ends with ':', which a YAML parser rejects; rephrase it ({FORMAT_NOTE})"
        for key, value in document.fields.items()
        if ": " in value or value.endswith(":")
    ]


def check_skills(root: Path) -> list[str]:
    """Checks the kit's own skills; other skills of the project, in one tool or both, are left alone."""
    problems: list[str] = []
    for name in KIT_SKILLS:
        problems += compare_skill(root, name)
        policy = root / ".agents/skills" / name / "agents/openai.yaml"
        if not policy.is_file() or policy.read_text() != CODEX_POLICY:
            problems.append(f"{relative(root, policy)}: must be exactly {CODEX_POLICY!r}")
    return problems


def compare_skill(root: Path, name: str) -> list[str]:
    problems: list[str] = []
    claude_path = root / ".claude/skills" / name / "SKILL.md"
    codex_path = root / ".agents/skills" / name / "SKILL.md"
    claude = load(root, claude_path, problems)
    codex = load(root, codex_path, problems)
    if claude is None or codex is None:
        return problems
    for document, path, keys in ((claude, claude_path, CLAUDE_SKILL_KEYS), (codex, codex_path, CODEX_SKILL_KEYS)):
        if set(document.fields) != keys:
            problems.append(f"{relative(root, path)}: front matter keys {sorted(document.fields)}, expected {sorted(keys)}")
        if document.fields.get("name") != name:
            problems.append(f"{relative(root, path)}: name {document.fields.get('name')!r}, expected {name!r}")
        problems += check_yaml_safe_values(relative(root, path), document)
    if claude.fields.get("disable-model-invocation") != "true":
        problems.append(f"{relative(root, claude_path)}: disable-model-invocation must be true")
    if not claude.fields.get("argument-hint"):
        problems.append(f"{relative(root, claude_path)}: argument-hint is empty")
    if claude.fields.get("description") != codex.fields.get("description"):
        problems.append(f"{relative(root, codex_path)}: description differs from {relative(root, claude_path)}")
    if claude.body != codex.body:
        problems.append(f"{relative(root, codex_path)}: body differs from {relative(root, claude_path)}")
    return problems


def check_documented_statuses(root: Path) -> list[str]:
    problems: list[str] = []
    for template, expected in (
        (SPEC_TEMPLATE, SPEC_STATUSES),
        (PLAN_TEMPLATE, PLAN_STATUSES),
        (ADR_TEMPLATE, ADR_STATUSES),
        (INVESTIGATION_TEMPLATE, INVESTIGATION_STATUSES),
    ):
        document = load(root, root / template, problems)
        if document is None:
            continue
        listed = tuple(status.strip() for status in document.comments.get("status", "").split("|"))
        if listed != expected:
            problems.append(f"{template}: status comment lists {' | '.join(listed)}, expected {' | '.join(expected)}")
        if document.fields.get("status") != expected[0]:
            problems.append(f"{template}: status {document.fields.get('status')!r}, expected {expected[0]!r}")
    problems += check_status_tables(root, README, (("### Spec statuses", SPEC_STATUSES), ("### Plan statuses", PLAN_STATUSES)))
    problems += check_status_tables(root, INVESTIGATIONS_README, (("## Statuses", INVESTIGATION_STATUSES),))
    return problems


def check_status_tables(root: Path, readme: str, tables: tuple[tuple[str, tuple[str, ...]], ...]) -> list[str]:
    """Checks that each status table of `readme` lists exactly the expected statuses, in order."""
    path = root / readme
    if not path.is_file():
        return [f"{readme}: missing"]
    problems: list[str] = []
    text = path.read_text()
    for heading, expected in tables:
        lines = section(text, heading)
        if lines is None:
            problems.append(f"{readme}: no section {heading!r}")
            continue
        listed = tuple(match.group(1) for line in lines if (match := STATUS_ROW.match(line)))
        if listed != expected:
            problems.append(f"{readme}: {heading!r} lists {', '.join(listed)}, expected {', '.join(expected)}")
    return problems


def ticket_folders(root: Path) -> list[Path]:
    specs = root / "docs/specs"
    folders = [path for path in specs.iterdir() if path.is_dir() and not path.name.startswith("_")]
    example = specs / "_example"
    if example.is_dir():
        folders += [path for path in example.iterdir() if path.is_dir()]
    return sorted(folders)


def check_ticket_folders(root: Path) -> list[str]:
    problems: list[str] = []
    templates = {name: load(root, root / path, problems) for name, path in (("spec", SPEC_TEMPLATE), ("plan", PLAN_TEMPLATE))}
    if None in templates.values():
        return problems
    folders_by_ticket: dict[tuple[Path, str], list[str]] = {}
    for folder in ticket_folders(root):
        ticket = check_ticket_folder(root, folder, templates["spec"], templates["plan"], problems)
        if ticket:
            folders_by_ticket.setdefault((folder.parent, ticket), []).append(folder.name)
    for (parent, ticket), names in sorted(folders_by_ticket.items()):
        if len(names) > 1:
            problems.append(f"{relative(root, parent)}: ticket {ticket} has several folders: {', '.join(names)}")
    return problems


def check_ticket_folder(root: Path, folder: Path, spec_template: Document, plan_template: Document, problems: list[str]) -> str | None:
    """Checks one ticket folder and returns its ticket, or None when the spec cannot be read."""
    spec_path = folder / "spec.md"
    plan_path = folder / "plan.md"
    spec = load(root, spec_path, problems)
    if spec is None:
        return None
    where = relative(root, spec_path)
    problems += check_plain_values(where, spec)
    if set(spec.fields) != set(spec_template.fields):
        problems.append(f"{where}: front matter keys {sorted(spec.fields)}, expected {sorted(spec_template.fields)}")
    ticket = spec.fields.get("ticket", "")
    if not ticket or not folder.name.startswith(f"{ticket}-") or folder.name == f"{ticket}-":
        problems.append(f"{relative(root, folder)}: folder name must be '{ticket or '<ticket>'}-<slug>'")
    spec_status = spec.fields.get("status")
    if spec_status not in SPEC_STATUSES:
        problems.append(f"{where}: status {spec_status!r} is not one of {', '.join(SPEC_STATUSES)}")
    if spec_status in ("approved", "done") and not (spec.fields.get("approved_by") and spec.fields.get("date")):
        problems.append(f"{where}: an {spec_status} spec needs approved_by and date")
    if not plan_path.is_file():
        if spec_status == "done":
            problems.append(f"{where}: the spec is done but there is no plan.md")
        return ticket
    plan = load(root, plan_path, problems)
    if plan is None:
        return ticket
    where = relative(root, plan_path)
    problems += check_plain_values(where, plan)
    if set(plan.fields) != set(plan_template.fields):
        problems.append(f"{where}: front matter keys {sorted(plan.fields)}, expected {sorted(plan_template.fields)}")
    if plan.fields.get("ticket") != ticket:
        problems.append(f"{where}: ticket {plan.fields.get('ticket')!r}, the spec has {ticket!r}")
    if plan.fields.get("spec") != plan_template.fields["spec"]:
        problems.append(f"{where}: spec {plan.fields.get('spec')!r}, expected {plan_template.fields['spec']!r}, the spec next to the plan")
    plan_status = plan.fields.get("status")
    if plan_status not in PLAN_STATUSES:
        problems.append(f"{where}: status {plan_status!r} is not one of {', '.join(PLAN_STATUSES)}")
        return ticket
    task_list = tasks(plan)
    problems += check_tasks(where, task_list)
    problems += check_sessions(where, plan, task_list)
    if plan_status in ("approved", "implemented") and spec_status not in ("approved", "done"):
        problems.append(f"{where}: the plan is {plan_status} but the spec is {spec_status}; a changed spec resets its plan to draft")
    if spec_status == "done" and plan_status != "implemented":
        problems.append(f"{where}: the spec is done but the plan is {plan_status}")
    if plan_status == "implemented":
        problems += check_implemented_plan(where, plan, plan_template)
    return ticket


def tasks(plan: Document) -> list[tuple[int, bool]]:
    """(number, ticked) of every task under '## Tasks', in order."""
    return [(int(match.group(2)), match.group(1) == "x") for line in plan.section("## Tasks") or [] if (match := TASK.match(line))]


def check_tasks(where: str, task_list: list[tuple[int, bool]]) -> list[str]:
    if not task_list:
        return [f"{where}: 'Tasks' has no entry like '- [ ] T1 (R1, AC1): <task>'"]
    if [number for number, _ in task_list] != list(range(1, len(task_list) + 1)):
        return [f"{where}: the tasks must be T1, T2, … in order"]
    return []


@dataclass
class Session:
    number: int
    tasks: list[int] = field(default_factory=list)
    check: list[str] = field(default_factory=list)
    checked: list[str] = field(default_factory=list)


def sessions(where: str, lines: list[str], problems: list[str]) -> list[Session]:
    """The entries under '## Sessions' with their tasks and every 'Check' and 'Checked' line they have."""
    entries: list[Session] = []
    for line in lines:
        if match := SESSION.match(line):
            session = Session(int(match.group(1)))
            for item in match.group(2).split(","):
                span = TASK_RANGE.fullmatch(item.strip())
                if span is None:
                    problems.append(f"{where}: S{session.number} lists {item.strip()!r}, expected T<n> or T<n>–T<m>")
                    continue
                first, last = int(span.group(1)), int(span.group(2) or span.group(1))
                if last < first:
                    problems.append(f"{where}: S{session.number} lists {item.strip()!r}, a range that goes backwards")
                    continue
                session.tasks += range(first, last + 1)
            entries.append(session)
        elif entries and (match := CHECK.match(line)):
            entries[-1].check.append(match.group(1).strip())
        elif entries and (match := CHECKED.match(line)):
            entries[-1].checked.append(match.group(1).strip())
    return entries


def check_sessions(where: str, plan: Document, task_list: list[tuple[int, bool]]) -> list[str]:
    """Every task in exactly one session, the sessions in order, one 'Check' with text and one 'Checked' per session, filled only when its tasks are all ticked."""
    lines = plan.section("## Sessions")
    if lines is None:
        return [f"{where}: no section '## Sessions'"]
    problems: list[str] = []
    entries = sessions(where, lines, problems)
    if not entries:
        return problems + [f"{where}: 'Sessions' has no entry like '- S1 (T1–T2): <what works after it>'"]
    if [session.number for session in entries] != list(range(1, len(entries) + 1)):
        problems.append(f"{where}: the sessions must be S1, S2, … in order")
    numbers = list(dict.fromkeys(number for number, _ in task_list))
    ticked = {number for number, is_ticked in task_list if is_ticked}
    taken = [task for session in entries for task in session.tasks]
    for session in entries:
        problems += [f"{where}: S{session.number} lists T{task}, which is not in 'Tasks'" for task in session.tasks if task not in numbers]
        if len(session.check) != 1:
            problems.append(f"{where}: S{session.number} needs exactly one 'Check' line, found {len(session.check)}")
        elif not session.check[0]:
            problems.append(f"{where}: 'Check' of S{session.number} is empty")
        if len(session.checked) != 1:
            problems.append(f"{where}: S{session.number} needs exactly one 'Checked' line, found {len(session.checked)}")
        elif session.checked[0]:
            if not CHECKED_VALUE.fullmatch(session.checked[0]):
                problems.append(f"{where}: 'Checked' of S{session.number} must be '<name>, <YYYY-MM-DD>'")
            problems += [f"{where}: S{session.number} is checked but T{task} is unticked" for task in session.tasks if task in numbers and task not in ticked]
    for task in numbers:
        if task not in taken:
            problems.append(f"{where}: T{task} is in no session")
        elif taken.count(task) > 1:
            problems.append(f"{where}: T{task} is in more than one session")
    if sorted(taken) == sorted(numbers) and taken != numbers:
        problems.append(f"{where}: the sessions do not take the tasks in the order of 'Tasks'")
    return problems


def check_implemented_plan(where: str, plan: Document, plan_template: Document) -> list[str]:
    problems: list[str] = []
    tasks = plan.section("## Tasks")
    if tasks is None:
        return [f"{where}: no section '## Tasks'"]
    unticked = [line for line in tasks if line.startswith("- [ ]")]
    ticked = [line for line in tasks if line.startswith("- [x]")]
    if unticked:
        problems.append(f"{where}: the plan is implemented but {len(unticked)} task(s) are unticked")
    if not ticked:
        problems.append(f"{where}: the plan is implemented but has no ticked tasks")
    if not filled_lines(plan, plan_template, "## Results and deviations"):
        problems.append(f"{where}: the plan is implemented but 'Results and deviations' is not filled")
    return problems


def investigation_folders(root: Path) -> list[Path]:
    investigations = root / "docs/investigations"
    if not investigations.is_dir():
        return []
    return sorted(path for path in investigations.iterdir() if path.is_dir() and not path.name.startswith("_"))


def check_investigation_folders(root: Path) -> list[str]:
    problems: list[str] = []
    templates = {name: load(root, root / path, problems) for name, path in (("investigation", INVESTIGATION_TEMPLATE), ("roadmap", ROADMAP_TEMPLATE))}
    if None in templates.values():
        return problems
    for folder in investigation_folders(root):
        check_investigation_folder(root, folder, templates["investigation"], templates["roadmap"], problems)
    return problems


def check_investigation_folder(root: Path, folder: Path, investigation_template: Document, roadmap_template: Document, problems: list[str]) -> None:
    """Checks one investigation folder: its investigation.md and, when present, its roadmap.md."""
    investigation_path = folder / "investigation.md"
    roadmap_path = folder / "roadmap.md"
    investigation = load(root, investigation_path, problems)
    if investigation is None:
        return
    where = relative(root, investigation_path)
    problems += check_plain_values(where, investigation)
    if set(investigation.fields) != set(investigation_template.fields):
        problems.append(f"{where}: front matter keys {sorted(investigation.fields)}, expected {sorted(investigation_template.fields)}")
    if investigation.fields.get("slug") != folder.name:
        problems.append(f"{where}: slug {investigation.fields.get('slug')!r} differs from the folder name {folder.name!r}")
    status = investigation.fields.get("status")
    if status not in INVESTIGATION_STATUSES:
        problems.append(f"{where}: status {status!r} is not one of {', '.join(INVESTIGATION_STATUSES)}")
    coverage = investigation.section("## Coverage")
    rows = coverage_rows(coverage or [])
    for area, state in rows:
        if state not in COVERAGE_STATUSES:
            problems.append(f"{where}: coverage of {area!r} is {state!r}, not one of {', '.join(COVERAGE_STATUSES)}")
    if coverage is None:
        problems.append(f"{where}: no section '## Coverage'")
    else:
        problems += check_coverage_areas(where, rows, coverage_rows(investigation_template.section("## Coverage") or []))
    if status == "ready":
        problems += check_ready_investigation(where, investigation, investigation_template, rows)
        if not roadmap_path.is_file():
            problems.append(f"{where}: the investigation is ready but there is no roadmap.md")
    if not roadmap_path.is_file():
        return
    roadmap = load(root, roadmap_path, problems)
    if roadmap is None:
        return
    where = relative(root, roadmap_path)
    problems += check_plain_values(where, roadmap)
    if set(roadmap.fields) != set(roadmap_template.fields):
        problems.append(f"{where}: front matter keys {sorted(roadmap.fields)}, expected {sorted(roadmap_template.fields)}")
    if roadmap.fields.get("slug") != folder.name:
        problems.append(f"{where}: slug {roadmap.fields.get('slug')!r} differs from the folder name {folder.name!r}")
    if roadmap.fields.get("investigation") != roadmap_template.fields["investigation"]:
        problems.append(f"{where}: investigation {roadmap.fields.get('investigation')!r}, expected {roadmap_template.fields['investigation']!r}, the investigation next to the roadmap")
    if status == "ready":
        problems += check_ready_roadmap(where, roadmap, roadmap_template)


def coverage_rows(lines: list[str]) -> list[tuple[str, str]]:
    """(area, status) of each row of the coverage table, without its header and separator."""
    rows: list[tuple[str, str]] = []
    for line in lines:
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 2 or cells[0] == "Area" or set(cells[0]) <= set("-: "):
            continue
        rows.append((cells[0], cells[1]))
    return rows


def check_coverage_areas(where: str, rows: list[tuple[str, str]], template_rows: list[tuple[str, str]]) -> list[str]:
    """Every area of the template is listed exactly once; a project may add areas of its own."""
    problems: list[str] = []
    areas = [area for area, _ in rows]
    missing = [area for area, _ in template_rows if area not in areas]
    duplicates = list(dict.fromkeys(area for area in areas if areas.count(area) > 1))
    if missing:
        problems.append(f"{where}: 'Coverage' lacks the area(s) of the template: {', '.join(missing)}")
    if duplicates:
        problems.append(f"{where}: 'Coverage' lists {', '.join(duplicates)} more than once")
    return problems


def check_ready_investigation(where: str, investigation: Document, template: Document, rows: list[tuple[str, str]]) -> list[str]:
    """What `status: ready` needs in investigation.md: a date, no open area, a decision."""
    problems: list[str] = []
    if not investigation.fields.get("date"):
        problems.append(f"{where}: a ready investigation needs date")
    open_areas = [area for area, state in rows if state == "open"]
    if open_areas:
        problems.append(f"{where}: the investigation is ready but {len(open_areas)} area(s) are still open: {', '.join(open_areas)}")
    if not entries(investigation, template, "## Decisions", DECISION):
        problems.append(f"{where}: the investigation is ready but 'Decisions' has no entry like '- D1 (<date>). <question>'")
    return problems


def check_ready_roadmap(where: str, roadmap: Document, template: Document) -> list[str]:
    """What `status: ready` needs in roadmap.md: a step and a candidate ticket."""
    return [
        f"{where}: the investigation is ready but {heading[3:]!r} has no entry like {example!r}"
        for heading, pattern, example in (("## Phases", STEP, "- S1. <step>"), ("## Candidate tickets", ITEM, "- <title>: <goal>"))
        if not entries(roadmap, template, heading, pattern)
    ]


def check_example(root: Path) -> list[str]:
    problems: list[str] = []
    example = root / "docs/specs/_example"
    if not example.is_dir():
        return problems
    for folder in sorted(path for path in example.iterdir() if path.is_dir()):
        for name, template_path in (("spec.md", SPEC_TEMPLATE), ("plan.md", PLAN_TEMPLATE)):
            template = load(root, root / template_path, problems)
            document = load(root, folder / name, problems)
            if template is None or document is None:
                continue
            if document.headings() != template.headings():
                problems.append(f"{relative(root, folder / name)}: sections {document.headings()} differ from {template_path}: {template.headings()}")
    return problems


def check_adrs(root: Path) -> list[str]:
    problems: list[str] = []
    adr_dir = root / "docs/adr"
    template = load(root, root / ADR_TEMPLATE, problems)
    if template is None:
        return problems
    adrs: dict[str, tuple[str, Document]] = {}
    for path in sorted(adr_dir.glob("*.md")):
        if path.name.startswith("_"):
            continue
        where = relative(root, path)
        match = ADR_FILE_NAME.fullmatch(path.name)
        if not match:
            problems.append(f"{where}: the name must be '0001-<slug>.md'")
            continue
        adr = load(root, path, problems)
        if adr is None:
            continue
        problems += check_plain_values(where, adr)
        if set(adr.fields) != set(template.fields):
            problems.append(f"{where}: front matter keys {sorted(adr.fields)}, expected {sorted(template.fields)}")
        if adr.fields.get("id") != match.group(1):
            problems.append(f"{where}: id {adr.fields.get('id')!r} differs from the number in the file name")
        if adr.fields.get("status") not in ADR_STATUSES:
            problems.append(f"{where}: status {adr.fields.get('status')!r} is not one of {', '.join(ADR_STATUSES)}")
        if match.group(1) in adrs:
            problems.append(f"{where}: number {match.group(1)} is also used by {adrs[match.group(1)][0]}")
            continue
        adrs[match.group(1)] = (where, adr)
    for where, adr in adrs.values():
        old = adr.fields.get("supersedes")
        if not old:
            continue
        if old not in adrs:
            problems.append(f"{where}: supersedes {old!r}, which does not exist")
        elif adr.fields.get("status") == "accepted" and adrs[old][1].fields.get("status") != "superseded":
            problems.append(f"{adrs[old][0]}: superseded by {where}, so its status must be superseded")
    return problems


def validate(root: Path) -> list[str]:
    return (
        check_skills(root)
        + check_documented_statuses(root)
        + check_ticket_folders(root)
        + check_investigation_folders(root)
        + check_example(root)
        + check_adrs(root)
    )


def main(argv: list[str]) -> int:
    root = Path(argv[1]).resolve() if len(argv) > 1 else Path(__file__).resolve().parents[3]
    problems = validate(root)
    for problem in problems:
        print(problem)
    print(f"{len(problems)} problem(s)" if problems else "ok")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

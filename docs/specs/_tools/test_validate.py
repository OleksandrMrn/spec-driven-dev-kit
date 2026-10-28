"""Tests of validate.py on a copy of the kit.

Run from the repository root: python3 -m unittest discover -s docs/specs/_tools
The copy holds the kit's own files and the example, not the project's tickets, ADRs and
investigations: the tests write their own, with fixed names and numbers.
The ticket tests follow the lifecycle scenarios of docs/specs/README.md, the investigation
tests those of docs/investigations/README.md.
"""

from __future__ import annotations

import re
import shutil
import tempfile
import unittest
from pathlib import Path

import validate

KIT_ROOT = Path(__file__).resolve().parents[3]
KIT_PARTS = ("AGENTS.md", ".claude", ".agents", "docs")


def strip_project_documents(root: Path) -> None:
    """Removes the project's tickets, ADRs and investigations from the copy: the tests write their own, with fixed names and numbers, and check the kit, not the project."""
    for folder in (root / "docs/specs").iterdir():
        if folder.is_dir() and not folder.name.startswith("_"):
            shutil.rmtree(folder)
    for file in (root / "docs/adr").glob("*.md"):
        if not file.name.startswith("_"):
            file.unlink()
    for folder in (root / "docs/investigations").iterdir():
        if folder.is_dir() and not folder.name.startswith("_"):
            shutil.rmtree(folder)


class KitTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        for part in KIT_PARTS:
            source = KIT_ROOT / part
            if source.is_dir():
                shutil.copytree(source, self.root / part, ignore=shutil.ignore_patterns("__pycache__", ".DS_Store"))
            else:
                shutil.copy2(source, self.root / part)
        strip_project_documents(self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def edit(self, path: str, old: str, new: str):
        file = self.root / path
        text = file.read_text()
        self.assertIn(old, text)
        file.write_text(text.replace(old, new, 1))

    def assertValid(self):
        self.assertEqual(validate.validate(self.root), [])

    def assertProblem(self, fragment: str):
        problems = validate.validate(self.root)
        self.assertTrue(any(fragment in problem for problem in problems), problems)

    def make_ticket(self, folder: str, spec_status: str, plan_status: str | None = None, tasks: str = "  ",
                    results: bool = False, ticket: str = "XYZ-1", approved: bool = True, checked: str = ""):
        """Writes a ticket folder from the templates; `tasks` holds the tick marks of T1 and T2, `checked` fills the 'Checked' of S1."""
        path = self.root / "docs/specs" / folder
        path.mkdir()
        spec = (self.root / validate.SPEC_TEMPLATE).read_text()
        # the placeholder after "ticket:" is the project's choice (AGENTS.md section 9), so the whole value is replaced
        spec = re.sub(r"^ticket: .*$", f"ticket: {ticket}", spec, count=1, flags=re.M)
        spec = re.sub(r"^status: draft", f"status: {spec_status}", spec, flags=re.M)
        if approved:
            spec = spec.replace("approved_by:\n", "approved_by: R. Reviewer\n").replace("date:\n", "date: 2026-01-02\n")
        (path / "spec.md").write_text(spec)
        if plan_status is None:
            return
        plan = (self.root / validate.PLAN_TEMPLATE).read_text()
        plan = re.sub(r"^ticket: .*$", f"ticket: {ticket}", plan, count=1, flags=re.M)
        plan = re.sub(r"^status: draft", f"status: {plan_status}", plan, flags=re.M)
        plan = plan.replace("- [ ] T1", f"- [{tasks[0]}] T1").replace("- [ ] T2", f"- [{tasks[1]}] T2")
        if checked:
            plan = plan.replace("  - Checked:\n", f"  - Checked: {checked}\n")
        if results:
            plan += "\nRun 1: typecheck, lint and tests passed.\n"
        (path / "plan.md").write_text(plan)

    def make_adr(self, name: str, adr_id: str, status: str, supersedes: str = ""):
        adr = (self.root / validate.ADR_TEMPLATE).read_text()
        adr = adr.replace("id: 0000", f"id: {adr_id}")
        adr = re.sub(r"^status: proposed", f"status: {status}", adr, flags=re.M)
        adr = adr.replace("supersedes:\n", f"supersedes: {supersedes}\n")
        (self.root / "docs/adr" / name).write_text(adr)

    def make_investigation(self, folder: str, status: str, roadmap: bool = False, slug: str | None = None, filled: bool = False):
        """Writes an investigation folder from the templates; `filled` gives it what `ready` needs."""
        slug = folder if slug is None else slug
        path = self.root / "docs/investigations" / folder
        path.mkdir()
        investigation = (self.root / validate.INVESTIGATION_TEMPLATE).read_text()
        investigation = investigation.replace("slug: <slug>", f"slug: {slug}")
        investigation = re.sub(r"^status: draft", f"status: {status}", investigation, flags=re.M)
        (path / "investigation.md").write_text(investigation)
        if filled:
            self.fill_investigation(folder)
        if roadmap:
            self.make_roadmap(folder, slug, filled)

    def fill_investigation(self, folder: str):
        """A date, every area covered and one decision: what `ready` needs in investigation.md."""
        path = f"docs/investigations/{folder}/investigation.md"
        self.edit(path, "date:\n", "date: 2026-01-02\n")
        file = self.root / path
        file.write_text(file.read_text().replace("| open |", "| covered |"))
        self.edit(path, "## Decisions\n", "## Decisions\n\n- D0 (2026-01-02). First version? Options: a) web; b) mobile. Choice: a. Why: the users are on desktop.\n")

    def make_roadmap(self, folder: str, slug: str, filled: bool = False):
        text = (self.root / validate.ROADMAP_TEMPLATE).read_text().replace("slug: <slug>", f"slug: {slug}")
        (self.root / "docs/investigations" / folder / "roadmap.md").write_text(text)
        if filled:
            self.fill_roadmap(folder)

    def fill_roadmap(self, folder: str):
        """A step and a candidate ticket: what `ready` needs in roadmap.md."""
        path = f"docs/investigations/{folder}/roadmap.md"
        self.edit(path, "## Phases\n", "## Phases\n\n- S0. Web client. Why: D0. Depends on: none. Realizes: D0. Verified by: a smoke test.\n")
        self.edit(path, "## Candidate tickets\n", "## Candidate tickets\n\n- Web client: the first version; realizes D0; steps S0.\n")

class KitTest(KitTestCase):
    def test_kit_is_valid(self):
        self.assertValid()


class SkillTest(KitTestCase):
    def test_codex_body_must_match(self):
        self.edit(".agents/skills/plan/SKILL.md", "No code changes.", "No changes.")
        self.assertProblem(".agents/skills/plan/SKILL.md: body differs")

    def test_codex_description_must_match(self):
        self.edit(".agents/skills/spec/SKILL.md", "description: Create", "description: Make")
        self.assertProblem(".agents/skills/spec/SKILL.md: description differs")

    def test_skill_must_exist_in_both_folders(self):
        shutil.rmtree(self.root / ".agents/skills/review")
        self.assertProblem(".agents/skills/review/SKILL.md: missing")

    def test_kit_skill_removed_from_both_folders(self):
        shutil.rmtree(self.root / ".claude/skills/review")
        shutil.rmtree(self.root / ".agents/skills/review")
        self.assertProblem(".claude/skills/review/SKILL.md: missing")
        self.assertProblem(".agents/skills/review/SKILL.md: missing")

    def test_project_skills_outside_the_kit_are_not_checked(self):
        deploy = self.root / ".claude/skills/deploy"
        deploy.mkdir()
        (deploy / "SKILL.md").write_text("---\nname: deploy\ndescription: Deploy the project.\n---\n\nDeploy.\n")
        self.assertValid()

    def test_claude_skill_is_invoked_explicitly(self):
        self.edit(".claude/skills/implement/SKILL.md", "disable-model-invocation: true", "disable-model-invocation: false")
        self.assertProblem("disable-model-invocation must be true")

    def test_codex_skill_is_invoked_explicitly(self):
        self.edit(".agents/skills/implement/agents/openai.yaml", "false", "true")
        self.assertProblem(".agents/skills/implement/agents/openai.yaml: must be exactly")

    def test_investigate_skill_is_part_of_the_kit(self):
        shutil.rmtree(self.root / ".agents/skills/investigate")
        self.assertProblem(".agents/skills/investigate/SKILL.md: missing")

    def test_investigate_codex_body_must_match(self):
        self.edit(".agents/skills/investigate/SKILL.md", "No commits.", "No commit.")
        self.assertProblem(".agents/skills/investigate/SKILL.md: body differs")

    def test_skill_description_is_yaml_safe(self):
        for path in (".claude/skills/investigate/SKILL.md", ".agents/skills/investigate/SKILL.md"):
            self.edit(path, "no ticket yet. Research", "no ticket yet: research")
        self.assertProblem(".claude/skills/investigate/SKILL.md: the value of description contains ': ' or ends with ':', which a YAML parser rejects")


class DocumentedStatusTest(KitTestCase):
    def test_spec_template_lists_spec_statuses(self):
        self.edit(validate.SPEC_TEMPLATE, "# draft | approved | done", "# draft | approved | implemented | done")
        self.assertProblem(f"{validate.SPEC_TEMPLATE}: status comment lists")

    def test_readme_lists_plan_statuses(self):
        self.edit(validate.README, "| `implemented` |", "| `finished` |")
        self.assertProblem("'### Plan statuses' lists")

    def test_investigation_template_lists_investigation_statuses(self):
        self.edit(validate.INVESTIGATION_TEMPLATE, "# draft | ready | parked", "# draft | ready | done | parked")
        self.assertProblem(f"{validate.INVESTIGATION_TEMPLATE}: status comment lists")

    def test_investigations_readme_lists_statuses(self):
        self.edit(validate.INVESTIGATIONS_README, "| `parked` |", "| `paused` |")
        self.assertProblem("'## Statuses' lists")


class TicketLifecycleTest(KitTestCase):
    def test_new_spec(self):
        self.make_ticket("XYZ-1-new", "draft", approved=False)
        self.assertValid()

    def test_spec_changed_after_approval_resets_the_plan(self):
        self.make_ticket("XYZ-1-changed", "draft", "approved", tasks="x ")
        self.assertProblem("the plan is approved but the spec is draft")

    def test_spec_and_plan_both_back_to_draft(self):
        self.make_ticket("XYZ-1-changed", "draft", "draft", tasks="x ")
        self.assertValid()

    def test_partial_implementation_keeps_the_plan_approved(self):
        self.make_ticket("XYZ-1-partial", "approved", "approved", tasks="x ", results=True)
        self.assertValid()

    def test_failed_final_verification_keeps_the_plan_approved(self):
        self.make_ticket("XYZ-1-failed", "approved", "approved", tasks="xx", results=True)
        self.assertValid()

    def test_implemented_plan_with_an_unticked_task(self):
        self.make_ticket("XYZ-1-failed", "approved", "implemented", tasks="x ", results=True)
        self.assertProblem("1 task(s) are unticked")

    def test_implemented_plan_without_results(self):
        self.make_ticket("XYZ-1-silent", "approved", "implemented", tasks="xx")
        self.assertProblem("'Results and deviations' is not filled")

    def test_implemented_plan(self):
        self.make_ticket("XYZ-1-implemented", "approved", "implemented", tasks="xx", results=True)
        self.assertValid()

    def test_unfinished_fix_after_review(self):
        self.make_ticket("XYZ-1-fix", "approved", "implemented", tasks="xx", results=True, checked="R. Reviewer, 2026-01-03")
        self.assertValid()
        path = "docs/specs/XYZ-1-fix/plan.md"
        self.edit(path, "- [x] T2", "- [ ] T2")
        self.edit(path, "status: implemented", "status: approved")
        self.assertProblem(f"{path}: S1 is checked but T2 is unticked")
        self.edit(path, "  - Checked: R. Reviewer, 2026-01-03\n", "  - Checked:\n")
        self.assertValid()

    def test_done_spec_with_an_unfinished_plan(self):
        self.make_ticket("XYZ-1-merged", "done", "approved", tasks="x ", results=True)
        self.assertProblem("the spec is done but the plan is approved")

    def test_done_spec_needs_a_plan(self):
        self.make_ticket("XYZ-1-merged", "done")
        self.assertProblem("the spec is done but there is no plan.md")

    def test_done_spec(self):
        self.make_ticket("XYZ-1-merged", "done", "implemented", tasks="xx", results=True)
        self.assertValid()

    def test_approved_spec_needs_an_approver(self):
        self.make_ticket("XYZ-1-unsigned", "approved", approved=False)
        self.assertProblem("an approved spec needs approved_by and date")

    def test_spec_has_no_implemented_status(self):
        self.make_ticket("XYZ-1-old", "implemented")
        self.assertProblem("status 'implemented' is not one of")


class TicketFolderTest(KitTestCase):
    def test_one_folder_per_ticket(self):
        self.make_ticket("XYZ-1-first_branch", "draft", approved=False)
        self.make_ticket("XYZ-1-renamed_branch", "draft", approved=False)
        self.assertProblem("ticket XYZ-1 has several folders")

    def test_folder_name_starts_with_the_ticket(self):
        self.make_ticket("XYZ-2-wrong", "draft", approved=False)
        self.assertProblem("docs/specs/XYZ-2-wrong: folder name must be 'XYZ-1-<slug>'")

    def test_plan_refers_to_the_spec_next_to_it(self):
        self.make_ticket("XYZ-1-plan", "approved", "draft")
        self.edit("docs/specs/XYZ-1-plan/plan.md", "spec: ./spec.md", "spec: ../XYZ-2-other/spec.md")
        self.assertProblem("docs/specs/XYZ-1-plan/plan.md: spec '../XYZ-2-other/spec.md', expected './spec.md'")

    def test_example_follows_the_templates(self):
        self.edit("docs/specs/_example/ABC-123-limit_login_attempts/spec.md", "## ADRs\n", "## Decisions\n")
        self.assertProblem("_example/ABC-123-limit_login_attempts/spec.md: sections")


class SessionTest(KitTestCase):
    PLAN = "docs/specs/XYZ-1-sessions/plan.md"

    def setUp(self):
        super().setUp()
        self.make_ticket("XYZ-1-sessions", "approved", "approved")

    def test_sessions_section_is_required(self):
        self.edit(self.PLAN, "## Sessions\n", "## Runs\n")
        self.assertProblem(f"{self.PLAN}: no section '## Sessions'")

    def test_every_task_is_in_a_session(self):
        self.edit(self.PLAN, "- S1 (T1–T2):", "- S1 (T1):")
        self.assertProblem(f"{self.PLAN}: T2 is in no session")

    def test_a_task_is_in_one_session_only(self):
        self.edit(self.PLAN, "  - Checked:\n", "  - Checked:\n- S2 (T2): the second slice.\n  - Check: it works.\n  - Checked:\n")
        self.assertProblem(f"{self.PLAN}: T2 is in more than one session")

    def test_a_session_lists_existing_tasks(self):
        self.edit(self.PLAN, "- S1 (T1–T2):", "- S1 (T1–T3):")
        self.assertProblem(f"{self.PLAN}: S1 lists T3, which is not in 'Tasks'")

    def test_a_session_lists_tasks_as_ranges_or_numbers(self):
        self.edit(self.PLAN, "- S1 (T1–T2):", "- S1 (T1, T2):")
        self.assertValid()
        self.edit(self.PLAN, "- S1 (T1, T2):", "- S1 (tasks 1 and 2):")
        self.assertProblem(f"{self.PLAN}: S1 lists 'tasks 1 and 2', expected T<n> or T<n>–T<m>")

    def test_sessions_take_the_tasks_in_order(self):
        self.edit(self.PLAN, "- S1 (T1–T2):", "- S1 (T2, T1):")
        self.assertProblem(f"{self.PLAN}: the sessions do not take the tasks in the order of 'Tasks'")

    def test_sessions_are_numbered_in_order(self):
        self.edit(self.PLAN, "- S1 (T1–T2):", "- S2 (T1–T2):")
        self.assertProblem(f"{self.PLAN}: the sessions must be S1, S2, … in order")

    def test_a_session_needs_a_checked_line(self):
        self.edit(self.PLAN, "  - Checked:\n", "")
        self.assertProblem(f"{self.PLAN}: S1 needs exactly one 'Checked' line, found 0")

    def test_a_session_has_one_checked_line(self):
        self.edit(self.PLAN, "  - Checked:\n", "  - Checked: R. Reviewer, 2026-01-03\n  - Checked:\n")
        self.assertProblem(f"{self.PLAN}: S1 needs exactly one 'Checked' line, found 2")

    def test_a_session_needs_a_check(self):
        self.edit(self.PLAN, "  - Check: <what the person verifies>.\n", "")
        self.assertProblem(f"{self.PLAN}: S1 needs exactly one 'Check' line, found 0")

    def test_a_session_has_one_check_line(self):
        self.edit(self.PLAN, "  - Check: <what the person verifies>.\n", "  - Check: the first thing.\n  - Check: the second thing.\n")
        self.assertProblem(f"{self.PLAN}: S1 needs exactly one 'Check' line, found 2")

    def test_check_has_text(self):
        self.edit(self.PLAN, "  - Check: <what the person verifies>.\n", "  - Check:\n")
        self.assertProblem(f"{self.PLAN}: 'Check' of S1 is empty")

    def test_checked_names_the_person_and_the_date(self):
        for task in ("T1", "T2"):
            self.edit(self.PLAN, f"- [ ] {task}", f"- [x] {task}")
        self.edit(self.PLAN, "  - Checked:\n", "  - Checked: yes\n")
        self.assertProblem(f"{self.PLAN}: 'Checked' of S1 must be '<name>, <YYYY-MM-DD>'")

    def test_a_range_goes_forward(self):
        self.edit(self.PLAN, "- S1 (T1–T2):", "- S1 (T2–T1):")
        self.assertProblem(f"{self.PLAN}: S1 lists 'T2–T1', a range that goes backwards")

    def test_tasks_are_numbered_in_order(self):
        self.edit(self.PLAN, "- [ ] T2 (R2, AC2):", "- [ ] T1 (R2, AC2):")
        self.assertProblem(f"{self.PLAN}: the tasks must be T1, T2, … in order")

    def test_a_plan_needs_tasks(self):
        self.edit(self.PLAN, "- [ ] T1 (R1, AC1):\n- [ ] T2 (R2, AC2):\n", "")
        self.assertProblem(f"{self.PLAN}: 'Tasks' has no entry like '- [ ] T1 (R1, AC1): <task>'")

    def test_checked_needs_every_task_ticked(self):
        self.edit(self.PLAN, "- [ ] T1", "- [x] T1")
        self.edit(self.PLAN, "  - Checked:\n", "  - Checked: R. Reviewer, 2026-01-03\n")
        self.assertProblem(f"{self.PLAN}: S1 is checked but T2 is unticked")

    def test_checked_session(self):
        self.make_ticket("XYZ-2-checked", "approved", "approved", tasks="xx", ticket="XYZ-2", checked="R. Reviewer, 2026-01-03")
        self.assertValid()

    def test_plan_in_two_sessions(self):
        path = self.PLAN
        self.edit(path, "- [ ] T2 (R2, AC2):\n", "- [ ] T2 (R2, AC2):\n- [ ] T3 (R3, AC3):\n- [ ] T4 (R4, AC4):\n")
        self.edit(path, "  - Checked:\n", "  - Checked:\n- S2 (T3–T4): the second slice.\n  - Check: the second slice works.\n  - Checked:\n")
        self.assertValid()
        for task in ("T1", "T2"):
            self.edit(path, f"- [ ] {task}", f"- [x] {task}")
        self.assertValid()
        self.edit(path, "  - Checked:\n", "  - Checked: R. Reviewer, 2026-01-03\n")
        self.assertValid()
        for task in ("T3", "T4"):
            self.edit(path, f"- [ ] {task}", f"- [x] {task}")
        self.edit(path, "status: approved", "status: implemented")
        self.assertProblem(f"{path}: the plan is implemented but 'Results and deviations' is not filled")
        file = self.root / path
        file.write_text(file.read_text() + "\nRun 1, S1: passed. Run 2, S2: passed.\n")
        self.assertValid()
        self.edit(path, "- [x] T2", "- [ ] T2")
        self.edit(path, "status: implemented", "status: approved")
        self.assertProblem(f"{path}: S1 is checked but T2 is unticked")
        self.edit(path, "  - Checked: R. Reviewer, 2026-01-03\n", "  - Checked:\n")
        self.assertValid()


class InvestigationTest(KitTestCase):
    def test_investigation_from_draft_to_ready(self):
        self.make_investigation("price_alerts", "draft")
        self.assertValid()
        path = "docs/investigations/price_alerts/investigation.md"
        self.edit(path, "status: draft", "status: ready")
        self.assertProblem(f"{path}: the investigation is ready but there is no roadmap.md")
        self.assertProblem(f"{path}: a ready investigation needs date")
        self.assertProblem(f"{path}: the investigation is ready but 11 area(s) are still open: Problem and users, ")
        self.assertProblem(f"{path}: the investigation is ready but 'Decisions' has no entry like '- D1 (<date>). <question>'")
        self.make_roadmap("price_alerts", "price_alerts")
        self.assertProblem("docs/investigations/price_alerts/roadmap.md: the investigation is ready but 'Phases' has no entry like '- S1. <step>'")
        self.assertProblem("docs/investigations/price_alerts/roadmap.md: the investigation is ready but 'Candidate tickets' has no entry like '- <title>: <goal>'")
        self.fill_investigation("price_alerts")
        self.fill_roadmap("price_alerts")
        self.assertValid()

    def test_ready_investigation(self):
        self.make_investigation("price_alerts", "ready", roadmap=True, filled=True)
        self.assertValid()

    def test_ready_with_an_area_that_does_not_apply(self):
        self.make_investigation("price_alerts", "ready", roadmap=True, filled=True)
        self.edit("docs/investigations/price_alerts/investigation.md", "| Operations | covered |", "| Operations | n/a |")
        self.assertValid()

    def test_ready_with_one_open_area(self):
        self.make_investigation("price_alerts", "ready", roadmap=True, filled=True)
        self.edit("docs/investigations/price_alerts/investigation.md", "| Operations | covered |", "| Operations | open |")
        self.assertProblem("investigation.md: the investigation is ready but 1 area(s) are still open: Operations")

    def test_ready_with_empty_documents(self):
        self.make_investigation("price_alerts", "ready", roadmap=True, filled=True)
        for name in ("investigation.md", "roadmap.md"):
            file = self.root / "docs/investigations/price_alerts" / name
            text = file.read_text()
            file.write_text(text[:text.index("---", 3) + 4])
        self.assertProblem("investigation.md: no section '## Coverage'")
        self.assertProblem("investigation.md: the investigation is ready but 'Decisions' has no entry like")
        self.assertProblem("roadmap.md: the investigation is ready but 'Phases' has no entry like")

    def test_ready_needs_entries_not_just_text(self):
        self.make_investigation("price_alerts", "ready", roadmap=True, filled=True)
        self.edit("docs/investigations/price_alerts/investigation.md", "- D0 (2026-01-02). First version?", "We decided on the web client.")
        self.edit("docs/investigations/price_alerts/roadmap.md", "- S0. Web client.", "Phase 1 builds the web client.")
        self.edit("docs/investigations/price_alerts/roadmap.md", "- Web client: the first version;", "None yet;")
        self.assertProblem("investigation.md: the investigation is ready but 'Decisions' has no entry like")
        self.assertProblem("roadmap.md: the investigation is ready but 'Phases' has no entry like")
        self.assertProblem("roadmap.md: the investigation is ready but 'Candidate tickets' has no entry like")

    def test_coverage_section_is_required_in_every_status(self):
        for status in ("draft", "parked", "rejected"):
            with self.subTest(status=status):
                self.make_investigation(f"idea_{status}", status)
                self.edit(f"docs/investigations/idea_{status}/investigation.md", "## Coverage\n", "## Areas\n")
                self.assertProblem(f"docs/investigations/idea_{status}/investigation.md: no section '## Coverage'")

    def test_coverage_lists_every_area_of_the_template(self):
        self.make_investigation("price_alerts", "draft")
        self.edit("docs/investigations/price_alerts/investigation.md", "| Operations | open | |\n", "")
        self.assertProblem("investigation.md: 'Coverage' lacks the area(s) of the template: Operations")

    def test_coverage_lists_an_area_once(self):
        self.make_investigation("price_alerts", "draft")
        self.edit("docs/investigations/price_alerts/investigation.md", "| Delivery | open | |\n", "| Delivery | open | |\n| Delivery | covered | D1 |\n")
        self.assertProblem("investigation.md: 'Coverage' lists Delivery more than once")

    def test_coverage_may_add_an_area(self):
        self.make_investigation("price_alerts", "draft")
        self.edit("docs/investigations/price_alerts/investigation.md", "| Delivery | open | |\n", "| Delivery | open | |\n| Localization | open | |\n")
        self.assertValid()

    def test_coverage_status_is_open_covered_or_n_a(self):
        self.make_investigation("price_alerts", "draft")
        self.edit("docs/investigations/price_alerts/investigation.md", "| Problem and users | open |", "| Problem and users | coverd |")
        self.assertProblem("investigation.md: coverage of 'Problem and users' is 'coverd', not one of open, covered, n/a")

    def test_draft_with_a_roadmap(self):
        self.make_investigation("price_alerts", "draft", roadmap=True)
        self.assertValid()

    def test_parked_investigation_needs_no_roadmap(self):
        self.make_investigation("price_alerts", "parked")
        self.assertValid()

    def test_investigation_has_no_approved_status(self):
        self.make_investigation("price_alerts", "approved")
        self.assertProblem("docs/investigations/price_alerts/investigation.md: status 'approved' is not one of")

    def test_slug_matches_the_folder(self):
        self.make_investigation("price_alerts", "draft", slug="alerts")
        self.assertProblem("docs/investigations/price_alerts/investigation.md: slug 'alerts' differs from the folder name 'price_alerts'")

    def test_roadmap_slug_matches_the_folder(self):
        self.make_investigation("price_alerts", "draft", roadmap=True)
        self.edit("docs/investigations/price_alerts/roadmap.md", "slug: price_alerts", "slug: alerts")
        self.assertProblem("docs/investigations/price_alerts/roadmap.md: slug 'alerts' differs from the folder name 'price_alerts'")

    def test_roadmap_refers_to_the_investigation_next_to_it(self):
        self.make_investigation("price_alerts", "draft", roadmap=True)
        self.edit("docs/investigations/price_alerts/roadmap.md", "investigation: ./investigation.md", "investigation: ../other/investigation.md")
        self.assertProblem("docs/investigations/price_alerts/roadmap.md: investigation '../other/investigation.md', expected './investigation.md'")

    def test_roadmap_has_no_status(self):
        self.make_investigation("price_alerts", "draft", roadmap=True)
        self.edit("docs/investigations/price_alerts/roadmap.md", "investigation: ./investigation.md\n", "investigation: ./investigation.md\nstatus: draft\n")
        self.assertProblem("docs/investigations/price_alerts/roadmap.md: front matter keys")

    def test_investigation_front_matter_keys(self):
        self.make_investigation("price_alerts", "draft")
        self.edit("docs/investigations/price_alerts/investigation.md", "author: <name>\n", "")
        self.assertProblem("docs/investigations/price_alerts/investigation.md: front matter keys")

class FrontMatterTest(KitTestCase):
    def test_quoted_value_is_reported_with_the_format(self):
        self.make_ticket("XYZ-1-quoted", "draft", approved=False)
        self.edit("docs/specs/XYZ-1-quoted/spec.md", "status: draft", 'status: "draft"')
        self.assertProblem("the value of status is quoted; write 'status: draft' (front matter format:")

    def test_value_with_a_colon_is_reported(self):
        self.make_ticket("XYZ-1-colon", "draft", approved=False)
        self.edit("docs/specs/XYZ-1-colon/spec.md", "title: <short title>", "title: Login: limit the attempts")
        self.assertProblem("docs/specs/XYZ-1-colon/spec.md: the value of title contains ': ' or ends with ':', which a YAML parser rejects")

    def test_indented_line_is_reported_with_the_format(self):
        self.make_ticket("XYZ-1-nested", "draft", approved=False)
        self.edit("docs/specs/XYZ-1-nested/spec.md", "approved_by:\n", "approved_by:\n  - R. Reviewer\n")
        self.assertProblem("line 7 '  - R. Reviewer' is not 'key: value' (front matter format:")


class AdrTest(KitTestCase):
    def test_adr(self):
        self.make_adr("0001-redis_for_shared_state.md", "0001", "accepted")
        self.assertValid()

    def test_adr_file_name(self):
        self.make_adr("redis.md", "0001", "accepted")
        self.assertProblem("docs/adr/redis.md: the name must be '0001-<slug>.md'")

    def test_adr_id_matches_the_file_name(self):
        self.make_adr("0001-redis.md", "0002", "accepted")
        self.assertProblem("id '0002' differs from the number in the file name")

    def test_superseded_adr(self):
        self.make_adr("0001-redis.md", "0001", "accepted")
        self.make_adr("0002-valkey.md", "0002", "accepted", supersedes="0001")
        self.assertProblem("docs/adr/0001-redis.md: superseded by docs/adr/0002-valkey.md")
        self.make_adr("0001-redis.md", "0001", "superseded")
        self.assertValid()


if __name__ == "__main__":
    unittest.main()

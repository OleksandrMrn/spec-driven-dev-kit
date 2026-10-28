---
ticket: <TICKET>
title: <short title>
status: draft            # draft | approved | done | rejected
author: <name>
approved_by:
date:
---

# <TICKET>: <short title>

## Context

Why this ticket exists: the problem, who reported it, links (tracker, designs, dashboards). Facts, not solutions.

## Goal

One or two sentences: what is true after the change that is not true now.

## Scope

- In scope: modules, features, configs, environments.
- Out of scope: what is explicitly not touched, even if related.

## Requirements

Numbered, testable statements. Each one can be checked on its own.

- R1.
- R2.

## Acceptance criteria

Observable outcomes a reviewer or QA can verify, each mapped to requirements.

- AC1 (R1):
- AC2 (R2):

## Contracts touched

Write "none" where nothing changes.

- Configs and file formats: files and keys, per environment.
- API and protocols: endpoints, messages, payloads.
- Data schema: tables, models, stored data; migrations.
- Public interfaces: module signatures used by others, CLI, routes.
- Events, analytics, feature flags: names, keys, parameters.

## ADRs

Accepted ADRs in `docs/adr/` that apply to this change, each with the constraint it sets. An ADR the change would contradict is named here and in "Open questions" (`docs/specs/README.md`, "ADRs"). Write "none" if none apply.

## Modules and environments affected

Which modules or features (and which copies, if the code is duplicated) and which environments.

## Preservation

What existing data and behavior must stay as is: stored data and user state, running experiments, analytics parity, other callers of the changed code.

## Risks

Production impact, rollback, dependencies on other teams or services.

## Open questions

Questions only the reviewer or stakeholders can answer. Empty before approval.

---
slug: <slug>
title: <short title>
status: draft            # draft | ready | parked | rejected
author: <name>
date:
---

# Investigation: <short title>

## Idea

The idea in the user's own words at the start. It stays as written; what changed since is in "Decisions".

## Coverage

Every area ends `covered` (decisions and findings exist for it) or `n/a` with the reason (`docs/investigations/README.md`, "Areas"). "Where" lists the `D<n>`, `F<n>` and `A<n>` entries that cover it.

| Area | Status | Where |
|---|---|---|
| Problem and users | open | |
| Value and success | open | |
| Non-goals | open | |
| First version | open | |
| Constraints | open | |
| Domain and data | open | |
| External dependencies | open | |
| Architecture and stack | open | |
| Risks and spikes | open | |
| Operations | open | |
| Delivery | open | |

## Decisions

Only the user decides; each entry keeps the question, the options and the reason. A decision that replaces an earlier one is added as a new entry, and the old one gets "superseded by D<n>".

- D1 (<date>). <the question in one line>
  - Options: a) …; b) …
  - Choice: …
  - Why: …

## Findings

Facts found by research, each with its source and date. `verified`: read from the source. `unverified`: from memory or inference, to be checked before the roadmap relies on it.

- F1 (<date>, verified). <fact>. Source: <url or path>.

## External dependencies

One entry per API, service, exchange or payment provider the idea relies on, filled before the roadmap builds on it. The first roadmap step that touches a dependency is one real operation end to end with real credentials.

- <name>
  - Needed: <endpoints or features>; status and changelog: …
  - Access: <keys, whitelist, KYC, contract>
  - Limits and fees: …
  - Unknown: …
  - Access check: <roadmap step>

## Assumptions

What is taken as true without a decision or a verified finding, each with the roadmap step that verifies it.

- A1. <assumption>. Verified by: <S<n>, or "open">.

## Risks

What can kill or reshape the idea, with the cheapest check for each and where it sits in the roadmap.

- <risk>. Check: …. Step: ….

## Open questions

Questions waiting for an answer. The user answers in chat by number or under "Answer" here; an answered question moves to "Decisions", "Findings" or "Assumptions".

- Q1 (round 1, <area>). <question>
  - Why it matters: <what in the roadmap depends on it>
  - Options: a) … (recommended); b) …; default: a
  - Who answers: <the user, or a named person>
  - Answer:

## Log

One line per round: date, questions asked, what was recorded, what stayed open.

- Round 1, <date>: Q1–Q10 asked; D1–D6, A1 recorded; Q4, Q9 open.

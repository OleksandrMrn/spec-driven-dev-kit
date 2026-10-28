---
ticket: ABC-123
title: Limit failed login attempts
status: done             # draft | approved | done | rejected
author: A. Developer
approved_by: R. Reviewer
date: 2026-10-05
---

# ABC-123: Limit failed login attempts

> Example only: the project, its files, ADRs, tickets and people are fictional. It shows a finished ticket: an approved spec, a plan implemented in two sessions and one fix after review.

## Context

Security review SEC-17 found that `POST /api/login` accepts any number of password attempts per account. The auth logs show bursts of more than 2,000 failed attempts per hour against single accounts (dashboard "Auth / failed logins", 2026-09).

## Goal

After too many failed logins for an account within a time window, further attempts are rejected until the window passes, and the client is told when to retry.

## Scope

- In scope: the login endpoint, its config, its error responses, staging and production.
- Out of scope: password reset, two-factor login, limits per IP address (ticket ABC-130).

## Requirements

- R1. Failed login attempts are counted per account in a sliding window.
- R2. Once an account has `maxAttempts` failed attempts in the window, every further attempt is rejected with HTTP 429 before the password is checked.
- R3. The 429 response has a `Retry-After` header: the whole seconds, rounded up, until the oldest counted attempt leaves the window.
- R4. A successful login clears the account's counter.
- R5. `maxAttempts` and the window are read from the config key `auth.loginLimit` (`maxAttempts`, `windowSeconds`) per environment; the defaults are 10 and 900.
- R6. If the counter store is unavailable, the login proceeds without the limit and the event `auth.limit_unavailable` is logged.

## Acceptance criteria

- AC1 (R1, R2): with the defaults, ten wrong passwords in a row return 401; the eleventh attempt returns 429, also with the right password.
- AC2 (R3): every 429 response has `Retry-After` between 1 and 900.
- AC3 (R4): after a successful login, ten more wrong passwords return 401 again.
- AC4 (R5): with `maxAttempts: 3` in staging, the fourth wrong password returns 429.
- AC5 (R6): with the counter store stopped, a right password logs in and `auth.limit_unavailable` is logged.

## Contracts touched

- Configs and file formats: new key `auth.loginLimit` in `config/staging.yaml` and `config/production.yaml` (`maxAttempts: 10`, `windowSeconds: 900`).
- API and protocols: `POST /api/login` gains the response 429 with the header `Retry-After` and the body `{"error": "too_many_attempts"}`.
- Data schema: none; the counters are short-lived Redis keys `login_attempts:<accountId>`.
- Public interfaces: none.
- Events, analytics, feature flags: new events `auth.login_blocked` (`accountId`, `attempts`) and `auth.limit_unavailable` (`accountId`).

## ADRs

- ADR-0004 "Redis holds all short-lived shared state": the counters live in Redis, not in the database.

## Modules and environments affected

`src/auth/` (login handler, new attempt counter), `src/config/`, `src/analytics/`; staging and production.

## Preservation

Existing sessions stay valid. Below the limit the 401 response for a wrong password is unchanged, and the event `auth.login_failed` keeps its parameters.

## Risks

An outage of the counter store must neither lock everyone out nor fail logins: R6 decides it. Rollback: redeploy the previous release, which has no limit; raising `maxAttempts` in the config is only a stopgap while that deploy runs. There is no data to migrate.

## Open questions

None. Resolved before approval: on an outage of the counter store logins go on without the limit (R6; R. Reviewer, 2026-10-04).

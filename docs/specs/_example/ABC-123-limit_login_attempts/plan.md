---
ticket: ABC-123
status: implemented      # draft | approved | implemented
spec: ./spec.md
---

# Plan: ABC-123 Limit failed login attempts

> Example only: the project, its files, commands and results are fictional.

## Facts

- `src/auth/loginHandler.ts:41-78` checks the password and returns 401 on failure; nothing counts attempts.
- `src/auth/index.ts:3` exports `loginHandler`; `src/server/routes.ts:22` is its only caller.
- `src/cache/redisClient.ts:12` is the shared Redis client (ADR-0004); `src/sessions/store.ts:30-44` keeps short-lived keys with a TTL the same way.
- Config is read through `src/config/schema.ts`, which rejects unknown keys (`schema.ts:55`), so the new key needs a schema entry.
- No compatibility layers in scope.

## Proposal

A new module `src/auth/attemptCounter.ts` keeps a Redis sorted set of failed-attempt timestamps per account, drops the entries older than the window, and returns the count and the seconds until the oldest one expires. `loginHandler` asks the counter before checking the password, records a failure after a 401 and clears the counter after a success.

Alternative considered: a fixed-window counter with `INCR` and `EXPIRE`. It is simpler, but it lets up to twice the limit through around a window boundary and cannot give an exact `Retry-After`, so R2 and R3 would not hold.

Compatibility layers: one, required by R6. When Redis does not answer, `attemptCounter` returns `unavailable`, and `loginHandler` skips the limit and logs `auth.limit_unavailable`. The fallback lives only in `attemptCounter.ts` and has its own test.

## Files to change

| File | Change |
|---|---|
| `src/auth/attemptCounter.ts` | new: sliding-window counter on Redis, `unavailable` result |
| `src/auth/loginHandler.ts` | check the counter before the password, record and clear attempts, 429 response |
| `src/config/schema.ts` | entry for `auth.loginLimit` |
| `config/staging.yaml`, `config/production.yaml` | `auth.loginLimit` |
| `src/analytics/events.ts` | events `auth.login_blocked`, `auth.limit_unavailable` |
| `src/auth/__tests__/attemptCounter.test.ts`, `src/auth/__tests__/loginHandler.test.ts` | tests for R1–R6 |

## Preservation of existing data and behavior

No stored data changes. Below the limit the handler's responses and the event `auth.login_failed` stay as they are; the existing tests of `loginHandler` are not changed and must pass.

Recovery (AGENTS.md section 8): for an hour after the deploy watch the dashboard "Auth / failed logins" and the rate of 429 responses; stop and restore if an account below the limit gets 429 or the login error rate rises. Restore by redeploying the previous release, 4.12.0, which has no limit; while that deploy runs, `maxAttempts: 100000` in `config/production.yaml` is a stopgap that only raises the threshold, the counting and the 429 after it stay. Confirm the restored state in two steps: `GET /api/version` on production answers `4.12.0`, which the stopgap alone would not change, and then on a test account eleven wrong passwords in a row are all answered 401.

## Verification

Commands (AGENTS.md section 9) and expected results, scoped to the change:

- Type check: `npm run typecheck`, no errors.
- Lint: `npm run lint -- src/auth src/config src/analytics`, no errors.
- Tests (scoped): `npm test -- src/auth`, all pass.
- Manual check: AC4 on staging with a test account and `maxAttempts: 3`; AC1, AC3 and AC5 locally with the defaults.

## Tasks

- [x] T1 (R5, AC4): `auth.loginLimit` in the schema and in both environments.
- [x] T2 (R1, R3, R6, AC2, AC5): `attemptCounter` with tests, including Redis not answering.
- [x] T3 (R2, R4, AC1, AC3): the counter in `loginHandler`, the 429 response, tests.
- [x] T4 (R2, R6): events `auth.login_blocked` and `auth.limit_unavailable`.

## Sessions

- S1 (T1–T2): the config key is read in both environments and the counter works on its own, with tests; the login endpoint is unchanged.
  - Check: `npm test -- src/auth` passes; `auth.loginLimit` is in both config files; the test with a failing Redis client covers R6.
  - Checked: R. Reviewer, 2026-10-08
- S2 (T3–T4): the login endpoint applies the limit and sends the events.
  - Check: AC1, AC3 and AC5 locally with the defaults; AC4 on staging with `maxAttempts: 3`.
  - Checked: R. Reviewer, 2026-10-07

## Results and deviations

Run 1, 2026-10-06, S1 (T1–T2):

- `npm run typecheck`: passed. `npm run lint -- src/auth src/config`: passed. `npm test -- src/auth`: 14 tests passed.
- Not verified: a real Redis failover; only the test with a failing client covers R6.
- Deviations: none.

Run 2, 2026-10-07, S2 (T3–T4):

- `npm run typecheck`: passed. `npm run lint -- src/auth src/config src/analytics`: passed. `npm test -- src/auth`: 24 tests passed.
- AC4 on staging: the fourth wrong password returned 429 with `Retry-After: 897`. AC1, AC3 and AC5 locally: as expected.
- Deviations: none.
- Out of scope: `src/auth/loginHandler.ts:90` logs the submitted e-mail address on 401; reported as ABC-131.

Run 3, 2026-10-08, fix after review (S1, T2):

- Review finding 1: `Retry-After` was rounded down and could be 0, against R3 and AC2. `attemptCounter.ts` now rounds up; a test for the last second of the window was added.
- `npm run typecheck`: passed. `npm run lint -- src/auth src/config src/analytics`: passed. `npm test -- src/auth`: 25 tests passed.
- S1 checked again by R. Reviewer on 2026-10-08.

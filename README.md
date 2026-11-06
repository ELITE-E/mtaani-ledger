# Mtaani Express Ledger

A wallet and double-entry ledger service for a hypothetical Eldoret delivery business (Mtaani Express), connected to the Safaricom M-Pesa Daraja sandbox. It is an engineering exercise in how money systems behave: balanced journals, transfers that cannot be applied twice, a daily reconciliation that flags mismatches, and real callbacks, delays and failures.

> **Status: design complete, implementation in progress.** The commands under "Run it" have **not** yet been verified from a clean checkout. This banner and the status table are updated as the build lands. If a statement here disagrees with the code, the code and tests win.

## What it demonstrates

| Skill | Design | Proof (planned) |
|---|---|---|
| Accounts and double-entry records | [Chart of accounts](docs/spec/02-chart-of-accounts.md), [posting rules](docs/spec/03-events-and-posting.md) | Golden scenario test with exact journal lines |
| A transfer that cannot be applied twice | [Idempotency and concurrency](docs/spec/06-concurrency-idempotency.md) | Duplicate, conflicting and concurrent request tests |
| Daily reconciliation that flags mismatches | [Reconciliation](docs/spec/07-reconciliation.md) | Statement fixture builder with injected faults |
| Real Daraja callbacks, delays and failures | `docs/engineering/daraja-notes.md` (written during the build) | Sandbox callbacks plus a fault-injection harness |

## The scenario

Mtaani Express takes orders for about 15 partner shops. Customers hold a wallet topped up through an M-Pesa Paybill and pay for orders from it. The business earns 12% commission on item value and keeps KES 50 of each KES 150 delivery fee (KES 100 goes to the rider). Shops are paid every Monday and riders every Friday, by M-Pesa. Details: [`docs/discovery/`](docs/discovery/).

The business and its stakeholders are **simulated**. See the [write-up](WRITEUP.md).

## Architecture

```
Daraja (C2B, B2C callbacks)      Order-event simulator       Finance users (API keys)
            \                            |                          /
             +------------------  FastAPI API  -------------------+
                                        |
                                  PostgreSQL  <---- worker (outbox, timeouts, scheduled jobs)
```

- One deployable API, one worker, one PostgreSQL database. No UI.
- Every posting goes through a single posting service. Nothing writes ledger tables directly.
- Money is whole-shilling integers (KES). Timestamps are UTC; business dates are derived in EAT.

## Run it (not yet verified)

Prerequisites: Docker, Git, a Daraja sandbox app, a tunnel (ngrok or cloudflared) for callbacks.

```bash
git clone <repository-url> && cd <repository-directory>
cp .env.example .env          # fill in database and Daraja sandbox settings
docker compose up --build -d
docker compose exec api alembic upgrade head
docker compose exec api pytest
```

Daraja callback URLs must be HTTPS, must be publicly reachable (so localhost needs a tunnel), and must not contain "mpesa", "m-pesa" or "safaricom". Never commit `.env`.

## Repository map

| Path | Contents |
|---|---|
| [`WRITEUP.md`](WRITEUP.md) | Design, decisions, limitations |
| [`docs/spec/`](docs/spec/) | Conventions, chart of accounts, events and posting rules, state machines, invariants, concurrency, reconciliation |
| `docs/engineering/` | Coding rules, test plan, Daraja notes (written during the build) |
| `docs/discovery/` | Fact sheet, decisions log, stakeholder interview summaries |

## Status

| Area | Status |
|---|---|
| Design (spec files) | Drafted |
| Ledger core and golden test | Not started |
| Orders, holds, settlement | Not started |
| C2B against the sandbox | Not started |
| B2C and UNKNOWN handling | Not started |
| Reconciliation and fixture builder | Not started |

## Known limitations

Summarised in the [write-up](WRITEUP.md). In short: the sandbox gives no real statement, the order system is simulated, and nothing here is a legal or regulatory compliance claim.

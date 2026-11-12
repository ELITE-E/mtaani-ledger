# Mtaani Express Ledger

A wallet and double-entry ledger service for a hypothetical Eldoret delivery business (Mtaani Express), connected to the Safaricom M-Pesa Daraja sandbox. It is an engineering exercise in how money systems behave: balanced journals, transfers that cannot be applied twice, a daily reconciliation that flags mismatches, and real callbacks, delays and failures.

> **Status: design complete; project foundation built and running. No ledger code yet.** The service starts (API, worker, PostgreSQL), health checks and migrations work, and lint and tests pass on the development machine. Nothing financial is implemented yet. This banner and the status table are updated as the build lands. If a statement here disagrees with the code, the code and tests win.

## What it demonstrates

| Skill | Design | Proof (planned) |
|---|---|---|
| Accounts and double-entry records | [Chart of accounts](docs/spec/02-chart-of-accounts.md), [posting rules](docs/spec/03-events-and-posting.md) | Golden scenario test with exact journal lines |
| A transfer that cannot be applied twice | [Idempotency and concurrency](docs/spec/06-concurrency-idempotency.md) | Duplicate, conflicting and concurrent request tests |
| Daily reconciliation that flags mismatches | [Reconciliation](docs/spec/07-reconciliation.md) | Statement fixture builder with injected faults |
| Real Daraja callbacks, delays and failures | `docs/engineering/daraja-notes.md` (written during the build) | Sandbox callbacks plus a fault-injection harness |

## The scenario

Mtaani Express takes orders for about 15 partner shops. Customers hold a wallet topped up through an M-Pesa Paybill and pay for orders from it. The business earns 12% commission on item value and keeps KES 50 of each KES 150 delivery fee (KES 100 goes to the rider). Shops are paid every Monday and riders every Friday, by M-Pesa. Details: `docs/discovery/` (not yet committed).

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

## Run it

Prerequisites: Docker (with Compose), Git, [`uv`](https://docs.astral.sh/uv/) and [`just`](https://just.systems/). A Daraja sandbox app and a tunnel (ngrok or cloudflared) will be needed once the M-Pesa work starts; they are not needed yet.

```bash
git clone <repository-url> && cd <repository-directory>
cp .env.example .env          # defaults work as-is for local development
uv sync                       # host tooling for tests and lint
just up                       # build and start db, api, worker (in the background)
just migrate                  # alembic upgrade head
just health                   # /health and /health/db
just check                    # ruff + pytest
just verify                   # full end-to-end check from a fresh build
```

Run `just` to list every recipe (`just api`, `just logs worker`, `just rollback`, `just psql`, ...). Without `just`, the same commands are plain `docker compose`, `uv run pytest` and `uv run ruff`.

Verified so far, on the development machine: the stack starts, both health endpoints answer, `just lint` is clean and all 9 tests pass, including the migration upgrade/downgrade round trip against the compose database. Not yet verified: a run from a clean clone.

**Linux:** if Docker reports `permission denied ... /var/run/docker.sock`, add yourself to the `docker` group (`sudo usermod -aG docker $USER`, then log out and back in) or prefix the recipes with `sudo`.

### Where things are

Everything is published on localhost only.

| Service | Address |
|---|---|
| API | http://localhost:8000 |
| Interactive API docs (Swagger) | http://localhost:8000/docs |
| Liveness check (no database) | http://localhost:8000/health |
| Readiness check (database) | http://localhost:8000/health/db (returns 503 when the database is down) |
| PostgreSQL | `localhost:5433` (user, password and database `ledger`; port set by `DB_HOST_PORT`) |

`just up` runs detached, so it prints no server output. Use `just ps` for status and ports, and `just logs api` or `just logs worker` to follow logs. `just dev` runs the API on the host with auto-reload instead (start the database first with `just db`).

### Tests

Tests run on the host (`just test`) against the compose database at `localhost:5433`; set `TEST_DATABASE_URL` to point elsewhere. Tests that need the database are skipped, not failed, when it is unreachable, so check the summary line for skips. The migration test downgrades to base and back, so it rewrites whatever schema the target database holds.

### Configuration

Settings come from environment variables or `.env` (see [`.env.example`](.env.example)). Used today: `DATABASE_URL` (set by Compose for the containers), `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `DB_HOST_PORT` and `WORKER_HEARTBEAT_SECONDS`. The `DARAJA_*` variables are placeholders and are not read yet.

Daraja callback URLs must be HTTPS, must be publicly reachable (so localhost needs a tunnel), and must not contain "mpesa", "m-pesa" or "safaricom". Never commit `.env`.

## What exists today

| Part | What it does now |
|---|---|
| API ([`app/main.py`](app/main.py)) | FastAPI app with `/health` and `/health/db` only |
| Worker ([`app/worker.py`](app/worker.py)) | Logs a heartbeat every `WORKER_HEARTBEAT_SECONDS`; shuts down cleanly on SIGTERM/SIGINT. The outbox, timeouts and scheduled jobs will run from this loop |
| Database | PostgreSQL 16 in Compose, data kept in the `pgdata` volume (`just down` keeps it, `just nuke` deletes it) |
| Migrations ([`migrations/`](migrations/)) | Alembic chain with an empty baseline revision `0001`; ledger tables arrive in later revisions |
| Logging ([`app/log_config.py`](app/log_config.py)) | UTC ISO-8601 timestamps, per the conventions spec |
| Tests ([`tests/`](tests/)) | Health endpoints (including the 503 path), single migration head and up/down round trip, worker loop and clean shutdown |
| Tooling | `uv` lockfile, `ruff` lint and format, `just` recipes, Python 3.12 in the container image |

## Repository map

| Path | Contents |
|---|---|
| [`WRITEUP.md`](WRITEUP.md) | Design, decisions, limitations |
| [`docs/spec/`](docs/spec/) | Conventions, chart of accounts, events and posting rules, state machines, invariants, concurrency, reconciliation |
| [`docs/diagrams/`](docs/diagrams/) | Rendered diagrams for the spec (accounts, posting, state machines, sequences); sources in `src/`, rebuilt by `render.sh` |
| [`app/`](app/), [`tests/`](tests/), [`migrations/`](migrations/) | Service code, tests, Alembic revisions |
| `docs/engineering/` | Coding rules, test plan, Daraja notes (**not yet written**) |
| `docs/discovery/` | Fact sheet, decisions log, stakeholder interview summaries (**not yet committed**) |

## Status

| Area | Status |
|---|---|
| Design (spec files) | Drafted |
| Project foundation (Compose stack, health checks, migrations, worker loop, lint, tests) | Done, verified on the development machine |
| Ledger core and golden test | Not started |
| Orders, holds, settlement | Not started |
| C2B against the sandbox | Not started |
| B2C and UNKNOWN handling | Not started |
| Reconciliation and fixture builder | Not started |

## Known limitations

Summarised in the [write-up](WRITEUP.md). In short: the sandbox gives no real statement, the order system is simulated, and nothing here is a legal or regulatory compliance claim.

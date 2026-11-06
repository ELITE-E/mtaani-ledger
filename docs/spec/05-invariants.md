# 05. Invariants

*Draft 0.1. An invariant is a statement that must be true at every commit. Each one names how it is enforced and which test proves it. Test names are planned, not yet written.*

Database constraints protect individual rows and uniqueness. They do not replace transactional posting logic or periodic recomputation of aggregates, so the strongest invariants use both.

## Enforced at write time

| ID | Invariant | Enforcement | Planned test | Priority |
|---|---|---|---|---|
| I1 | Every posted journal balances (debits = credits) | Deferred constraint trigger at commit on journal lines, plus validation in the posting service | Attempt an unbalanced journal: commit fails, no lines persist | Must |
| I2 | No negative customer available or held balance | Row lock on the wallet, availability check after the lock, CHECK constraints on the balance projection | Two concurrent holds of 700 against 1,000 available: exactly one succeeds | Must |
| I3 | No negative merchant or rider payable | Lock the payable before reserving a payout; CHECK on the projection | Two concurrent reservations exceeding one payable: only the affordable one succeeds | Must |
| I4 | Journals and lines are append-only | Triggers reject UPDATE and DELETE on posted rows | Attempt to edit and delete: both fail; a correction leaves the original intact | Must |
| I5 | An order settles at most once | Unique constraint on the order's settlement; state transition under row lock | Deliver the same order twice concurrently: one settlement journal | Must |
| I6 | A receipt credits at most once | Unique constraint on the M-Pesa receipt number; receipt record and journal in one transaction | Submit one receipt twice concurrently: one credit | Must |
| I7 | A payout item is never initiated twice while PENDING or UNKNOWN | State check under lock; unique initiation record | Concurrent initiation of one item: one external attempt | Must |
| I8 | A payout result is applied at most once | Terminal-state guard on the payout (primary); unique evidence record | Replay a result callback: no second posting | Must |
| I9 | The journal, idempotency record and balance projection change together or not at all | One database transaction | Force a failure between steps: nothing commits | Must |
| I10 | Every journal line references a valid account and the right subledger entity | Foreign keys | Insert a line with a missing party: rejected | Must |
| I11 | At most one full refund per order | Unique constraint on the refund's order reference | Two concurrent refunds: one journal | Should |

## Verified by recomputation (integrity check and reconciliation)

| ID | Invariant | How it is checked | Planned test |
|---|---|---|---|
| R1 | Cached account balance = sum of posted journal lines for that account | Recompute from lines and compare; mismatch raises an integrity exception and never rewrites the journal | Corrupt a test projection: the check detects it |
| R2 | Control account balance = sum of its subledger balances | Recompute per control account | Post multi-party movements, then compare |
| R3 | A customer's total = available (2000) + held (2001); held = sum of active order holds | Recompute from the journal | Place, cancel and settle holds, then compare |
| R4 | Ledger cash = statement balance + payout debits in transit + unsettled fees | Daily reconciliation ([07](07-reconciliation.md)) | Fixture with a missing line: exception raised |
| R5 | Protected cash ≥ protected obligations | Daily coverage check: COVERED / SHORTFALL / NOT VERIFIED | Underfunded fixture reports SHORTFALL; a stale statement reports NOT VERIFIED |

## Monitored conditions (alerts, not constraints)

- Operating cash minus unsettled fee payable at or above the KES 13,000 floor (blocks drawings and discretionary outflows; refunds are never blocked but alert).
- UNKNOWN payouts and unreturned principals, with their age.
- Missing or stale statement.
- Unmatched receipts older than 48 hours.

An unexplained difference is an exception to be investigated. It is never closed with a balancing entry.

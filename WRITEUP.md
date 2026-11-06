# Write-up: Mtaani Express Ledger

*Draft 0.1, 5 November 2026. Sections marked **[FILL AFTER BUILD]** are deliberately empty until the code and tests exist.*

## 1. The brief and my approach

The brief: build a small wallet or ledger service with accounts, double-entry records, a transfer that cannot be applied twice, and a daily reconciliation that flags mismatches, then connect it to the M-Pesa Daraja sandbox to deal with real callbacks, delays and failures.

I did not want to start from a blank table. A ledger encodes a business's rules, so I first defined a business, then worked from its requirements to the design: requirements, boundary, flow of funds, accounts, events, posting rules, integrity, then code. Each stage produced decisions that are recorded in `docs/`.

## 2. Where the requirements came from (simulated)

Mtaani Express is hypothetical, and so are its finance manager, accountant and operations lead. I elicited requirements by interviewing three separately prompted AI personas, then resolved the conflicts between them into numbered decisions (D1 to D16). **Every business rule is therefore an assumption, not a fact.** The interview summaries and the decisions log are in `docs/discovery/` so the reasoning can be challenged.

## 3. The design in brief

- **Double-entry, append-only.** Every business event posts balanced journal lines to a small chart of accounts. Corrections are a reversal plus a replacement, never an edit.
- **Control accounts with subledgers.** One general-ledger account per kind (customer wallets, merchant payables, rider payables); per-party balances live in subledgers that must always sum to the control account.
- **Orders are upstream.** The ledger consumes order events and keeps a minimal financial record. The order total (item value plus delivery fee) is held at placement, settled at delivery (commission, merchant and rider payables, income), or released on cancellation. Holds are journalled, so available and held balances can be rebuilt from the journal.
- **Payouts in transit.** A payout moves the payable into an in-transit liability and leaves ledger cash unchanged until M-Pesa confirms success. A timeout is **UNKNOWN**, never "failed", and an UNKNOWN payout is never blindly retried.
- **Logical segregation of funds.** One M-Pesa shortcode, two ledger cash pools: a protected pool backing customer and payee obligations, and an operating pool for fees and earned income. This is an accounting control, not a legal separation.
- **Idempotency in the database.** An M-Pesa receipt, an order lifecycle event and a payout result can each take effect once, enforced by unique constraints inside the posting transaction.
- **Outbox for Daraja calls.** The payout intent and its outbox row commit together; a separate worker calls Daraja outside any database transaction.

## 4. Key decisions and trade-offs

| Decision | Alternative | Why |
|---|---|---|
| Journal order holds via a holds liability | Track holds only in a subledger table | Every balance movement is then a balanced, idempotent journal entry that can be audited and replayed |
| Payout-in-transit liability; ledger cash leaves on confirmed success | Remove the payable at initiation | Initiation is not payment; a stuck or failed payout must not make an obligation disappear |
| Match wallets on `BillRefNumber` only, never fuzzy | Guess from the payer's phone | Daraja confirmation callbacks carry a masked or hashed payer number (UNVERIFIED), and a near match could credit the wrong person |
| Expected fees posted from a tariff table, trued up from the statement | Post fees only when the statement arrives | Callbacks carry no fee field, and waiting for the statement leaves cash overstated |
| PostgreSQL outbox plus a separate worker | In-process background tasks, or Redis/Celery | Durable and recoverable with no extra infrastructure at this volume |
| Single tenant, API keys per role | Multi-tenancy, full user management | Neither helps prove the four skills |

## 5. What Daraja taught me  **[FILL AFTER BUILD]**

Real payloads captured, how correlation identifiers behaved, what a timeout looked like, and every item on the UNVERIFIED list that the spike settled or left open.

## 6. Verification  **[FILL AFTER BUILD]**

Golden scenario results, idempotency and concurrency results, fault-injection results, reconciliation results, and the clean-checkout run.

## 7. Limitations

- **Simulated business, simulated stakeholders, simulated order system.**
- **No real M-Pesa statement.** The sandbox does not provide one, so reconciliation runs against a fixture I generate in an assumed portal format. The fixture proves the reconciliation engine works. It does not prove a real cash balance.
- **Logical segregation only.** Production would need a trust account or a licensed partner. Nothing here is a claim of regulatory compliance (Kenya's payment-service rules and unclaimed-funds law were noted but not verified).
- **Provider behaviour I could not confirm** is listed as UNVERIFIED in `docs/engineering/daraja-notes.md`, including callback authenticity.
- **Deliberately not built:** STK Push, cash-out workflow, owner-drawing workflow, dormancy automation, month-close, partial refunds, dual cash/accrual reporting views, UI.
- Human authentication is a static API key per role, enough to demonstrate maker-checker but not production access control.

## 8. If I had more time

Real statement ingestion, STK Push, an automated weekly sweep, month-end close, merchant recovery on post-delivery refunds, and a proper identity layer.

## 9. How this was built

AI assistants played the simulated stakeholders, acted as a design-review engineer, and helped write code and tests. Design decisions were mine to accept or reject, and each is recorded. **[Confirm and edit this paragraph so it states exactly what you did and can explain.]**

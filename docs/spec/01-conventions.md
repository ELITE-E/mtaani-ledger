# 01. Conventions

*Draft 0.1. These conventions are fixed before any table or API is designed. If one changes, every other spec file is affected.*

## Terminology

| Term | Meaning in this project |
|---|---|
| **Event** | A business occurrence (a top-up, an order delivered). Catalogue in [03](03-events-and-posting.md). |
| **Journal** | A set of balanced debit and credit lines posted for an event. |
| **Posting** | The act of writing a journal. Only the posting service does it. |
| **Database transaction** | The atomic unit in PostgreSQL. Never used to mean a business event. |
| **Subledger** | Per-party balances (customer, shop, rider, receipt, payout) under a control account. |
| **Timing item** | A named, evidenced reason cash differs between ledger and statement. See [07](07-reconciliation.md). |

## Money

- All amounts are **whole Kenyan shillings stored as integers**. No floats, no decimals, no cents.
- One currency (KES) in v1. A currency column may exist but only `KES` is accepted.
- A journal line holds a **positive** amount and an explicit side (debit or credit). Negative amounts are never used to mean the other side.
- Every journal satisfies: sum of debits = sum of credits.

## Commission rounding

Commission is 12% of the item value, rounded half up to a whole shilling, computed per order. Store the rate as **basis points** (12% = 1200) and use integer arithmetic:

```
commission = (item_value * rate_bps + 5000) // 10000
merchant_payable = item_value - commission
```

Examples: 1,800 gives 216; 1,801 gives 216; 1,805 gives 217. At 12% on whole shillings an exact half never occurs, so half-up and half-even agree today; the rule matters if the rate changes. The rate and a policy version are frozen in the order snapshot at placement.

## Time

| Timestamp | Meaning |
|---|---|
| **Event time** | When the real-world or M-Pesa event happened (e.g. the M-Pesa transaction time) |
| **Received time** | When our system received the callback, request, file or action |
| **Posting time** | When the journal was committed |

- Store all timestamps in **UTC**. Derive the **business date** in Africa/Nairobi (EAT). The business day closes at 23:59 EAT.
- **Cash is dated by M-Pesa event time.** **Revenue is dated by delivery event time.** An order placed 23:50 Monday and delivered 00:10 Tuesday holds on Monday and earns on Tuesday.
- Never substitute received time for event time because a callback was late.

## Identifiers

Keep these distinct. An order ID is not an event ID, and a receipt number is not a wallet ID.

| Kind | Example | Used for |
|---|---|---|
| Internal ID | `customer_id`, `journal_id` | Database identity |
| External business reference | M-Pesa receipt `QAB123XYZ`, order ID | Uniqueness against the outside world |
| Event ID | upstream `source_event_id` | Idempotency of incoming events |
| Idempotency key | client UUID, `(order_id, event_type)` | One effect per operation |

External identifiers are unique-constrained in the database. They are never primary keys.

## Customers and phone numbers

- Kenyan mobile numbers only in v1. Canonical form is **E.164 (`+254...`)**, produced by one shared normalisation function using a phone-number library with Kenya as the region (not hand-written string replacement; Kenyan mobile ranges now include 01xx numbers).
- A customer has a surrogate `customer_id` plus a unique canonical phone number. Phone-number **changes are rejected in v1**.
- A wallet is opened **only** by an explicit registration event. A payment never creates a wallet.
- **Wallets are matched on `BillRefNumber` only** (the account text the customer typed, up to 20 characters). Normalise it, look it up, and if it is missing, malformed, unregistered or closed, post to suspense. **No fuzzy matching.** Never use the payer's phone number to choose a wallet: the confirmation callback carries it masked or hashed (UNVERIFIED), and payer and wallet owner can differ.
- Store the original `BillRefNumber`, the normalised value, the payer MSISDN exactly as received, and the matching outcome and reason.

## Tenancy

Single tenant (Mtaani Express). No `tenant_id` column.

## Corrections

Posted journals are never edited or deleted. A correction is a **reversal** (exact mirror) plus a **replacement**, each with its own journal ID, linked to the original. See [03](03-events-and-posting.md).

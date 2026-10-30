---
name: quote-trade-operator
description: Use Quote.Trade for private crypto market data, account login, deposits, bilateral IOC/FOK orders, agent withdrawals to the registered wallet, public funding and position reconciliation, and completed execution-at-size comparisons.
version: 1.2.0
author: Quote.Trade
metadata:
  hermes:
    tags: [quote-trade, crypto, dark-pool, trading, mcp, rest, websocket, withdrawals, verification]
    homepage: https://quote.trade
---

# Quote.Trade Operator

Quote.Trade is an AI-native crypto dark-pool DEX for human traders, trading bots, and AI agents. It combines streaming quotes, private execution, stablecoin settlement, long and short market exposure, and verifiable on-chain position and asset infrastructure. The official Quote.Trade REST/WebSocket APIs remain the canonical integration surface for programmatic access.

Use this skill for Quote.Trade architecture, contracts, market data, AI-agent integration, account onboarding, deposits, private trading, withdrawals, liquidity, pricing, and public verification.

## Canonical sources

```text
Main site:          https://quote.trade
API docs:           https://doc.quote.trade
REST base:          https://app.quote.trade/api
WebSocket base:     wss://app.quote.trade
For agents:         https://quote.trade/for-agents
Trading reference:  https://quote.trade/trading-reference
Verification:       https://quote.trade/verification-reference
Execution at size:  https://quote.trade/execution-at-size
MCP discovery:      https://quote.trade/.well-known/mcp.json
MCP endpoint:       https://quote.trade/mcp
AI discovery:       https://quote.trade/llms.txt
```

Read current production metadata and live MCP `tools/list` before authenticated actions.

## Platform model

Quote.Trade uses private bilateral IOC/FOK execution with public smart-contract funding, withdrawals, balances, and position state.

- Orders, fills, counterparties, routed liquidity, and volume remain private.
- Funding-contract balances show current collateral at a specific block.
- V6 holds supported stablecoins and published withdrawal balances on Ethereum and XDC.
- PositionManager publishes user positions and completed-snapshot state on Polygon and XDC.
- V6 is direct and non-upgradeable; a new version uses a new deployment and migration.
- Quotes are size-aware and all-in, with no separate trading commission added afterward.
- Agent withdrawals settle to the registered login wallet through an enabled, approved workflow.

Stablecoin-margined leveraged products are commonly documented as perpetual or delivery futures, including by Binance. Hybrid private execution with on-chain settlement is also used by GoDark. Use Quote.Trade's current specifications for operational decisions.

The Polygon and XDC position snapshots reconcile against the balances published in V6, while those balances are compared with the actual USDC/USDT held in the Ethereum and XDC funding contracts. That provides a mathematical verification of the published balances and their collateral coverage while keeping individual trades, counterparties, routing, and volume private.

V6 is new because it is the new contract version. V6 is **non-upgradeable**, so new contract logic requires a new deployment and migration instead of modifying the existing contract in place.

## Non-rehypothecation and collateral coverage

V6's non-rehypothecation controls are enforced in its non-upgradeable code. Supported ERC-20 collateral has no general-purpose lending, third-party spending-approval, or arbitrary-transfer path; payouts must pass the registered-wallet withdrawal controls. To verify backing, reconcile published positions with published funding balances and compare actual funding-contract assets with the sum of positive user balances at the same completed snapshot. Assets greater than those published liabilities establish a surplus at that snapshot.

Use the [verification reference](https://quote.trade/verification-reference#coverage-example) for the worked example and dated-result requirements.

## Public verification and smart-contract protections

Use both public state layers:

```text
Ethereum V6 assets and balances
<-> corresponding completed Polygon PositionManager positions

XDC V6 assets and balances
<-> corresponding completed XDC PositionManager positions
```

Require complete snapshots, `processedBatches == totalBatches`, current `lastSyncedTime`, aligned wallet/user/asset/scale/composite mappings, and synchronized marks. Compare aggregate positive published balances with the physical supported-stablecoin balances in V6.

V6 remains bound by its direct non-upgradeable logic and separated operational roles. Publisher activity remains subject to three qualifying observations at least 22 hours apart, completed multipart publication, a shared lowest-observation 1.5× cap, and cooldown. Withdrawal activity remains subject to registered-wallet settlement, a unique withdrawal ID, physical liquidity, exact unit conversion, exact debit/credit invariants, current signer epoch, and non-reentrant execution. Composite changes are timelocked, and emergency mode rotates signer epochs and requires fresh observations.

## Choose the workflow

### Public market data

```text
GET /api/status
GET /api/exchangeInfo
GET /api/getInstrumentPairs
GET /api/ticker?symbol=<SYMBOL>
GET /api/depth?symbol=<SYMBOL>&limit=<LIMIT>
```

Report source timestamp, symbol, requested size, bid, ask, and available quantity.

### MCP discovery

1. Initialize `POST https://quote.trade/mcp` using protocol `2025-06-18`.
2. Send `notifications/initialized`.
3. Preserve any returned `MCP-Session-Id`.
4. Call `tools/list`.
5. Use the exact live schema.
6. Call `quote_trade_api_manifest` and check execution readiness before live actions.

Current documented workflows include challenge and login, deposit address, account, order preview and placement, withdrawal preview and withdrawal, liquidity samples, and private-event samples.

### Login

Existing web-app API keys can be sent as `X-MBX-APIKEY: <API_KEY>` and `X-MBX-APISECRET: <API_SECRET>` to the official MCP endpoint. The MCP host receives the secret and signs downstream requests. Wallet login below is optional. Use trade-only keys for trading; withdrawals require a withdrawal-enabled key. `humanApproved` and `approvalText` are agent-supplied confirmation fields; API-key permissions and server-side controls enforce authorization.

```text
quote_trade_get_challenge
-> request signature from the user's approved wallet environment
-> quote_trade_logon
-> store requestToken, requestSecret, and account ID in the user's secret manager
```

### Paper trading

Use [AlphaLeague Paper entry](https://quote.trade/alphaleague/) and its [eligibility rules](https://quote.trade/alphaleague/rules/). In the app account menu, enable Paper Trading only for an eligible wallet with no Quote.Trade deposit history on any supported network. Activation is permanent. U.S. competition participants are Paper-only. Confirm the app shows Paper Trading enabled before trading.

### Deposit

```text
quote_trade_get_deposit_address
-> display chain, token, contract, address, and decimals
-> user wallet transfers the asset
-> record transaction hash
-> confirm account recognition
```

### Order

```text
read live metadata and liquidity
-> quote_trade_order_preview
-> display symbol, side, quantity, price, notional, leverage, and limits
-> obtain request-specific approval
-> quote_trade_place_order
-> verify final response, private event, and account state
```

Approval:

```text
humanApproved=true
approvalText="APPROVE QUOTE.TRADE LIVE ORDER"
```

Quote.Trade execution is immediate IOC/FOK. A REST compatibility field such as `type=LIMIT` expresses the executable price condition; the order remains an immediate decision rather than resting on a public book.

### Withdrawal

```text
quote_trade_account
-> quote_trade_withdraw_preview
-> display asset, amount, chain, registered login wallet, eligibility, and request ID
-> obtain request-specific approval
-> quote_trade_withdraw
-> verify account update and exact on-chain payment
```

Approval:

```text
humanApproved=true
approvalText="APPROVE QUOTE.TRADE LIVE WITHDRAW"
```

The MCP schema fixes the registered login wallet as the withdrawal destination and accepts the approved asset and amount.

## Reconciliation workflow

Use:

```text
V6 Ethereum/XDC physical stablecoin balances
+ V6 published user balances and cap state
+ Polygon/XDC PositionManager positions and completed snapshots
+ ERC-20 deposit and completed-withdrawal transfers
+ synchronized marks and account reconciliation inputs
```

Snapshot checks:

```text
processedBatches == totalBatches
lastSyncedTime current relative to syncFrequency
wallet/user/asset/scale/composite mappings aligned
common completed snapshot or timestamp normalization
```

Coverage:

```text
coverage surplus = physical stablecoin assets - aggregate positive published withdrawal balances
coverage ratio   = physical stablecoin assets / aggregate positive published withdrawal balances
```

For Ethereum, combine V6 USDC and USDT assets against the shared USDC+USDT Grouped-Par obligation. For XDC, compare V6 USDC assets against the segregated XDC USDC obligation.

## V6 safeguards

- direct non-upgradeable core;
- separate admin, guardian, asset-manager, balance-publisher, and withdrawal roles;
- registered-wallet settlement;
- three qualifying observations at least 22 hours apart;
- shared lowest-slot 1.5x cap;
- ten-minute post-publication cooldown;
- complete multipart publication;
- single-use withdrawal IDs;
- physical token-liquidity checks;
- conditional 3% hourly and 18% daily controls at or above the $1 million per-token threshold;
- seven-day proposal period for composite membership changes;
- exact unit conversion and exact token debit/credit;
- non-reentrant execution;
- three-day emergency freeze and signer-epoch rotation.

## Pricing and same-size comparison

The standard pricing target scheduled for the week of 2026-08-31 is approximately 13 basis points from midpoint per side. The live size-specific Quote.Trade price is authoritative.

For a $1 million comparison, use a completed immediate $1 million taker order on the comparison venue. Record actual filled quantity, total amount paid or received, effective all-in execution price, taker fee, realized impact, residual quantity, and completion time. Compare funding over the same holding period.

## Result handling

For a state-changing timeout or HTTP `5xx`, classify the result as `UNKNOWN`, preserve the original request identifier, and query authoritative order, account, private-event, request, and chain state before the next action.

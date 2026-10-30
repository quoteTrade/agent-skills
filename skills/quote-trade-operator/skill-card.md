# Skill Card: Quote.Trade Operator

- **Name:** `quote-trade-operator`
- **Version:** `1.2.0`
- **Publisher:** Quote.Trade
- **License:** MIT-0
- **Category:** Finance / Crypto / Agent integrations
- **Purpose:** Explain and operate Quote.Trade through public REST data, WebSocket guidance, MCP discovery, and guarded account, deposit, trading, and registered-wallet withdrawal workflows.

## Network access

The skill may direct Hermes to canonical Quote.Trade public endpoints:

- `https://quote.trade`
- `https://doc.quote.trade`
- `https://app.quote.trade/api`
- `wss://app.quote.trade`

## Included executable code

`scripts/quote_trade_readonly.py` uses the Python standard library. It performs public GET requests and public MCP calls only. It contains an explicit allowlist and refuses private/account/trading tool names.

## Credentials

No credentials are included or required for the bundled helper. Authenticated workflows use the user's own Quote.Trade API key and secret, sent as `X-MBX-APIKEY`/`X-MBX-APISECRET` to the official MCP endpoint and kept in the user's secret manager, never pasted into chat. Use a trade-only key for trading; withdrawals need a withdrawal-enabled key.

## Prohibited capabilities

- withdrawals or transfers without request-specific user approval, or to any destination other than the registered login wallet
- private-key or seed-phrase handling
- wallet signing by the model (signatures come from the user's approved wallet environment)
- staking or unstaking
- unrestricted autonomous live-order loops
- silent leverage enablement

## Live trading and withdrawals

Any live order requires exact order preview, enforceable symbol/notional/leverage controls, explicit user approval, server-side trading enablement, and an unambiguous server response.

Any live withdrawal requires a withdrawal preview, a withdrawal-enabled key, explicit request-specific approval, and payment only to the registered login wallet; verify the exact on-chain payment afterwards.

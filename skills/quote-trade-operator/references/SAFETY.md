# Quote.Trade Agent Safety Policy

## Default state

The default mode is public, read-only market data. No credential should be requested for status, exchange information, instruments, ticker, or depth.

## Secret handling

Never expose any of the following to the language model or user-visible output:

- API secret or request secret
- private key or seed phrase
- wallet-signing material
- bearer token or session cookie
- HMAC key or raw signed payload containing secret material
- credential files

Use a local secret store, Hermes secure environment setup, or a server-side credential broker. Do not ask users to paste secrets into chat.

## Permission model

Grant the least privilege:

- market-data agent: public access only
- account assistant: read-only account access
- trading assistant: order permission only after independent controls are active
- deposit assistant: retrieve the deposit address; any transfer requires a user-authorized wallet transaction outside MCP
- withdrawal assistant: withdrawal-enabled credentials, request-specific authorization, server-side controls, and payment only to the registered login wallet
- no AI agent: staking, unstaking, private-key, or seed-phrase access; wallet signing remains in the user-approved wallet environment

## Pre-trade controls

Before any live order:

1. Normalize symbol, side, type, quantity, price, settlement currency, leverage state, and estimated notional.
2. Fetch a fresh quote or validate the limit price.
3. Confirm the symbol is allowlisted.
4. Confirm estimated notional is under the configured maximum.
5. Keep leverage disabled unless explicitly requested and authorized.
6. Display the exact order and state that no order has yet been sent.
7. Require explicit approval for that exact order.
8. For the documented MCP flow, require `APPROVE QUOTE.TRADE LIVE ORDER` and `humanApproved=true`.

## Post-trade controls

- Record order ID and returned state.
- Do not expose secrets in logs.
- If the request times out or returns `5XX`, treat execution as unknown and reconcile before retrying.
- Stop after the approved action. Do not turn one approval into an ongoing strategy loop.

## Forbidden behavior

- withdrawal or transfer without the user's authorization
- wallet signing by a model
- collection of private keys or seed phrases
- unbounded order loops
- silent leverage enablement
- order submission without exact preview and approval
- blind retry after ambiguous execution
- invention of undocumented private schemas

# Quote.Trade MCP Reference

## Endpoint

```text
POST https://quote.trade/mcp
```

Transport: Streamable HTTP with JSON-RPC 2.0. The documented protocol version is `2025-06-18`.

`GET /mcp` is not the invocation method. An HTTP 405 response to `GET` is expected unless the server separately supports server-initiated SSE.

## Standard sequence

1. Send `initialize` with the supported protocol version and client information.
2. Read `Mcp-Session-Id` if the server issues one.
3. Send `notifications/initialized` with the negotiated protocol version and session header.
4. Call `ping` if desired.
5. Call `tools/list`.
6. Invoke an allowlisted public tool through `tools/call`.

Use headers:

```text
Content-Type: application/json
Accept: application/json, text/event-stream
MCP-Protocol-Version: 2025-06-18
Mcp-Session-Id: <only when issued by the server>
```

## Public tools

The current official agent guide documents these public tools:

- `quote_trade_api_manifest`
- `quote_trade_status`
- `quote_trade_exchange_info`
- `quote_trade_instruments`
- `quote_trade_ticker`
- `quote_trade_depth`

Public tools map to existing Quote.Trade REST endpoints.

## Guarded tools

Official materials also describe selected account, order-preview, order-placement, liquidity-stream, and private-event workflows. They require the relevant server-side capability, credentials, permissions, and safety controls.

Never assume the existence or availability of a guarded tool from its name alone. Confirm through `tools/list` and inspect its input schema.

## Live order gates

The documented live MCP flow should require:

- a prior order preview
- human approval for the exact normalized order
- `humanApproved=true`
- exact approval text: `APPROVE QUOTE.TRADE LIVE ORDER`
- server-side trading enabled
- scoped per-request API credentials
- allowed-symbol validation (an empty allowlist denies all symbols)
- maximum-notional validation (`maxNotionalUsd > 0` is required)
- leverage disabled unless explicitly allowed

Withdrawals follow the guarded workflow in `SKILL.md` and settle only to the registered login wallet. Wallet signing remains outside MCP; the bundled helper remains read-only. `humanApproved` and `approvalText` are agent-supplied confirmation fields; API-key permissions and server-side controls enforce authorization.

## Bundled test helper

```bash
python ${HERMES_SKILL_DIR}/scripts/quote_trade_readonly.py mcp-tools
python ${HERMES_SKILL_DIR}/scripts/quote_trade_readonly.py mcp-call quote_trade_ticker --arguments '{"symbol":"BTC"}'
```

The helper allowlists public tools and refuses account or trading tools.

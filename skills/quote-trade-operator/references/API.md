# Quote.Trade API Reference for Agents

## Canonical bases

- REST: `https://app.quote.trade/api`
- WebSocket: `wss://app.quote.trade`
- Documentation: `https://doc.quote.trade`

## Verified public REST routes

| Purpose | Request |
|---|---|
| Status | `GET /api/status` |
| Exchange metadata | `GET /api/exchangeInfo` |
| Instruments | `GET /api/getInstrumentPairs` |
| Ticker | `GET /api/ticker?symbol=BTC` |
| Depth | `GET /api/depth?symbol=BTC&limit=100` |

Public routes require no API key. Use an explicit timeout, parse JSON defensively, and record retrieval time.

## Private routes

Use only the exact private request/response schemas in the current Quote.Trade documentation or trading reference. Do not infer a private schema solely because the API follows Binance V3-compatible patterns.

The official documentation describes API keys through `X-MBX-APIKEY` and HMAC SHA-256 signing for documented signed requests. Keep secrets outside prompts, terminal transcripts, screenshots, browser-visible output, and model traces.

## WebSocket routes

- Liquidity data: `wss://app.quote.trade/ws/liquidity`
- Authorized private events: `wss://app.quote.trade/ws/listenKey`

Use WebSocket for sustained real-time feeds. Implement reconnect backoff, heartbeat handling, stale-event detection, resubscription, and bounded queue sizes.

## Rate limits and errors

- Shared API limit documented by Quote.Trade: 1,200 requests per minute based on IP, subject to route weights and change.
- On `429`, stop and obey `Retry-After`.
- Repeated violations can produce `418`; do not retry until the stated interval expires.
- A `403` may indicate WAF rejection.
- A `5XX` after an order request means the execution state may be unknown. Reconcile order/account state before any retry.

## All-in quote semantics

Quote.Trade presents an all-in execution price and adds no separate trading commission. Agents should display the quoted execution price as the platform cost and must not add an assumed commission. Network costs outside the Quote.Trade quote may exist when users move assets on-chain, but they are not a separate Quote.Trade trading fee.

## Reliability checklist

- use UTC timestamps
- use finite connect/read timeouts
- retry only idempotent reads, with bounded exponential backoff
- never automatically retry a possibly accepted order
- validate symbol, type, and numeric strings
- detect stale timestamps or update identifiers
- preserve `Retry-After`
- redact all authorization material

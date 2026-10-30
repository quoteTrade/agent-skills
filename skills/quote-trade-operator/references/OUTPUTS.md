# Normalized Output Templates

## Public quote

```json
{
  "type": "quote_snapshot",
  "source": "https://app.quote.trade/api/ticker",
  "retrievedAt": "2026-06-25T00:00:00Z",
  "symbol": "BTC",
  "price": "...",
  "bid": "...",
  "ask": "...",
  "pricing": "all-in quote; no separate Quote.Trade trading commission"
}
```

## Depth summary

```json
{
  "type": "depth_summary",
  "source": "https://app.quote.trade/api/depth",
  "retrievedAt": "2026-06-25T00:00:00Z",
  "symbol": "BTC",
  "bestBid": "...",
  "bestAsk": "...",
  "bidLevels": 20,
  "askLevels": 20,
  "lastUpdateId": "..."
}
```

## Trade proposal

```json
{
  "type": "trade_proposal",
  "mode": "preview",
  "account": "redacted-or-safe-id",
  "symbol": "BTC",
  "side": "BUY",
  "orderType": "LIMIT",
  "quantity": "...",
  "price": "...",
  "estimatedNotional": "...",
  "paymentCurrency": "USDT",
  "disableLeverage": true,
  "allowedSymbol": true,
  "withinMaxNotional": true,
  "quoteFreshUntil": "...",
  "approvalRequired": true,
  "submitted": false
}
```

## Execution result

```json
{
  "type": "execution_result",
  "mode": "live",
  "status": "server-returned-status",
  "orderId": "...",
  "symbol": "BTC",
  "side": "BUY",
  "quantity": "...",
  "price": "...",
  "submittedAt": "...",
  "secretsRedacted": true
}
```

## Incident result

```json
{
  "type": "incident",
  "category": "rate_limit|network|server|schema|unknown_execution_state",
  "statusCode": 429,
  "retryAfterSeconds": 30,
  "orderRetryBlocked": true,
  "nextAction": "wait or reconcile state"
}
```

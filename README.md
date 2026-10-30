# Quote.Trade agent skills

Agent skills for [Quote.Trade](https://quote.trade), the AI-native crypto dark-pool DEX.

| Skill | Version | What it does |
| --- | --- | --- |
| [`quote-trade-operator`](skills/quote-trade-operator/SKILL.md) | 1.2.0 | Use Quote.Trade for private crypto market data, account login, deposits, bilateral IOC/FOK orders, agent withdrawals to the registered wallet, public funding and position reconciliation, and completed execution-at-size comparisons. |

## Install

- **skills CLI** (Claude Code, Codex, Cursor and more): `npx skills add quoteTrade/agent-skills`
- **OpenClaw / ClawHub:** `openclaw skills install @quotetrade/quote-trade-operator`
- **Hosted copy:** https://quote.trade/.well-known/skills/quote-trade-operator/SKILL.md

## Hosted MCP server

The skill works with the Quote.Trade MCP server at `https://quote.trade/mcp` (Streamable HTTP, registry name `trade.quote/mcp`). Public market data needs no key; account, trading and withdrawal tools take a Quote.Trade API key in the `X-MBX-APIKEY` / `X-MBX-APISECRET` headers. See https://quote.trade/for-agents/.

## Source

The canonical copy of each skill is the one served from quote.trade. This repository mirrors it on each skill release.

## License

[MIT-0](LICENSE)

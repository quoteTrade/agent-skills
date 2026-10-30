#!/usr/bin/env python3
"""Read-only Quote.Trade REST and MCP helper for Hermes Agent.

This helper intentionally supports only public REST endpoints and public MCP
methods/tools. It has no credential flags and refuses account or trading tools.
"""

from __future__ import annotations

import argparse
import http.client
import json
import ssl
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urljoin, urlsplit
from urllib.request import Request, urlopen

DEFAULT_API_BASE = "https://app.quote.trade/api"
DEFAULT_MCP_URL = "https://quote.trade/mcp"
PROTOCOL_VERSION = "2025-06-18"
USER_AGENT = "quote-trade-hermes-skill/1.0"

PUBLIC_MCP_TOOLS = frozenset(
    {
        "quote_trade_api_manifest",
        "quote_trade_status",
        "quote_trade_exchange_info",
        "quote_trade_instruments",
        "quote_trade_ticker",
        "quote_trade_depth",
    }
)


@dataclass(frozen=True)
class HttpResult:
    status: int
    reason: str
    headers: dict[str, str]
    body: bytes
    elapsed_ms: float


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def emit(value: Any) -> None:
    print(json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True))


def api_url(base: str, path: str, query: dict[str, Any] | None = None) -> str:
    url = base.rstrip("/") + "/" + path.lstrip("/")
    if query:
        clean = {k: v for k, v in query.items() if v is not None}
        if clean:
            url += "?" + urlencode(clean)
    return url


def rest_get(url: str, timeout: float) -> dict[str, Any] | list[Any]:
    request = Request(
        url,
        method="GET",
        headers={"Accept": "application/json", "User-Agent": USER_AGENT},
    )
    started = time.perf_counter()
    try:
        with urlopen(request, timeout=timeout) as response:
            body = response.read()
            status = response.status
            headers = {k.lower(): v for k, v in response.headers.items()}
    except HTTPError as exc:
        body = exc.read()
        retry_after = exc.headers.get("Retry-After")
        detail = body.decode("utf-8", errors="replace")[:1000]
        raise RuntimeError(
            f"HTTP {exc.code} from {url}; retry-after={retry_after!r}; body={detail!r}"
        ) from exc
    except URLError as exc:
        raise RuntimeError(f"Network error for {url}: {exc.reason}") from exc

    elapsed_ms = (time.perf_counter() - started) * 1000
    content_type = headers.get("content-type", "")
    if not body:
        raise RuntimeError(f"HTTP {status} returned an empty body from {url}")
    try:
        value = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            f"HTTP {status} returned non-JSON content ({content_type}) from {url}"
        ) from exc

    if not isinstance(value, (dict, list)):
        raise RuntimeError(f"Expected a JSON object or array from {url}")

    return {
        "source": url,
        "retrievedAt": utc_now(),
        "httpStatus": status,
        "elapsedMs": round(elapsed_ms, 1),
        "data": value,
    }


def post_json(
    url: str,
    payload: dict[str, Any],
    headers: dict[str, str],
    timeout: float,
) -> HttpResult:
    """POST JSON while preserving POST across 307/308 redirects."""
    current_url = url
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")

    for _ in range(4):
        parsed = urlsplit(current_url)
        if parsed.scheme not in {"https", "http"} or not parsed.hostname:
            raise ValueError(f"Unsupported URL: {current_url}")

        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        path = parsed.path or "/"
        if parsed.query:
            path += "?" + parsed.query

        conn_cls = http.client.HTTPSConnection if parsed.scheme == "https" else http.client.HTTPConnection
        kwargs: dict[str, Any] = {"timeout": timeout}
        if parsed.scheme == "https":
            kwargs["context"] = ssl.create_default_context()

        conn = conn_cls(parsed.hostname, port, **kwargs)
        request_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "User-Agent": USER_AGENT,
            **headers,
        }

        started = time.perf_counter()
        try:
            conn.request("POST", path, body=body, headers=request_headers)
            response = conn.getresponse()
            response_body = response.read()
            elapsed_ms = (time.perf_counter() - started) * 1000
            response_headers = {key.lower(): value for key, value in response.getheaders()}
            status = response.status
            reason = response.reason
        finally:
            conn.close()

        if status in {307, 308}:
            location = response_headers.get("location")
            if not location:
                raise RuntimeError(f"HTTP {status} without Location header")
            current_url = urljoin(current_url, location)
            continue
        if status in {301, 302, 303}:
            raise RuntimeError(
                f"Endpoint returned HTTP {status}; refusing to convert MCP POST to GET"
            )

        return HttpResult(status, reason, response_headers, response_body, elapsed_ms)

    raise RuntimeError("Too many redirects")


def parse_json_or_sse(result: HttpResult, expected_id: int | None) -> dict[str, Any] | None:
    if not result.body:
        return None
    text = result.body.decode("utf-8", errors="replace")
    content_type = result.headers.get("content-type", "").lower()

    if "text/event-stream" not in content_type:
        value = json.loads(text)
        if not isinstance(value, dict):
            raise RuntimeError("Expected a JSON object response")
        return value

    candidates: list[dict[str, Any]] = []
    for line in text.splitlines():
        if not line.startswith("data:"):
            continue
        raw = line[5:].strip()
        if not raw or raw == "[DONE]":
            continue
        try:
            value = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            candidates.append(value)

    if expected_id is not None:
        for value in reversed(candidates):
            if value.get("id") == expected_id:
                return value
    return candidates[-1] if candidates else None


def rpc_result(label: str, response: dict[str, Any] | None, request_id: int) -> dict[str, Any]:
    if response is None:
        raise RuntimeError(f"{label}: empty response")
    if response.get("id") != request_id:
        raise RuntimeError(f"{label}: unexpected JSON-RPC id {response.get('id')!r}")
    if "error" in response:
        raise RuntimeError(f"{label}: JSON-RPC error {json.dumps(response['error'])}")
    value = response.get("result")
    if not isinstance(value, dict):
        raise RuntimeError(f"{label}: missing object result")
    return value


class McpClient:
    def __init__(self, url: str, timeout: float) -> None:
        self.url = url
        self.timeout = timeout
        self.headers: dict[str, str] = {}
        self.next_id = 1
        self.server_info: dict[str, Any] = {}
        self.protocol_version = PROTOCOL_VERSION

    def _request(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        request_id = self.next_id
        self.next_id += 1
        payload: dict[str, Any] = {"jsonrpc": "2.0", "id": request_id, "method": method}
        if params is not None:
            payload["params"] = params
        http_result = post_json(self.url, payload, self.headers, self.timeout)
        if not 200 <= http_result.status < 300:
            detail = http_result.body.decode("utf-8", errors="replace")[:1000]
            raise RuntimeError(f"{method}: HTTP {http_result.status} {detail!r}")
        return rpc_result(method, parse_json_or_sse(http_result, request_id), request_id)

    def initialize(self) -> dict[str, Any]:
        request_id = self.next_id
        self.next_id += 1
        payload = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": "initialize",
            "params": {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "quote-trade-hermes-skill", "version": "1.0.0"},
            },
        }
        http_result = post_json(self.url, payload, {}, self.timeout)
        if not 200 <= http_result.status < 300:
            detail = http_result.body.decode("utf-8", errors="replace")[:1000]
            raise RuntimeError(f"initialize: HTTP {http_result.status} {detail!r}")
        result = rpc_result("initialize", parse_json_or_sse(http_result, request_id), request_id)
        version = result.get("protocolVersion")
        if not isinstance(version, str) or not version:
            raise RuntimeError("initialize: server returned no protocolVersion")
        self.protocol_version = version
        self.headers["MCP-Protocol-Version"] = version
        session_id = http_result.headers.get("mcp-session-id")
        if session_id:
            self.headers["Mcp-Session-Id"] = session_id
        self.server_info = result.get("serverInfo") if isinstance(result.get("serverInfo"), dict) else {}

        notification = {"jsonrpc": "2.0", "method": "notifications/initialized"}
        notify_result = post_json(self.url, notification, self.headers, self.timeout)
        if notify_result.status not in {200, 202, 204}:
            detail = notify_result.body.decode("utf-8", errors="replace")[:1000]
            raise RuntimeError(
                f"notifications/initialized: HTTP {notify_result.status} {detail!r}"
            )
        return result

    def list_tools(self) -> list[dict[str, Any]]:
        result = self._request("tools/list", {})
        tools = result.get("tools")
        if not isinstance(tools, list):
            raise RuntimeError("tools/list: result.tools is not an array")
        return [tool for tool in tools if isinstance(tool, dict)]

    def call_public_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if name not in PUBLIC_MCP_TOOLS:
            allowed = ", ".join(sorted(PUBLIC_MCP_TOOLS))
            raise RuntimeError(f"Refusing non-public MCP tool {name!r}. Allowed: {allowed}")
        return self._request("tools/call", {"name": name, "arguments": arguments})


def command_rest(args: argparse.Namespace) -> Any:
    if args.command == "status":
        return rest_get(api_url(args.api_base, "status"), args.timeout)
    if args.command == "exchange-info":
        return rest_get(api_url(args.api_base, "exchangeInfo"), args.timeout)
    if args.command == "instruments":
        return rest_get(api_url(args.api_base, "getInstrumentPairs", {"limit": args.limit}), args.timeout)
    if args.command == "ticker":
        return rest_get(api_url(args.api_base, "ticker", {"symbol": args.symbol.upper()}), args.timeout)
    if args.command == "depth":
        return rest_get(
            api_url(args.api_base, "depth", {"symbol": args.symbol.upper(), "limit": args.limit}),
            args.timeout,
        )
    raise RuntimeError(f"Unsupported command: {args.command}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-base", default=DEFAULT_API_BASE)
    parser.add_argument("--mcp-url", default=DEFAULT_MCP_URL)
    parser.add_argument("--timeout", type=float, default=20.0)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("status")
    sub.add_parser("exchange-info")

    instruments = sub.add_parser("instruments")
    instruments.add_argument("--limit", type=int, default=5000)

    ticker = sub.add_parser("ticker")
    ticker.add_argument("symbol")

    depth = sub.add_parser("depth")
    depth.add_argument("symbol")
    depth.add_argument("--limit", type=int, default=100)

    sub.add_parser("mcp-tools")

    call = sub.add_parser("mcp-call")
    call.add_argument("tool")
    call.add_argument("--arguments", default="{}", help="JSON object")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        if args.command in {"status", "exchange-info", "instruments", "ticker", "depth"}:
            emit(command_rest(args))
            return 0

        client = McpClient(args.mcp_url, args.timeout)
        init = client.initialize()
        tools = client.list_tools()
        public = [tool for tool in tools if tool.get("name") in PUBLIC_MCP_TOOLS]

        if args.command == "mcp-tools":
            emit(
                {
                    "source": args.mcp_url,
                    "retrievedAt": utc_now(),
                    "protocolVersion": client.protocol_version,
                    "serverInfo": client.server_info,
                    "publicTools": public,
                    "allAdvertisedToolNames": [tool.get("name") for tool in tools],
                }
            )
            return 0

        try:
            arguments = json.loads(args.arguments)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"--arguments must be valid JSON: {exc}") from exc
        if not isinstance(arguments, dict):
            raise RuntimeError("--arguments must decode to a JSON object")
        advertised = {tool.get("name") for tool in tools}
        if args.tool not in advertised:
            raise RuntimeError(f"MCP server did not advertise tool {args.tool!r}")
        result = client.call_public_tool(args.tool, arguments)
        emit(
            {
                "source": args.mcp_url,
                "retrievedAt": utc_now(),
                "tool": args.tool,
                "arguments": arguments,
                "result": result,
            }
        )
        return 0
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        emit({"ok": False, "error": str(exc), "retrievedAt": utc_now()})
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

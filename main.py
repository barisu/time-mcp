import argparse
import os
from datetime import datetime
from typing import Sequence

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

LOCAL_BIND_HOSTS = {"127.0.0.1", "localhost", "::1"}
WILDCARD_BIND_HOSTS = {"0.0.0.0", "::", "[::]"}
DEFAULT_ALLOWED_HOSTS = ["127.0.0.1:*", "localhost:*", "[::1]:*"]
DEFAULT_ALLOWED_ORIGINS = [
    "http://127.0.0.1:*",
    "http://localhost:*",
    "http://[::1]:*",
]


def _env_int(name: str, default: int) -> int:
    return int(os.getenv(name, str(default)))


def _env_path(name: str, default: str) -> str:
    value = os.getenv(name, default)
    return value if value.startswith("/") else f"/{value}"


def _split_csv(values: Sequence[str] | None) -> list[str]:
    items: list[str] = []
    for value in values or ():
        for item in value.split(","):
            normalized = item.strip()
            if normalized:
                items.append(normalized)
    return items


def _env_list(name: str) -> list[str]:
    value = os.getenv(name)
    if not value:
        return []
    return _split_csv([value])


def _unique(values: Sequence[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _host_pattern(host: str) -> str:
    if ":" in host and not host.startswith("["):
        return f"[{host}]:*"
    return f"{host}:*"


def _origin_patterns_from_host_pattern(host_pattern: str) -> list[str]:
    if ":" not in host_pattern:
        return [f"http://{host_pattern}", f"https://{host_pattern}"]

    host, port = host_pattern.rsplit(":", 1)
    return [f"http://{host}:{port}", f"https://{host}:{port}"]


def _default_allowed_hosts(host: str) -> list[str]:
    if host in LOCAL_BIND_HOSTS:
        return DEFAULT_ALLOWED_HOSTS.copy()
    return []


def _default_allowed_origins(host: str) -> list[str]:
    if host in LOCAL_BIND_HOSTS:
        return DEFAULT_ALLOWED_ORIGINS.copy()
    return []


def _inferred_allowed_hosts(host: str) -> list[str]:
    if host in WILDCARD_BIND_HOSTS:
        return []
    if host in LOCAL_BIND_HOSTS:
        return DEFAULT_ALLOWED_HOSTS.copy()
    return [_host_pattern(host)]


def _inferred_allowed_origins(host: str) -> list[str]:
    if host in LOCAL_BIND_HOSTS:
        return DEFAULT_ALLOWED_ORIGINS.copy()
    if host in WILDCARD_BIND_HOSTS:
        return []

    normalized_host = host if ":" not in host or host.startswith("[") else f"[{host}]"
    return [f"http://{normalized_host}:*", f"https://{normalized_host}:*"]


def _build_transport_security(
    host: str,
    allowed_hosts: Sequence[str],
    allowed_origins: Sequence[str],
) -> TransportSecuritySettings | None:
    default_hosts = _default_allowed_hosts(host)
    default_origins = _default_allowed_origins(host)
    explicit_hosts = _unique(allowed_hosts)
    explicit_origins = _unique(allowed_origins)

    if not default_hosts and not explicit_hosts and not explicit_origins:
        return None

    inferred_hosts = _inferred_allowed_hosts(host) if explicit_origins and not explicit_hosts else []
    inferred_origins = _inferred_allowed_origins(host) if explicit_origins else []

    merged_hosts = _unique([*default_hosts, *inferred_hosts, *explicit_hosts])
    merged_origins = _unique([*default_origins, *inferred_origins, *explicit_origins])

    if explicit_hosts and not explicit_origins:
        derived_origins: list[str] = []
        for host_pattern in explicit_hosts:
            derived_origins.extend(_origin_patterns_from_host_pattern(host_pattern))
        merged_origins = _unique([*merged_origins, *derived_origins])

    if explicit_origins and not merged_hosts:
        raise ValueError(
            "Allowed origins require allowed hosts when binding to a wildcard address. "
            "Set --allow-host or FASTMCP_ALLOWED_HOSTS."
        )

    return TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=merged_hosts,
        allowed_origins=merged_origins,
    )


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="time-mcp HTTP MCP server")
    parser.add_argument(
        "--host",
        default=os.getenv("FASTMCP_HOST", "127.0.0.1"),
        help="Bind host. Overrides FASTMCP_HOST.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=_env_int("FASTMCP_PORT", 8000),
        help="Bind port. Overrides FASTMCP_PORT.",
    )
    parser.add_argument(
        "--streamable-http-path",
        default=_env_path("FASTMCP_STREAMABLE_HTTP_PATH", "/mcp"),
        help="MCP endpoint path. Overrides FASTMCP_STREAMABLE_HTTP_PATH.",
    )
    parser.add_argument(
        "--allow-origin",
        action="append",
        default=[],
        metavar="ORIGIN",
        help=(
            "Allowed Origin header value. Repeat or use a comma-separated list. "
            "Values are appended to FASTMCP_ALLOWED_ORIGINS."
        ),
    )
    parser.add_argument(
        "--allow-host",
        action="append",
        default=[],
        metavar="HOST",
        help=(
            "Allowed Host header value. Repeat or use a comma-separated list. "
            "Values are appended to FASTMCP_ALLOWED_HOSTS."
        ),
    )
    return parser.parse_args(argv)


def create_mcp(argv: Sequence[str] | None = None) -> FastMCP:
    args = parse_args(argv)
    allowed_origins = _unique([*_env_list("FASTMCP_ALLOWED_ORIGINS"), *_split_csv(args.allow_origin)])
    allowed_hosts = _unique([*_env_list("FASTMCP_ALLOWED_HOSTS"), *_split_csv(args.allow_host)])
    transport_security = _build_transport_security(
        host=args.host,
        allowed_hosts=allowed_hosts,
        allowed_origins=allowed_origins,
    )

    mcp = FastMCP(
        name="time-mcp",
        instructions="Return the current server datetime.",
        host=args.host,
        port=args.port,
        streamable_http_path=args.streamable_http_path,
        transport_security=transport_security,
    )

    @mcp.tool()
    def get_current_datetime() -> str:
        """Return the current server datetime as an ISO 8601 string with timezone offset."""
        return datetime.now().astimezone().isoformat(timespec="seconds")

    @mcp.custom_route("/", methods=["GET"], include_in_schema=False)
    async def index(_: Request) -> Response:
        return JSONResponse(
            {
                "name": mcp.name,
                "transport": "streamable-http",
                "endpoint": mcp.settings.streamable_http_path,
                "tool": "get_current_datetime",
            }
        )

    return mcp


def main(argv: Sequence[str] | None = None) -> None:
    create_mcp(argv).run(transport="streamable-http")


if __name__ == "__main__":
    main()

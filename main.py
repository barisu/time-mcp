import os
from datetime import datetime

from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


def _env_int(name: str, default: int) -> int:
    return int(os.getenv(name, str(default)))


def _env_path(name: str, default: str) -> str:
    value = os.getenv(name, default)
    return value if value.startswith("/") else f"/{value}"


mcp = FastMCP(
    name="time-mcp",
    instructions="Return the current server datetime.",
    host=os.getenv("FASTMCP_HOST", "127.0.0.1"),
    port=_env_int("FASTMCP_PORT", 8000),
    streamable_http_path=_env_path("FASTMCP_STREAMABLE_HTTP_PATH", "/mcp"),
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


def main() -> None:
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()

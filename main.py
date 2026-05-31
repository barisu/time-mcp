from datetime import datetime

from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


mcp = FastMCP(
    name="time-mcp",
    instructions="Return the current server datetime.",
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

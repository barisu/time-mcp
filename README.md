# time-mcp

HTTP only MCP server that exposes a single tool, `get_current_datetime`, and returns the current server datetime in ISO 8601 format with a timezone offset.

## Run

```bash
uv sync
uv run time-mcp
```

The server starts with Streamable HTTP on `http://127.0.0.1:8000/mcp`.

You can change the bind settings with FastMCP environment variables, for example:

```bash
FASTMCP_HOST=0.0.0.0 FASTMCP_PORT=8080 uv run time-mcp
```

`GET /` returns a small JSON document with the MCP endpoint and tool name.

## Run as a service

If you want to register it on a server, the simplest option is a `systemd` service.

1. Prepare the project once.

```bash
cd /opt/time-mcp
uv sync
```

2. Create `/etc/systemd/system/time-mcp.service`.

```ini
[Unit]
Description=time-mcp HTTP MCP server
After=network.target

[Service]
Type=simple
User=time-mcp
Group=time-mcp
WorkingDirectory=/opt/time-mcp
Environment=FASTMCP_HOST=0.0.0.0
Environment=FASTMCP_PORT=8000
ExecStart=/opt/time-mcp/.venv/bin/time-mcp
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

3. Register and start the service.

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now time-mcp
sudo systemctl status time-mcp
```

With this setup, the MCP endpoint is available at `http://<server>:8000/mcp`.
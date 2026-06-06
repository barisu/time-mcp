# time-mcp

HTTP only MCP server that exposes a single tool, `get_current_datetime`, and returns the current server datetime in ISO 8601 format with a timezone offset.

## Run

```bash
uv sync
uv run time-mcp
```

The server starts with Streamable HTTP on `http://127.0.0.1:8000/mcp`.

You can change the bind settings with this app's environment variables:

```bash
FASTMCP_HOST=0.0.0.0 FASTMCP_PORT=8080 uv run time-mcp
```

You can also pass runtime options:

```bash
uv run time-mcp --host 0.0.0.0 --port 8080
```

You can also change the MCP path:

```bash
FASTMCP_STREAMABLE_HTTP_PATH=/time uv run time-mcp
```

## Allowing additional origins

When the server is bound to localhost, browser requests from localhost are allowed by default. To allow additional `Origin` values, pass `--allow-origin` at startup or set `FASTMCP_ALLOWED_ORIGINS`.

```bash
uv run time-mcp \
  --allow-origin https://app.example.com \
  --allow-origin https://admin.example.com
```

Comma-separated values are also supported:

```bash
FASTMCP_ALLOWED_ORIGINS=https://app.example.com,https://admin.example.com uv run time-mcp
```

If you bind to a wildcard host such as `0.0.0.0`, also set the allowed host list so Host header validation can stay enabled:

```bash
uv run time-mcp \
  --host 0.0.0.0 \
  --allow-host mcp.example.com:* \
  --allow-origin https://app.example.com
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

`ExecStart=/opt/time-mcp/.venv/bin/time-mcp` works because `uv sync` installs the project and generates the console script from `[project.scripts]` in `pyproject.toml`. If you prefer not to rely on that entry point, you can use this instead:

```ini
ExecStart=/opt/time-mcp/.venv/bin/python /opt/time-mcp/main.py
```
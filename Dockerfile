FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim

WORKDIR /app

COPY pyproject.toml README.md main.py ./

RUN uv sync --no-dev

ENV PATH="/app/.venv/bin:${PATH}" \
    FASTMCP_HOST=0.0.0.0 \
    FASTMCP_PORT=8000

EXPOSE 8000

CMD ["time-mcp"]

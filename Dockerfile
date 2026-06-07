FROM ghcr.io/astral-sh/uv:python3.12-alpine

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

COPY pyproject.toml uv.lock README.md ./
COPY src ./src

RUN uv sync --locked --no-dev

WORKDIR /workspace

ENTRYPOINT ["/app/.venv/bin/tool-mermaid"]
CMD ["."]

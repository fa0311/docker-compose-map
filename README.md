# docker-compose-map

Render Docker Compose stacks as Mermaid Markdown.

## Usage

```bash
docker run --rm -v "$PWD:/workspace" ghcr.io/fa0311/docker-compose-map:latest . -o compose-graph.md
```

Without `-o`, the rendered Markdown is printed to stdout:

```bash
docker run --rm -v "$PWD:/workspace" ghcr.io/fa0311/docker-compose-map:latest .
```

From a local checkout:

```bash
uv run tool-mermaid ./stacks -o compose-graph.md
uv run tool-mermaid './stacks/**/compose.yaml'
```

Inputs can be Compose files, directories, or glob-like paths. Supported Compose
filenames are `compose.yaml`, `compose.yml`, `docker-compose.yaml`, and
`docker-compose.yml`.

## Output

`-o` updates a Markdown template file. Existing text outside placeholder blocks
is preserved.

````markdown
<!-- compose-map:map:start -->
```mermaid
graph LR
```
<!-- compose-map:map:end -->
````

The built-in default template contains `dependencies`, `map`, `network`, and
`volumes` blocks. Templates may include only the blocks they need.

## Development

```bash
uv sync --locked --all-groups
uv run ruff check .
uv run pyright
uv run pytest
docker build -t docker-compose-map .
```

## License

MIT

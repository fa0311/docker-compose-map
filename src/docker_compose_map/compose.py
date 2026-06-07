from __future__ import annotations

import posixpath
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import yaml
from pydantic import TypeAdapter

from docker_compose_map.discovery import ComposeSelection
from docker_compose_map.domain import Network, Service, Stack

ComposeData = dict[str, Any]
COMPOSE_DATA = TypeAdapter(ComposeData)


def load_stacks(selection: ComposeSelection) -> tuple[Stack, ...]:
    return tuple(stack_from_file(path, selection.root) for path in selection.files)


def stack_from_file(path: Path, root: Path) -> Stack:
    data = load_compose_file(path)
    rel_dir = path.parent.relative_to(root).as_posix() or "."
    uid = "root" if rel_dir == "." else rel_dir
    name = str(data.get("name") or path.parent.name)
    return parse_stack(
        data=data,
        name=name,
        uid=uid,
        rel_dir=rel_dir,
        stack_dir=path.parent.as_posix(),
    )


def load_compose_file(path: Path) -> ComposeData:
    raw_data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data = COMPOSE_DATA.validate_python(raw_data)
    if "services" not in data:
        raise ValueError(f"{path} is not a compose file: missing 'services'")
    return data


def parse_stack(data: ComposeData, name: str, uid: str, rel_dir: str, stack_dir: str) -> Stack:
    networks = {
        alias: _parse_network(alias, definition)
        for alias, definition in _mapping(data.get("networks")).items()
    }
    volumes = frozenset(str(name) for name in _mapping(data.get("volumes")))
    services = {
        service_name: _parse_service(service_name, service_data, volumes, stack_dir)
        for service_name, service_data in _mapping(data.get("services")).items()
    }
    return Stack(
        name=name,
        uid=uid,
        rel_dir=rel_dir,
        services=services,
        networks=networks,
        volumes=volumes,
    )


def _parse_network(alias: str, definition: Any) -> Network:
    network = _mapping(definition)
    external = network.get("external", False)
    external_name = external.get("name") if isinstance(external, Mapping) else None
    global_name = network.get("name") or external_name or alias
    return Network(alias=alias, external=bool(external), global_name=str(global_name))


def _parse_service(
    service_name: str,
    service_data: Any,
    named_volumes: frozenset[str],
    stack_dir: str,
) -> Service:
    service = _mapping(service_data)
    mounts, host_mounts = _service_volumes(service, named_volumes, stack_dir)
    return Service(
        name=service_name,
        depends_on=_as_tuple(service.get("depends_on")),
        netns_target=_netns_target(service.get("network_mode")),
        networks=_as_tuple(service.get("networks")),
        ports=tuple(
            port
            for raw_port in _sequence(service.get("ports"))
            if (port := _published_port(raw_port)) is not None
        ),
        mounts=mounts,
        host_mounts=host_mounts,
    )


def _mapping(value: Any) -> Mapping[str, Any]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return value
    raise TypeError(f"expected a mapping, got {type(value).__name__}")


def _sequence(value: Any) -> Sequence[Any]:
    if value is None:
        return ()
    if isinstance(value, Sequence) and not isinstance(value, str):
        return value
    return (value,)


def _as_tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, Mapping):
        return tuple(str(key) for key in value)
    if isinstance(value, Sequence) and not isinstance(value, str):
        return tuple(str(item) for item in value)
    return (str(value),)


def _netns_target(value: Any) -> str | None:
    if isinstance(value, str) and value.startswith("service:"):
        return value.split(":", 1)[1]
    return None


def _published_port(spec: Any) -> str | None:
    if isinstance(spec, Mapping):
        published = spec.get("published")
        return str(published) if published is not None else None

    text = str(spec).split("/", 1)[0]
    parts = text.split(":")
    if len(parts) >= 2:
        return parts[-2]
    return None


def _service_volumes(
    service: Mapping[str, Any],
    named_volumes: frozenset[str],
    stack_dir: str,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    mounts: list[str] = []
    host_mounts: list[str] = []
    for entry in _sequence(service.get("volumes")):
        source = _volume_source(entry)
        if source is None:
            continue
        if _is_named_volume(entry, source, named_volumes):
            _append_once(mounts, source)
            continue
        if host_mount := _host_mount_label(source, stack_dir):
            _append_once(host_mounts, host_mount)
    return tuple(mounts), tuple(host_mounts)


def _volume_source(entry: Any) -> str | None:
    if isinstance(entry, Mapping):
        source = entry.get("source")
        return str(source) if source is not None else None
    text = str(entry)
    return text.split(":", 1)[0] if ":" in text else None


def _is_named_volume(entry: Any, source: str, named_volumes: frozenset[str]) -> bool:
    if source in named_volumes:
        return True
    return isinstance(entry, Mapping) and entry.get("type") == "volume"


def _host_mount_label(source: str, stack_dir: str) -> str | None:
    source = source.strip()
    if not source:
        return None
    if "$" in source:
        return source
    if source.startswith("~"):
        return posixpath.expanduser(source)
    if posixpath.isabs(source):
        return posixpath.normpath(source)

    absolute_path = posixpath.normpath(posixpath.join(stack_dir, source))
    normalized_stack_dir = posixpath.normpath(stack_dir)
    if absolute_path == normalized_stack_dir or absolute_path.startswith(
        f"{normalized_stack_dir}/"
    ):
        return None
    return absolute_path


def _append_once(items: list[str], value: str) -> None:
    if value not in items:
        items.append(value)

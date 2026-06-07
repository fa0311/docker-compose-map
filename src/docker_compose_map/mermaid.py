from __future__ import annotations

import re

from docker_compose_map.domain import Direction, GraphName, Stack

ID_RE = re.compile(r"[^A-Za-z0-9]")


def render_graphs(stacks: tuple[Stack, ...], direction: Direction) -> dict[GraphName, str]:
    return {
        GraphName.map: render_unified(stacks, direction),
        GraphName.network: render_network(stacks, direction),
        GraphName.volumes: render_volume(stacks, direction),
        GraphName.dependencies: render_compose_deps(stacks, direction),
    }


def mid(*parts: str) -> str:
    return ID_RE.sub("_", "__".join(parts))


def esc(text: str) -> str:
    return text.replace('"', "&quot;")


def shared_networks(
    stacks: tuple[Stack, ...],
) -> tuple[dict[str, list[tuple[str, str]]], dict[str, str | None]]:
    owners: dict[str, set[str]] = {}
    members: dict[str, list[tuple[str, str]]] = {}
    for stack in stacks:
        for network in stack.networks.values():
            if network.global_name != "default" and not network.external:
                owners.setdefault(network.global_name, set()).add(stack.uid)
    for stack in stacks:
        for service in stack.services.values():
            for alias in service.networks:
                global_name = (
                    stack.networks[alias].global_name if alias in stack.networks else alias
                )
                if global_name == "default":
                    continue
                members.setdefault(global_name, []).append((stack.uid, service.name))
    shared = {
        global_name: service_refs
        for global_name, service_refs in members.items()
        if len({uid for uid, _ in service_refs}) > 1
    }
    net_owner = {
        global_name: sorted(owners[global_name])[0] if owners.get(global_name) else None
        for global_name in shared
    }
    return shared, net_owner


def render_unified(stacks: tuple[Stack, ...], direction: Direction) -> str:
    lines = [f"graph {direction.value}"]
    outside = "outside"
    lines.append(f'  {outside}(("🌐 External<br/>Internet / LAN"))')

    shared, net_owner = shared_networks(stacks)

    for stack in sorted(stacks, key=lambda candidate: candidate.name):
        mounted = {mount for service in stack.services.values() for mount in service.mounts}
        lines.append(f'  subgraph {mid("g", stack.uid)}["{esc(stack.name)}"]')
        for service in stack.services.values():
            lines.append(f'    {mid("v", stack.uid, service.name)}["{esc(service.name)}"]')
        for volume in sorted(mounted):
            lines.append(f'    {mid("vol", stack.uid, volume)}[("💾 {esc(volume)}")]')
        for global_name in sorted(shared):
            if net_owner[global_name] == stack.uid:
                lines.append(f'    {mid("n", global_name)}{{{{"🔗 {esc(global_name)}"}}}}')
        lines.append("  end")

    for global_name in sorted(shared):
        if net_owner[global_name] is None:
            lines.append(f'  {mid("n", global_name)}{{{{"🔗 {esc(global_name)}"}}}}')

    host_paths = sorted(
        {
            host_mount
            for stack in stacks
            for service in stack.services.values()
            for host_mount in service.host_mounts
        }
    )
    for host_path in host_paths:
        lines.append(f'  {mid("host", host_path)}[/"📁 {esc(host_path)}"/]')

    lines.append("")
    for stack in stacks:
        for service in stack.services.values():
            service_id = mid("v", stack.uid, service.name)
            for dependency in service.depends_on:
                if dependency in stack.services:
                    lines.append(
                        f"  {service_id} -->|depends on| {mid('v', stack.uid, dependency)}"
                    )
            if service.netns_target and service.netns_target in stack.services:
                lines.append(
                    f"  {service_id} -.->|shares netns| {mid('v', stack.uid, service.netns_target)}"
                )
            for volume in service.mounts:
                lines.append(f"  {mid('vol', stack.uid, volume)} -.-> {service_id}")
            for host_path in service.host_mounts:
                lines.append(f"  {mid('host', host_path)} -.-> {service_id}")

    _append_shared_network_edges(lines, shared)
    _append_ports(lines, stacks, outside)
    _append_unified_styles(lines, stacks, shared, host_paths, outside)
    return "\n".join(lines)


def render_network(stacks: tuple[Stack, ...], direction: Direction) -> str:
    shared, net_owner = shared_networks(stacks)
    scoped = _network_scoped_services(stacks, shared)

    lines = [f"graph {direction.value}"]
    outside = "outside"
    lines.append(f'  {outside}(("🌐 External<br/>Internet / LAN"))')

    for stack in sorted(stacks, key=lambda candidate: candidate.name):
        owns_here = [
            global_name for global_name in sorted(shared) if net_owner[global_name] == stack.uid
        ]
        if not scoped[stack.uid] and not owns_here:
            continue
        lines.append(f'  subgraph {mid("g", stack.uid)}["{esc(stack.name)}"]')
        for service in stack.services.values():
            if service.name in scoped[stack.uid]:
                lines.append(f'    {mid("v", stack.uid, service.name)}["{esc(service.name)}"]')
        for global_name in owns_here:
            lines.append(f'    {mid("n", global_name)}{{{{"🔗 {esc(global_name)}"}}}}')
        lines.append("  end")

    for global_name in sorted(shared):
        if net_owner[global_name] is None:
            lines.append(f'  {mid("n", global_name)}{{{{"🔗 {esc(global_name)}"}}}}')

    lines.append("")
    for stack in stacks:
        for service in stack.services.values():
            if service.netns_target and service.netns_target in stack.services:
                lines.append(
                    f"  {mid('v', stack.uid, service.name)} -.->|shares netns| "
                    f"{mid('v', stack.uid, service.netns_target)}"
                )

    _append_shared_network_edges(lines, shared)
    _append_ports(lines, stacks, outside)

    lines.append("")
    lines.append("  classDef net fill:#fef3c7,stroke:#d97706,color:#7c2d12;")
    lines.append("  classDef out fill:#dcfce7,stroke:#16a34a,color:#14532d;")
    lines.append(f"  class {outside} out;")
    if shared:
        lines.append(
            "  class " + ",".join(mid("n", global_name) for global_name in sorted(shared)) + " net;"
        )
    return "\n".join(lines)


def render_volume(stacks: tuple[Stack, ...], direction: Direction) -> str:
    lines = [f"graph {direction.value}"]
    host_paths = sorted(
        {
            host_mount
            for stack in stacks
            for service in stack.services.values()
            for host_mount in service.host_mounts
        }
    )

    for stack in sorted(stacks, key=lambda candidate: candidate.name):
        mounted = sorted({mount for service in stack.services.values() for mount in service.mounts})
        scoped = {
            service.name
            for service in stack.services.values()
            if service.mounts or service.host_mounts
        }
        if not scoped:
            continue
        lines.append(f'  subgraph {mid("g", stack.uid)}["{esc(stack.name)}"]')
        for service in stack.services.values():
            if service.name in scoped:
                lines.append(f'    {mid("v", stack.uid, service.name)}["{esc(service.name)}"]')
        for volume in mounted:
            lines.append(f'    {mid("vol", stack.uid, volume)}[("💾 {esc(volume)}")]')
        lines.append("  end")

    for host_path in host_paths:
        lines.append(f'  {mid("host", host_path)}[/"📁 {esc(host_path)}"/]')

    lines.append("")
    for stack in stacks:
        for service in stack.services.values():
            service_id = mid("v", stack.uid, service.name)
            for volume in service.mounts:
                lines.append(f"  {mid('vol', stack.uid, volume)} -.-> {service_id}")
            for host_path in service.host_mounts:
                lines.append(f"  {mid('host', host_path)} -.-> {service_id}")

    lines.append("")
    lines.append("  classDef vol fill:#e0e7ff,stroke:#4f46e5,color:#312e81;")
    lines.append("  classDef host fill:#fae8ff,stroke:#a21caf,color:#701a75;")
    volumes = [
        mid("vol", stack.uid, volume)
        for stack in stacks
        for volume in sorted(
            {mount for service in stack.services.values() for mount in service.mounts}
        )
    ]
    if volumes:
        lines.append("  class " + ",".join(volumes) + " vol;")
    if host_paths:
        lines.append(
            "  class " + ",".join(mid("host", host_path) for host_path in host_paths) + " host;"
        )
    return "\n".join(lines)


def render_compose_deps(stacks: tuple[Stack, ...], direction: Direction) -> str:
    owners: dict[str, set[str]] = {}
    consumers: dict[str, set[str]] = {}
    for stack in stacks:
        for network in stack.networks.values():
            if network.global_name == "default":
                continue
            target = consumers if network.external else owners
            target.setdefault(network.global_name, set()).add(stack.uid)

    name_by_uid = {stack.uid: stack.name for stack in stacks}
    pair_networks: dict[tuple[str, str], set[str]] = {}
    orphan_networks: dict[str, set[str]] = {}
    for global_name, consumer_uids in consumers.items():
        creator_uids = owners.get(global_name, set())
        for consumer_uid in consumer_uids:
            real_creators = {
                creator_uid for creator_uid in creator_uids if creator_uid != consumer_uid
            }
            if real_creators:
                for creator_uid in real_creators:
                    pair_networks.setdefault((consumer_uid, creator_uid), set()).add(global_name)
            else:
                orphan_networks.setdefault(consumer_uid, set()).add(global_name)

    ported_services = [
        (stack, service)
        for stack in stacks
        for service in stack.services.values()
        if service.ports
    ]

    lines = [f"graph {direction.value}"]
    if not pair_networks and not orphan_networks and not ported_services:
        lines.append('  none["(no cross-stack network dependencies)"]')
        return "\n".join(lines)

    outside = "outside"
    if ported_services:
        lines.append(f'  {outside}(("🌐 External<br/>Internet / LAN"))')

    involved = {uid for pair in pair_networks for uid in pair} | set(orphan_networks)
    for uid in sorted(involved):
        lines.append(f'  {mid("c", uid)}["{esc(name_by_uid[uid])}"]')

    orphan_global_names = sorted({name for names in orphan_networks.values() for name in names})
    for global_name in orphan_global_names:
        lines.append(f'  {mid("n", global_name)}{{{{"🔗 {esc(global_name)}<br/>(no creator)"}}}}')

    for stack, service in ported_services:
        lines.append(f'  {mid("v", stack.uid, service.name)}["{esc(service.name)}"]')

    lines.append("")
    for (consumer_uid, creator_uid), network_names in sorted(pair_networks.items()):
        label = esc(", ".join(sorted(network_names)))
        lines.append(f'  {mid("c", consumer_uid)} -->|"{label}"| {mid("c", creator_uid)}')
    for consumer_uid, network_names in sorted(orphan_networks.items()):
        for global_name in sorted(network_names):
            lines.append(
                f'  {mid("c", consumer_uid)} -->|"{esc(global_name)}"| {mid("n", global_name)}'
            )

    if ported_services:
        _append_ports(lines, stacks, outside)

    lines.append("")
    lines.append("  classDef net fill:#fef3c7,stroke:#d97706,color:#7c2d12;")
    lines.append("  classDef out fill:#dcfce7,stroke:#16a34a,color:#14532d;")
    if ported_services:
        lines.append(f"  class {outside} out;")
    if orphan_global_names:
        lines.append(
            "  class "
            + ",".join(mid("n", global_name) for global_name in orphan_global_names)
            + " net;"
        )
    return "\n".join(lines)


def _network_scoped_services(
    stacks: tuple[Stack, ...],
    shared: dict[str, list[tuple[str, str]]],
) -> dict[str, set[str]]:
    scoped: dict[str, set[str]] = {}
    for stack in stacks:
        services: set[str] = set()
        for service in stack.services.values():
            on_shared = any(
                (stack.networks[alias].global_name if alias in stack.networks else alias) in shared
                for alias in service.networks
            )
            if service.ports or on_shared or service.netns_target:
                services.add(service.name)
                if service.netns_target and service.netns_target in stack.services:
                    services.add(service.netns_target)
        scoped[stack.uid] = services
    return scoped


def _append_shared_network_edges(
    lines: list[str],
    shared: dict[str, list[tuple[str, str]]],
) -> None:
    if not shared:
        return
    lines.append("")
    for global_name in sorted(shared):
        network_id = mid("n", global_name)
        for uid, service_name in sorted(shared[global_name]):
            lines.append(f"  {mid('v', uid, service_name)} --> {network_id}")


def _append_ports(lines: list[str], stacks: tuple[Stack, ...], outside: str) -> None:
    lines.append("")
    for stack in stacks:
        for service in stack.services.values():
            if service.ports:
                ports = "/".join(f":{port}" for port in service.ports)
                lines.append(
                    f'  {outside} -->|"publishes {ports}"| {mid("v", stack.uid, service.name)}'
                )


def _append_unified_styles(
    lines: list[str],
    stacks: tuple[Stack, ...],
    shared: dict[str, list[tuple[str, str]]],
    host_paths: list[str],
    outside: str,
) -> None:
    lines.append("")
    lines.append("  classDef net fill:#fef3c7,stroke:#d97706,color:#7c2d12;")
    lines.append("  classDef out fill:#dcfce7,stroke:#16a34a,color:#14532d;")
    lines.append("  classDef vol fill:#e0e7ff,stroke:#4f46e5,color:#312e81;")
    lines.append("  classDef host fill:#fae8ff,stroke:#a21caf,color:#701a75;")
    lines.append(f"  class {outside} out;")
    if shared:
        lines.append(
            "  class " + ",".join(mid("n", global_name) for global_name in sorted(shared)) + " net;"
        )
    volumes = [
        mid("vol", stack.uid, volume)
        for stack in stacks
        for volume in sorted(
            {mount for service in stack.services.values() for mount in service.mounts}
        )
    ]
    if volumes:
        lines.append("  class " + ",".join(volumes) + " vol;")
    if host_paths:
        lines.append(
            "  class " + ",".join(mid("host", host_path) for host_path in host_paths) + " host;"
        )

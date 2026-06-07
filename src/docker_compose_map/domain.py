from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class Direction(StrEnum):
    LR = "LR"
    TD = "TD"
    TB = "TB"
    RL = "RL"
    BT = "BT"


class GraphName(StrEnum):
    map = "map"
    network = "network"
    volumes = "volumes"
    dependencies = "dependencies"


class Service(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str
    depends_on: tuple[str, ...] = ()
    netns_target: str | None = None
    networks: tuple[str, ...] = ()
    ports: tuple[str, ...] = ()
    mounts: tuple[str, ...] = ()
    host_mounts: tuple[str, ...] = ()


class Network(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    alias: str
    external: bool
    global_name: str


class Stack(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str
    uid: str
    rel_dir: str
    services: dict[str, Service] = Field(default_factory=dict)
    networks: dict[str, Network] = Field(default_factory=dict)
    volumes: frozenset[str] = frozenset()

    def owns(self, global_name: str) -> bool:
        return any(
            network.global_name == global_name and not network.external
            for network in self.networks.values()
        )

    def joins(self, global_name: str) -> bool:
        return any(network.global_name == global_name for network in self.networks.values())

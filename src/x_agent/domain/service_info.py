from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ServiceInfo:
    name: str
    version: str
    responsibilities: tuple[str, ...]
    layers: tuple[str, ...]

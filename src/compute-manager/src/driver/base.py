from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, Any, Optional
from datetime import datetime
from enum import Enum, auto
from typing import Dict

class ContainerStatus(str, Enum):
    STARTING  = "STARTING"
    RUNNING   = "RUNNING"
    COMPLETED = "COMPLETED"
    STOPPED   = "STOPPED"
    CRASHED   = "CRASHED"
    FAILED    = "FAILED"

@dataclass
class ConnectionInfo:
    ip: str
    transport: str
    signature_scheme: str
    key: str
    shell_port: int
    iopub_port: int
    stdin_port: int
    control_port: int
    hb_port: int

@dataclass
class ContainerContext:
    id: str
    caller: str
    created_at: datetime
    status: ContainerStatus
    status_msg: Optional[str] = None
    client_connection_info: Optional[ConnectionInfo] = None

@dataclass
class DriverStatus:
    num_running_containers: int

class Driver(ABC):
    worker_image: str
    mounts: Dict[str, str]

    def __init__(self, config: Dict):
        self.worker_image = config["image"]
        self.mounts = config.get("mounts", {})

    @abstractmethod
    async def can_allocate_container(self, ctx: ContainerContext) -> bool:
        """Determines whether container can be launched for requested context."""
        pass

    @abstractmethod
    async def launch_container(self, ctx: ContainerContext) -> None:
        """Attempt to launch the container. Return True if successful, False otherwise."""
        pass

    @abstractmethod
    async def stop_container(self, id: str) -> None:
        """Stop and remove a container."""
        pass

    @abstractmethod
    async def get_container(self, id: str) -> ContainerContext:
        """Gets a container."""
        pass

    @abstractmethod
    async def get_status(self) -> DriverStatus:
        """Gets status of driver."""
        pass

class ContainerNotFoundError(Exception): ...
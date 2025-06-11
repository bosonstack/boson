import asyncio
import docker
from docker.models.containers import Container
from docker.errors import NotFound, APIError
from typing import Dict
import os
from typing import Tuple, Optional
import logging
import tarfile
import io
import secrets, base64
import json
import random
from dataclasses import asdict
from copy import copy

from src.driver.base import Driver, ContainerContext, ContainerStatus, DriverStatus, ContainerNotFoundError, ConnectionInfo

SIGTERM_EXIT = 143
SIGKILL_EXIT = 137

class LocalDriver(Driver):
    def __init__(self, config: dict):
        super().__init__(config)
        self._docker: docker.DockerClient = docker.from_env()

        self._containers: Dict[str, Tuple[ContainerContext, Optional[Container]]] = {}
        self._watch_tasks: Dict[str, asyncio.Task] = {}

    async def launch_container(self, ctx: ContainerContext) -> None:
        """Start a container and begin watching it for unexpected exits."""
        try:
            self._containers[ctx.id] = (ctx, None)

            network_name = self._get_network_name()
            project_name = self._get_compose_project_name()

            ports = random.sample(range(49152, 65535), 5)

            # Couldn't get key to work #TODO: Fix key
            key_bytes = secrets.token_bytes(32)
            key_str = base64.b64encode(key_bytes).decode()

            # Generate connection spec
            connection_info = ConnectionInfo(
                ip="0.0.0.0",  # ipykernel listens on all interfaces
                transport="tcp",
                signature_scheme="hmac-sha256",
                key=key_str,
                shell_port=ports[0],
                iopub_port=ports[1],
                stdin_port=ports[2],
                control_port=ports[3],
                hb_port=ports[4],
            )

            # Serialize the connection file
            connection_file_data = json.dumps(asdict(connection_info)).encode()

            # Create a tarball in memory to copy into container
            tarstream = io.BytesIO()
            with tarfile.open(fileobj=tarstream, mode='w') as tar:
                tarinfo = tarfile.TarInfo(name="connection.json")
                tarinfo.size = len(connection_file_data)
                tar.addfile(tarinfo, io.BytesIO(connection_file_data))
            tarstream.seek(0)

            # Create mount configuration
            volumes_dict = {}
            for name, host_path in self.mounts.items():
                container_path = f"/mnt/{name}"
                volumes_dict[host_path] = {"bind": container_path, "mode": "ro"}

            # Launch the container (do NOT start ipykernel yet)
            container = await asyncio.to_thread(
                self._docker.containers.run,
                image=self.worker_image,
                name=f"flint__{project_name}__worker__{ctx.id}",
                detach=True,
                auto_remove=True,
                network=network_name,
                labels={"flint.ephemeral": "true"},
                environment={
                    "FLINT_CONTROL_PLANE_ENDPOINT": "http://reverse-proxy",
                    "STORAGE_USER": os.environ.get("STORAGE_USER"),
                    "STORAGE_PASSWORD": os.environ.get("STORAGE_PASSWORD")
                },
                command=["sh", "-c", "poetry run python /root/watchdog.py >> /tmp/watchdog.log 2>&1"],
                tty=True,
                stdin_open=True,
                volumes=volumes_dict,
            )

            # Copy connection.json into container
            await asyncio.to_thread(container.put_archive, "/tmp", tarstream.read())

            # Run ipykernel inside the container
            run_kernel_cmd = [
                "poetry", "run", "python", "-m", "ipykernel_launcher", "-f", "/tmp/connection.json"
            ]
            await asyncio.to_thread(container.exec_run, run_kernel_cmd, detach=True)

            # Update container context
            await asyncio.to_thread(container.reload)
            network_info = container.attrs["NetworkSettings"]["Networks"][network_name]
            container_ip = network_info["IPAddress"]
            client_connection_info = copy(connection_info)
            client_connection_info.ip = container_ip
            ctx.client_connection_info = client_connection_info
            ctx.status = ContainerStatus.RUNNING

            self._containers[ctx.id] = (ctx, container)

            # Watchdog
            task = asyncio.create_task(self._watch_container_exit(container, ctx))
            self._watch_tasks[ctx.id] = task
            task.add_done_callback(lambda _: self._watch_tasks.pop(ctx.id, None))

        except Exception as e:
            logging.error(f"Failed to launch container {ctx.id}: {e}", exc_info=True)
            ctx.status = ContainerStatus.FAILED
            ctx.status_msg = e

    async def stop_container(self, id: str) -> None:
        """Gracefully stop the container that belongs to *ctx*."""
        try:
            _, container = self._containers.get(id)
        except:
            raise ContainerNotFoundError()

        try:
            await asyncio.to_thread(container.stop, timeout=10)
        except APIError as e:
            # Container might have exited by itself in the meantime
            if "is not running" not in str(e).lower():
                return
            
    async def can_allocate_container(self, ctx: ContainerContext) -> bool:
        """Determines whether container can be launched per requested `ctx`."""
        return True
    
    async def get_container(self, id: str) -> ContainerContext:
        """Gets a container."""
        try:
            ctx, container = self._containers.get(id)
        except:
            raise ContainerNotFoundError()
        
        return ctx
    
    async def get_status(self) -> DriverStatus:
        """Gets a container."""
        running_containers = [ctx for ctx, _ in self._containers.values() if ctx.status == ContainerStatus.RUNNING]

        return DriverStatus(
            num_running_containers=len(running_containers)
        )
    
    def _tar_authorized_keys(self, public_key_path: str) -> bytes:
        data = io.BytesIO()
        with tarfile.open(fileobj=data, mode="w") as tar:
            tar.add(public_key_path, arcname="authorized_keys")
        data.seek(0)
        return data.read()

    async def _handle_container_exit(self, ctx: ContainerContext) -> None:
        ...

    async def _watch_container_exit(
        self, 
        container: Container, 
        ctx: ContainerContext
    ) -> None:
        """Block until *container* is no longer running.

        Exit may be caused by completion, stop instruction or failure.
        """
        logging.info(f"Watching container, {ctx.id}, for exit.")
        
        try:
            # Wait for container to leave "running" state
            result = await asyncio.to_thread(container.wait)
            code = result.get("StatusCode", -1)
        except APIError as e:
            # Daemon unreachable => crash
            code = 1

        logging.info(f"Container, {ctx.id}, exited with code {code} and result:\n{result}.")
        
        if code == 0:
            ctx.status = ContainerStatus.COMPLETED
        elif code in (SIGTERM_EXIT, SIGKILL_EXIT):
            ctx.status = ContainerStatus.STOPPED
        else:
            ctx.status = ContainerStatus.CRASHED

        await self._handle_container_exit(ctx)

    def _get_compose_project_name(self) -> Optional[str]:
        """Attempts to get the current Compose project name via the container label."""
        this_id = os.uname()[1]  # Hostname = container ID inside the container
        container = self._docker.containers.get(this_id)
        return container.labels.get("com.docker.compose.project")
    
    def _get_network_name(self) -> str:
        """
        Returns the name of the Docker network this container is in.
        """
        container_id = os.uname().nodename
        container = self._docker.containers.get(container_id)
        networks = container.attrs["NetworkSettings"]["Networks"]
        return next(iter(networks))
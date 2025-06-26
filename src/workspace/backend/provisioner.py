from jupyter_client.provisioning.provisioner_base import KernelProvisionerBase
import requests
import time
import logging
import asyncio
import signal

class DeliberateException(Exception):
    ...

class RemoteContainerProvisioner(KernelProvisionerBase):
    def __init__(self, **kwargs):
        logging.info("Instantiating provisioner")
        super().__init__(**kwargs)
        self.container_id = None
        self._container_attached = False

    async def pre_launch(self, **kwargs):
        if not self._container_attached:
            # Allocate container
            resp = requests.post("http://compute-manager:8000/allocate", json={
                "caller": "jupyterlab"
            })
            resp.raise_for_status()
            self.container_id = resp.json()["container_id"]

            # Poll until container is ready
            while True:
                await asyncio.sleep(1)
                info = requests.get(f"http://compute-manager:8000/container/{self.container_id}").json()
                ctx = info["container_context"]
                if ctx["status"] == "RUNNING":
                    break

            self._container_attached = True

        connection_info = ctx["client_connection_info"]

        self.parent.ip = connection_info["ip"]
        self.parent.transport = connection_info["transport"]
        self.parent.signature_scheme = connection_info["signature_scheme"]
        self.parent.session.key = connection_info["key"].encode("utf-8")

        self.parent.shell_port = connection_info["shell_port"]
        self.parent.iopub_port = connection_info["iopub_port"]
        self.parent.stdin_port = connection_info["stdin_port"]
        self.parent.control_port = connection_info["control_port"]
        self.parent.hb_port = connection_info["hb_port"]

        self.parent.write_connection_file()
        self.connection_info = self.parent.get_connection_info()

        return await super().pre_launch(cmd={}, **kwargs)

    async def launch_kernel(self, cmd: list[str], **kwargs):
        # (Optional) Notify container to start listening
        return self.connection_info

    async def cleanup(self, restart=False):
        requests.delete(f"http://compute-manager:8000/container/{self.container_id}")
        self._container_attached = False

    async def kill(self, restart=False):
        await self.cleanup(restart=restart)

    async def terminate(self, restart=False):
        await self.cleanup(restart=restart)

    async def poll(self):
        r = requests.get(f"http://compute-manager:8000/container/{self.container_id}")
        status = r.json()["container_context"]["status"]

        if status == "COMPLETED" or status == "STOPPED":
            return 0
        
        if status == "RUNNING":
            return
        
        return 1

    async def wait(self):
        while True:
            status = await self.poll()
            if status != 0:
                break
            await asyncio.sleep(2)
        return 0

    async def send_signal(self, signum):
        if signum in (signal.SIGTERM, signal.SIGKILL, signal.SIGINT):
            logging.info("Sending graceful shutdown request to container.")
            await self.cleanup(restart=False)

    @property
    def has_process(self) -> bool:
        return self._container_attached
    

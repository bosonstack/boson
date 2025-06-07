from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from uuid import uuid4
from datetime import datetime
import yaml
import asyncio
import logging
from dataclasses import asdict

from src.driver.base import ContainerStatus, ContainerContext, Driver, DriverStatus, ContainerNotFoundError
from src.driver.local import LocalDriver

# --- Initialise ---

app = FastAPI()

# --- Load worker config ---
with open("/app/worker/worker.yaml", "r") as f:
    config = yaml.safe_load(f)

driver_configs = config["driver"]

# --- Load Driver ---
logging.info("Instantiating driver...")
match driver_configs["type"]:
    case "local":
        driver = LocalDriver(driver_configs)
    case  _:
        raise ValueError(f"Driver type, {driver_configs['type']}, could not be loaded.")
    
driver: Driver

# --- HTTP Models ---
class AllocationRequest(BaseModel):
    caller: str
    
class AllocationResponse(BaseModel):
    container_id: str
    message: str = "Starting container..."

class ContainerResponse(BaseModel):
    container_id: str
    status: ContainerStatus
    container_context: ContainerContext

class SystemStatusResponse(BaseModel):
    driver_status: DriverStatus

# --- Endpoints ---
@app.post("/allocate", response_model=AllocationResponse, status_code=202)
async def allocate(req: AllocationRequest):
    logging.info(f"Allocating container for request:\n{req}")

    container_id = str(uuid4())
    container_context = ContainerContext(
        id=container_id,
        caller=req.caller,
        created_at=datetime.utcnow(),
        status=ContainerStatus.STARTING
    )

    if not await driver.can_allocate_container(container_context):
        raise HTTPException(
            status_code=403,
            detail="Could not allocate container."
        )

    asyncio.create_task(driver.launch_container(container_context))

    return AllocationResponse(
        container_id=container_id
    )

@app.get("/container/{container_id}", response_model=ContainerResponse)
async def get_container(container_id: str):
    logging.info(f"Getting container details for id '{container_id}'")

    try:
        container_context = await driver.get_container(container_id)
    except ContainerNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail=f"Container with id, {container_id}, could not be found."
        )

    return ContainerResponse(
        container_id=container_id,
        status=container_context.status,
        container_context=container_context
    )
    
@app.delete("/container/{container_id}", status_code=202)
async def terminate(container_id: str):
    logging.info(f"Terminating container with id '{container_id}'")

    async def _stop():
        try:
            await driver.stop_container(container_id)
        except ContainerNotFoundError:
            raise HTTPException(
                status_code=404,
                detail=f"Container with id, {container_id}, could not be found."
            )

    asyncio.create_task(_stop())

@app.get("/status", response_model=SystemStatusResponse)
async def get_status():
    logging.info(f"Getting Compute Manager Status.")

    status = await driver.get_status()

    return SystemStatusResponse(
        driver_status=status
    )
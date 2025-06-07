import time
import requests
import os
import signal
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

FLINT_CONTROL_PLANE_ENDPOINT = os.getenv("FLINT_CONTROL_PLANE_ENDPOINT")
CHECK_INTERVAL_SECONDS = 10

def is_control_plane_alive():
    try:
        r = requests.get(f"{FLINT_CONTROL_PLANE_ENDPOINT}/compute-manager/status", timeout=5)
        alive = r.status_code == 200
        if not alive:
            logging.warning(f"Received status code {r.status_code}")
        return alive
    except Exception as e:
        logging.warning(f"Failed to contact control plane: {e}")
        return False

def shutdown():
    logging.error("Control plane unreachable. Shutting down container.")
    sys.exit(1)

if __name__ == "__main__":
    logging.info("Starting watchdog...")
    while True:
        if not is_control_plane_alive():
            shutdown()
        time.sleep(CHECK_INTERVAL_SECONDS)

# Copyright 2022-2023 XProbe Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import asyncio
import logging
import multiprocessing
import signal
import sys
from typing import Dict, Optional

import pytest
import xoscar as xo

from xinference.core.supervisor import SupervisorActor
from xinference.deploy.utils import create_worker_actor_pool
from xinference.deploy.worker import start_worker_components

TEST_LOGGING_CONF = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "formatter": {
            "format": "%(asctime)s %(name)-12s %(process)d %(levelname)-8s %(message)s",
        },
    },
    "handlers": {
        "stream_handler": {
            "class": "logging.StreamHandler",
            "formatter": "formatter",
            "level": "DEBUG",
            "stream": "ext://sys.stderr",
        },
    },
    "root": {
        "level": "DEBUG",
        "handlers": ["stream_handler"],
    },
}


def api_health_check(endpoint: str, max_attempts: int, sleep_interval: int = 3):
    import time

    import requests

    attempts = 0
    while attempts < max_attempts:
        time.sleep(sleep_interval)
        try:
            response = requests.get(f"{endpoint}/status")
            if response.status_code == 200:
                return True
        except requests.RequestException as e:
            print(f"Error while checking endpoint: {e}")

        attempts += 1
        if attempts < max_attempts:
            print(
                f"Endpoint not available, will try {max_attempts - attempts} more times"
            )

    return False


async def _start_test_cluster(
    address: str,
    logging_conf: Optional[Dict] = None,
):
    logging.config.dictConfig(logging_conf)  # type: ignore

    pool = None
    try:
        pool = await create_worker_actor_pool(
            address=f"test://{address}", logging_conf=logging_conf
        )
        await xo.create_actor(
            SupervisorActor, address=address, uid=SupervisorActor.uid()
        )
        await start_worker_components(
            address=address, supervisor_address=address, main_pool=pool
        )
        await pool.join()
    except asyncio.CancelledError:
        if pool is not None:
            await pool.stop()


def run_test_cluster(address: str, logging_conf: Optional[Dict] = None):
    def sigterm_handler(signum, frame):
        sys.exit(0)

    signal.signal(signal.SIGTERM, sigterm_handler)

    loop = asyncio.get_event_loop()
    task = loop.create_task(
        _start_test_cluster(address=address, logging_conf=logging_conf)
    )
    loop.run_until_complete(task)


def run_test_cluster_in_subprocess(
    address: str, logging_conf: Optional[Dict] = None
) -> multiprocessing.Process:
    # prevent re-init cuda error.
    multiprocessing.set_start_method(method="spawn", force=True)

    p = multiprocessing.Process(target=run_test_cluster, args=(address, logging_conf))
    p.start()
    return p


@pytest.fixture
def setup():
    from .api.restful_api import run_in_subprocess as run_restful_api
    from .deploy.utils import health_check as cluster_health_check

    logging.config.dictConfig(TEST_LOGGING_CONF)  # type: ignore

    supervisor_addr = f"localhost:{xo.utils.get_next_port()}"
    local_cluster_proc = run_test_cluster_in_subprocess(
        supervisor_addr, TEST_LOGGING_CONF
    )
    if not cluster_health_check(supervisor_addr, max_attempts=3, sleep_interval=3):
        raise RuntimeError("Cluster is not available after multiple attempts")

    port = xo.utils.get_next_port()
    restful_api_proc = run_restful_api(
        supervisor_addr,
        host="localhost",
        port=port,
        logging_conf=TEST_LOGGING_CONF,
    )
    endpoint = f"http://localhost:{port}"
    if not api_health_check(endpoint, max_attempts=3, sleep_interval=5):
        raise RuntimeError("Endpoint is not available after multiple attempts")

    yield f"http://localhost:{port}", supervisor_addr

    local_cluster_proc.terminate()
    restful_api_proc.terminate()

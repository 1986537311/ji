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

import xoscar as xo

from ..actor.service import WorkerActor


async def start_worker_components(address: str, controller_address: str):
    await xo.create_actor(
        WorkerActor,
        address=address,
        uid=WorkerActor.uid(),
        controller_address=controller_address,
    )
    # TODO: start resource actor


async def _start_worker(address: str, controller_address: str):
    from .utils import create_actor_pool

    pool = await create_actor_pool(address=address, n_process=0)
    await start_worker_components(address=address, controller_address=controller_address)
    await pool.join()


def main(address: str, controller_address: str):
    loop = asyncio.get_event_loop()
    task = loop.create_task(_start_worker(address, controller_address))

    try:
        loop.run_until_complete(task)
    except KeyboardInterrupt:
        task.cancel()
        loop.run_until_complete(task)
        # avoid displaying exception-unhandled warnings
        task.exception()

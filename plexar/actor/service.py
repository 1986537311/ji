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

from logging import getLogger
from typing import Dict, List, Optional

import xoscar as xo

from plexar.actor import ModelActor

logger = getLogger(__name__)


class ControllerActor(xo.Actor):
    def __init__(self):
        super().__init__()
        self._workers: List[xo.ActorRefType[WorkerActor]] = []
        self._model_uid_to_worker: Dict[str, xo.ActorRefType[WorkerActor]] = {}

    @classmethod
    def uid(cls) -> str:
        return "plexar_controller"

    async def _choose_worker(self) -> xo.ActorRefType["WorkerActor"]:
        # TODO: better allocation strategy.
        min_running_model_count = None
        target_worker = None
        for worker in self._workers:
            running_model_count = await worker.get_model_count()
            if (
                min_running_model_count is None
                or running_model_count < min_running_model_count
            ):
                min_running_model_count = running_model_count
                target_worker = worker

            return target_worker

        raise RuntimeError("TODO")

    async def launch_builtin_model(
        self,
        model_uid: str,
        model_name: str,
        n_parameters_in_billions: Optional[int],
        fmt: Optional[str],
        quantization: Optional[str],
        **kwargs
    ) -> xo.ActorRefType["ModelActor"]:
        assert model_uid not in self._model_uid_to_worker

        worker_ref = await self._choose_worker()
        model_ref = await worker_ref.launch_builtin_model(
            model_uid=model_uid,
            model_name=model_name,
            n_parameters_in_billions=n_parameters_in_billions,
            fmt=fmt,
            quantization=quantization,
            **kwargs
        )
        self._model_uid_to_worker[model_uid] = worker_ref

        return model_ref

    async def terminate_model(self, model_uid: str):
        assert model_uid in self._model_uid_to_worker

        worker_ref = self._model_uid_to_worker[model_uid]
        await worker_ref.terminate_model(model_uid=model_uid)
        del self._model_uid_to_worker[model_uid]

    async def get_model(self, model_uid: str):
        assert model_uid in self._model_uid_to_worker

        worker_ref = self._model_uid_to_worker[model_uid]
        return await worker_ref.get_model(model_uid=model_uid)

    async def list_models(self) -> List[str]:
        return list(self._model_uid_to_worker.keys())

    async def add_worker(self, worker_address: str):
        worker_ref = await xo.actor_ref(address=worker_address, uid=WorkerActor.uid())
        self._workers.append(worker_ref)


class WorkerActor(xo.Actor):
    def __init__(self, controller_address: str):
        super().__init__()
        self._controller_address = controller_address
        self._model_uid_to_model: Dict[str, xo.ActorRefType["ModelActor"]] = {}

    @classmethod
    def uid(cls) -> str:
        return "plexar_worker"

    async def __post_create__(self):
        controller_ref: xo.ActorRefType["ControllerActor"] = await xo.actor_ref(
            address=self._controller_address, uid=ControllerActor.uid()
        )
        await controller_ref.add_worker(self.address)

    async def get_model_count(self) -> int:
        return len(self._model_uid_to_model)

    async def launch_builtin_model(
        self,
        model_uid: str,
        model_name: str,
        n_parameters_in_billions: Optional[int],
        fmt: Optional[str],
        quantization: Optional[str],
        **kwargs
    ) -> xo.ActorRefType["ModelActor"]:
        assert model_uid not in self._model_uid_to_model

        from plexar.model import MODEL_SPECS

        for model_spec in MODEL_SPECS:
            if model_spec.match(
                model_name, n_parameters_in_billions, fmt, quantization
            ):
                model_cls = model_spec.cls
                assert model_cls is not None

                save_path = model_spec.cache()
                model = model_cls(save_path, kwargs)
                model_ref = await xo.create_actor(
                    ModelActor, address=self.address, uid=model_uid, model=model
                )
                self._model_uid_to_model[model_uid] = model_ref
                return model_ref

        raise ValueError("TODO")

    async def terminate_model(self, model_uid: str):
        assert model_uid in self._model_uid_to_model

        model_ref = self._model_uid_to_model[model_uid]
        await xo.destroy_actor(model_ref)
        del self._model_uid_to_model[model_uid]

    async def list_models(self) -> List[str]:
        return list(self._model_uid_to_model.keys())

    async def get_model(self, model_uid: str) -> xo.ActorRefType["ModelActor"]:
        assert model_uid in self._model_uid_to_model

        return self._model_uid_to_model[model_uid]

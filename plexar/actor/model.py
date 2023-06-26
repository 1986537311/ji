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
from typing import TYPE_CHECKING, Any, Dict, Iterator

import xoscar as xo

from .common import IteratorActor, IteratorWrapper

if TYPE_CHECKING:
    from ..model.llm.core import Model


class ModelManagerActor(xo.Actor):
    models: Dict[str, xo.ActorRef] = dict()

    def add_model(self, model_uid: str, ref: xo.ActorRef):
        self.models[model_uid] = ref

    def get_model(self, model_uid: str):
        return self.models[model_uid]


class ModelActor(xo.Actor):
    @classmethod
    def gen_uid(cls, model: "Model"):
        return f"{model.__class__}-model-actor"

    def __init__(self, model: "Model"):
        super().__init__()
        self._model = model

    async def __post_create__(self):
        self._model.load()

    async def _create_iterator_actor(self, it: Iterator) -> IteratorWrapper:
        uid = str(id(it))
        await xo.create_actor(IteratorActor, address=self.address, uid=uid, it=it)
        return IteratorWrapper(iter_actor_addr=self.address, iter_actor_uid=uid)

    async def _wrap_iterator(self, ret: Any):
        if hasattr(ret, "__iter__"):
            return await self._create_iterator_actor(iter(ret))
        else:
            return ret

    async def generate(self, prompt: str, *args, **kwargs):
        if not hasattr(self._model, "generate"):
            raise AttributeError("generate")

        return self._wrap_iterator(
            getattr(self._model, "generate")(prompt, *args, **kwargs)
        )

    async def chat(self, prompt: str, *args, **kwargs):
        if not hasattr(self._model, "chat"):
            raise AttributeError("chat")

        return self._wrap_iterator(
            getattr(self._model, "chat")(prompt, *args, **kwargs)
        )

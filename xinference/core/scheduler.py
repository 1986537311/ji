# Copyright 2022-2024 XProbe Inc.
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
from collections import deque
from typing import List

import xoscar as xo


class InferenceRequest:
    def __init__(self, prompt, future, is_prefill, *args, **kwargs):
        self._prompt = prompt
        self._full_prompt = None
        self._is_prefill = is_prefill
        self._prompt_tokens = None
        self._new_tokens = []
        self._outputs = None
        self._kv_cache = None
        self._inference_args = args
        self._inference_kwargs = kwargs
        self._stopped = False
        # self.completion_chunk = None
        # self.completion_usage = None
        self.completion = []
        self.future = future
        self._check_args()

    def _check_args(self):
        assert len(self._inference_args) == 3
        # system prompt
        assert self._inference_args[0] is None or isinstance(
            self._inference_args[0], str
        )
        # chat history
        assert self._inference_args[1] is None or isinstance(
            self._inference_args[1], list
        )
        # generate config
        assert self._inference_args[2] is None or isinstance(
            self._inference_args[2], dict
        )

    @property
    def prompt(self):
        return self._prompt

    @property
    def system_prompt(self):
        return self._inference_args[0]

    @property
    def chat_history(self):
        return self._inference_args[1]

    @property
    def full_prompt(self):
        return self._full_prompt

    @full_prompt.setter
    def full_prompt(self, value: str):
        self._full_prompt = value

    @property
    def is_prefill(self):
        return self._is_prefill

    @is_prefill.setter
    def is_prefill(self, value: bool):
        self._is_prefill = value

    @property
    def prompt_tokens(self):
        return self._prompt_tokens

    @prompt_tokens.setter
    def prompt_tokens(self, value: List[int]):
        self._prompt_tokens = value

    @property
    def kv_cache(self):
        return self._kv_cache

    @kv_cache.setter
    def kv_cache(self, value):
        self._kv_cache = value

    @property
    def new_tokens(self):
        return self._new_tokens

    def append_new_token(self, token: int):
        self._new_tokens.append(token)

    @property
    def generate_config(self):
        return self._inference_args[2]

    @property
    def stopped(self):
        return self._stopped

    @stopped.setter
    def stopped(self, value: bool):
        self._stopped = value

    @property
    def outputs(self):
        return self._outputs

    @outputs.setter
    def outputs(self, value):
        self._outputs = value

    @property
    def stream(self) -> bool:
        return (
            False
            if self.generate_config is None
            else self.generate_config.get("stream", False)
        )


class SchedulerActor(xo.StatelessActor):
    @classmethod
    def gen_uid(cls, model_uid: str, replica_id: str):
        return f"{model_uid}-{replica_id}-scheduler-actor"

    def __init__(self):
        super().__init__()
        self._waiting_queue = deque()
        self._running_queue = deque()
        self._model = None

    def set_model(self, model):
        self._model = model

    def _handle_request(self) -> List[InferenceRequest]:
        res = []
        while len(self._waiting_queue) > 0:
            res.append(self._waiting_queue.popleft())
        while len(self._running_queue) > 0:
            res.append(self._running_queue.popleft())
        return res

    async def step(self):
        req_list = self._handle_request()
        if not req_list:
            return
        self._model.batch_inference(req_list)

        # TODO: handle stopped request
        for r in req_list:
            if r.stream:
                for completion in r.completion:
                    await r.future.put(completion)

            if not r.stopped:
                self._running_queue.append(r)
            else:
                if not r.stream:
                    r.future.set_result(r.completion[0])
                else:
                    # TODO: done str
                    await r.future.put("xinference_done")

    async def add_request(self, prompt: str, future, *args, **kwargs):
        req = InferenceRequest(prompt, future, True, *args, **kwargs)
        self._waiting_queue.append(req)
        print("========Add request done!!!!")

    async def run(self):
        while True:
            await self.step()
            await asyncio.sleep(0.1)

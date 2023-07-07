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

import random
import string
from typing import Iterator, Optional

import pytest

from .. import MODEL_FAMILIES, ModelFamily, ModelSpec
from ..llm.chatglm import ChatglmCppChatModel


class MockModelFamily(ModelFamily):
    def cache(
        self,
        model_size_in_billions: Optional[int] = None,
        quantization: Optional[str] = None,
    ):
        pass


class MockPipeline:
    def __init__(self) -> None:
        pass

    def stream_chat(self, *args, **kwargs) -> Iterator[str]:
        res = [f"chatglm_test_stream_{i}" for i in range(100)]
        return iter(res)

    def chat(self, *args, **kwargs) -> str:
        res = "chatglm_test_chat"
        return res


class MockChatglmCppChatModel(ChatglmCppChatModel):
    def load(self):
        self._llm = MockPipeline()


MODEL_FAMILIES.append(
    MockModelFamily(
        model_name="mock_chatglm",
        model_sizes_in_billions=[6],
        model_format="ggmlv3",
        quantizations=[
            "q4_0",
            "q4_1",
            "q5_0",
            "q5_1",
            "q8_0",
        ],
        url_generator=lambda: "",
        cls=MockChatglmCppChatModel,
    )
)

mock_model_spec1 = ModelSpec(
    model_name="chatglm",
    model_format="ggmlv3",
    model_size_in_billions=6,
    quantization="q4_0",
    url="http://chatglm_test.url",
)

mock_model_spec2 = ModelSpec(
    model_name="chatglm2",
    model_format="ggmlv3",
    model_size_in_billions=6,
    quantization="q4_0",
    url="http://chatglm2_test.url",
)


@pytest.mark.parametrize("model_spec", [mock_model_spec1, mock_model_spec2])
def test_model_init(model_spec):
    uid = "".join(random.choice(string.digits) for i in range(100))
    path = "".join(
        random.choice(string.ascii_letters + string.punctuation) for i in range(100)
    )
    model = MockChatglmCppChatModel(uid, model_spec, path)

    assert model.model_uid == uid
    assert model._model_path == path
    assert model.model_spec == model_spec

    if model_spec.model_name == "chatglm":
        assert model.max_context_length == 2048
    elif model_spec.model_name == "chatglm2":
        assert model.max_context_length == 8192

    assert model._model_config is None
    model._model_config = model._sanitize_generate_config(None)
    assert model._model_config == {
        "max_tokens": 256,
        "temperature": 0.95,
        "top_p": 0.8,
        "stream": False,
    }


@pytest.mark.parametrize("model_spec", [mock_model_spec1, mock_model_spec2])
def test_model_pipeline(model_spec):
    model = MockChatglmCppChatModel("uid", model_spec, "path")
    assert model._llm is None

    model.load()
    assert isinstance(model._llm, MockPipeline)


@pytest.mark.parametrize("model_spec", [mock_model_spec1, mock_model_spec2])
def test_chat_stream(model_spec):
    model = MockChatglmCppChatModel("uid", model_spec, "path")
    model.load()
    responses = list(model.chat("Hello", generate_config={"stream": True}))

    assert responses[0]["choices"][0]["delta"] == {"role": "assistant"}

    for i in range(3):
        assert responses[i + 1]["choices"][0]["delta"] == {
            "content": f"chatglm_test_stream_{i}"
        }


@pytest.mark.parametrize("model_spec", [mock_model_spec1, mock_model_spec2])
def test_chat_non_stream(model_spec):
    model = MockChatglmCppChatModel("uid", model_spec, "path")
    model.load()
    response = model.chat("Hello")

    assert response["choices"][0]["message"] == {
        "role": "assistant",
        "content": "chatglm_test_chat",
    }

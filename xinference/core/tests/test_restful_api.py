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

import pytest
import requests


@pytest.mark.asyncio
async def test_restful_api(setup):
    endpoint, _ = setup
    print(endpoint)
    url = f"{endpoint}/v1/models"

    # list
    response = requests.get(url)
    response_data = response.json()
    assert len(response_data) == 0

    # launch
    payload = {"model_uid": "test", "model_name": "orca", "quantization": "q4_0"}

    response = requests.post(url, json=payload)
    response_data = response.json()
    model_uid_res = response_data["model_uid"]
    assert model_uid_res == "test"

    # list
    response = requests.get(url)
    response_data = response.json()
    assert len(response_data) == 1

    # generate
    url = f"{endpoint}/v1/completions"
    payload = {
        "model": model_uid_res,
        "prompt": "Once upon a time, there was a very old computer.",
    }
    response = requests.post(url, json=payload)
    completion = response.json()
    assert "text" in completion["choices"][0]

    # chat
    url = f"{endpoint}/v1/chat/completions"
    payload = {
        "model": model_uid_res,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello!"},
            {"role": "assistant", "content": "Hi what can I help you?"},
            {"role": "user", "content": "What is the capital of France?"},
        ],
    }
    response = requests.post(url, json=payload)
    completion = response.json()
    assert "content" in completion["choices"][0]["message"]

    # delete
    url = f"{endpoint}/v1/models/test"
    response = requests.delete(url)

    # list
    response = requests.get(f"{endpoint}/v1/models")
    response_data = response.json()
    assert len(response_data) == 0

    # delete again
    url = f"{endpoint}/v1/models/test"
    response = requests.delete(url)
    assert response.status_code != 200

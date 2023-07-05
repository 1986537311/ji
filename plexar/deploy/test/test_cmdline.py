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
from click.testing import CliRunner

from plexar.client import Client
from plexar.deploy.cmdline import model_generate


@pytest.mark.asyncio
async def test_generate(setup):
    pool = setup
    address = pool.external_address
    client = Client(address)
    model_uid = client.launch_model("wizardlm-v1.0", quantization="q2_K")
    assert model_uid is not None

    runner = CliRunner()
    result = runner.invoke(
        model_generate,
        [
            "--model-uid",
            model_uid,
            "--prompt",
            "You are a helpful AI assistant. USER: write a poem. ASSISTANT:",
        ],
    )

    assert result.exit_code == 0
    assert len(result.stdout) != 0

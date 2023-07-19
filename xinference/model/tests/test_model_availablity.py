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
import os
import platform
from unittest import mock

import pytest
import requests

from ...constants import XINFERENCE_CACHE_DIR
from .. import MODEL_FAMILIES, ModelFamily
from ..llm.wizardlm import WizardlmGgml


@pytest.mark.parametrize(
    "model_spec",
    [
        model_spec
        for model_family in MODEL_FAMILIES
        for model_spec in model_family
        if model_spec.model_format != "pytorch"
    ],
)
def test_model_availability(model_spec):
    attempt = 0
    max_attempt = 3
    if model_spec.model_format != "pytorch":
        while attempt < max_attempt:
            attempt += 1
            try:
                assert requests.head(model_spec.url).status_code != 404
                break
            except Exception:
                continue

    if attempt == max_attempt:
        pytest.fail(f"{str(model_spec)} is not available")


@pytest.mark.parametrize(
    "model_spec",
    [
        model_spec
        for model_family in MODEL_FAMILIES
        for model_spec in model_family
        if model_spec.model_format != "pytorch"
    ],
)
def test_rp_availability(model_spec):
    attempt = 0
    max_attempt = 3
    while attempt < max_attempt:
        attempt += 1
        try:
            assert requests.head(model_spec.rp_url).status_code != 404
            response = requests.get(model_spec.rp_url)
            res_content = response.content
            splitted_res_content = res_content.split()
            expected_size = -1
            stripped_List = []
            for index in range(len(splitted_res_content)):
                current_chunk = str(splitted_res_content[index], encoding="utf-8")
                stripped_List.append(current_chunk)
                if current_chunk == "size":
                    expected_size = int(
                        str(splitted_res_content[index + 1], encoding="utf-8")
                    )

            assert "size" in stripped_List
            assert expected_size != -1
            break
        except Exception:
            continue

    if attempt == max_attempt:
        pytest.fail(f"{str(model_spec)} is not available")


@pytest.mark.skipif(
    platform.system() == "Windows",
    reason="Windows have restriction on write in permission",
)
def test_model_integrity():
    # need to update the link format if the source path is changed or no longer available
    wizardlm_v1_0_url_generator = lambda model_size, quantization: (
        f"https://huggingface.co/TheBloke/WizardLM-{model_size}B-V1.0-Uncensored-GGML/resolve/main/"
        f"wizardlm-{model_size}b-v1.0-uncensored.ggmlv3.{quantization}.bin"
    )

    wizardlm_v1_0_url_raw_generator = lambda model_size, quantization: (
        f"https://huggingface.co/TheBloke/WizardLM-{model_size}B-V1.0-Uncensored-GGML/raw/main/"
        f"wizardlm-{model_size}b-v1.0-uncensored.ggmlv3.{quantization}.bin"
    )

    test_model = ModelFamily(
        model_name="wizardlm-v1.0",
        model_sizes_in_billions=[7],
        model_format="ggmlv3",
        quantizations=["q2_K"],
        url_generator=wizardlm_v1_0_url_generator,
        rp_url_generator=wizardlm_v1_0_url_raw_generator,
        cls=WizardlmGgml,
    )

    # initiate a empty bin folder and test whether a warning is thrown:
    full_name = f"{str(test_model)}-{test_model.model_sizes_in_billions[0]}b-{test_model.quantizations[0]}"
    save_dir = os.path.join(XINFERENCE_CACHE_DIR, full_name)

    os.makedirs(save_dir, exist_ok=True)
    file = os.path.join(save_dir, "model.bin")

    # clean the leftover from the previous test.
    if os.path.exists(file):
        os.remove(file)

    # create a new pseudo file path with empty
    with open(file, "w"):
        pass

    with pytest.warns(Warning) as w:
        test_model.cache()
        assert len(w) == 1

        warning = w[0]
        assert str(warning.message) == "Model size doesn't match, try to update it..."


@pytest.mark.skipif(
    platform.system() == "Windows",
    reason="Windows have restriction on write in permission",
)
def test_model_cache_raise():
    # need to update the link format if the source path is changed or no longer available
    wizardlm_v1_0_url_generator = lambda model_size, quantization: (
        f"https://huggingface.co/TheBloke/WizardLM-{model_size}B-V1.0-Uncensored-GGML/resolve/main/"
        f"wizardlm-{model_size}b-v1.0-uncensored.ggmlv3.{quantization}.bin"
    )

    wizardlm_v1_0_url_raw_generator = lambda model_size, quantization: (
        f"https://huggingface.co/TheBloke/WizardLM-{model_size}B-V1.0-Uncensored-GGML/raw/main/"
        f"wizardlm-{model_size}b-v1.0-uncensored.ggmlv3.{quantization}.bin"
    )

    with mock.patch("requests.get") as mock_get:
        # Set up the desired response
        mock_response = mock.Mock()
        mock_response.status_code = 200
        response_data = "version https://git-lfs.github.com/spec/v1\\noid sha256:e48c7238fb7baeb4006cffb5b77416ddeb492cef0669eabbcc4aaf77d9abad0a\nsize 23\n"
        res_data_encoded = response_data.encode("utf-8")
        mock_response.content = res_data_encoded
        mock_get.return_value = mock_response

        test_model = ModelFamily(
            model_name="wizardlm-v1.0",
            model_sizes_in_billions=[7],
            model_format="ggmlv3",
            quantizations=["q2_K"],
            url_generator=wizardlm_v1_0_url_generator,
            rp_url_generator=wizardlm_v1_0_url_raw_generator,
            cls=WizardlmGgml,
        )

        full_name = f"{str(test_model)}-{test_model.model_sizes_in_billions[0]}b-{test_model.quantizations[0]}"
        save_dir = os.path.join(XINFERENCE_CACHE_DIR, full_name)
        os.makedirs(save_dir, exist_ok=True)
        file = os.path.join(save_dir, "model.bin")

        # clean the leftover from the previous test.
        if os.path.exists(file):
            os.remove(file)

        with pytest.raises(RuntimeError):
            test_model.cache()

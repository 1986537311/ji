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


def install():
    from plexar.model.llm.core import LlamaCppModel

    from .. import MODEL_FAMILIES, ModelFamily
    from .vicuna import VicunaCensoredGgml, VicunaUncensoredGgml
    from .wizardlm import WizardlmGgml

    baichuan_url_generator = lambda model_size, quantization: (
        f"https://huggingface.co/TheBloke/baichuan-llama-{model_size}B-GGML/resolve/main/"
        f"baichuan-llama-{model_size}b.ggmlv3.{quantization}.bin"
    )
    MODEL_FAMILIES.append(
        ModelFamily(
            model_name="baichuan",
            model_format="ggmlv3",
            model_sizes_in_billions=[7],
            quantizations=[
                "q2_K",
                "q3_K_L",
                "q3_K_M",
                "q3_K_S",
                "q4_0",
                "q4_1",
                "q4_K_M",
                "q4_K_S",
                "q5_0",
                "q5_1",
                "q5_K_M",
                "q5_K_S",
                "q6_K",
                "q8_0",
            ],
            url_generator=baichuan_url_generator,
            cls=LlamaCppModel,
        )
    )

    baichuan_chat_url_generator = lambda model_size, quantization: (
        f"https://huggingface.co/TheBloke/baichuan-vicuna-{model_size}B-GGML/resolve/main/"
        f"baichuan-vicuna-{model_size}b.ggmlv3.{quantization}.bin"
    )
    MODEL_FAMILIES.append(
        ModelFamily(
            model_name="baichuan-chat",
            model_format="ggmlv3",
            model_sizes_in_billions=[7],
            quantizations=[
                "q2_K",
                "q3_K_L",
                "q3_K_M",
                "q3_K_S",
                "q4_0",
                "q4_1",
                "q4_K_M",
                "q4_K_S",
                "q5_0",
                "q5_1",
                "q5_K_M",
                "q5_K_S",
                "q6_K",
                "q8_0",
            ],
            url_generator=baichuan_chat_url_generator,
            cls=VicunaCensoredGgml,
        )
    )

    wizardlm_v1_0_url_generator = lambda model_size, quantization: (
        f"https://huggingface.co/TheBloke/WizardLM-{model_size}B-V1.0-Uncensored-GGML/resolve/main/"
        f"wizardlm-{model_size}b-v1.0-uncensored.ggmlv3.{quantization}.bin"
    )
    MODEL_FAMILIES.append(
        ModelFamily(
            model_name="wizardlm-v1.0",
            model_sizes_in_billions=[7, 13, 33],
            model_format="ggmlv3",
            quantizations=[
                "q2_K",
                "q3_K_L",
                "q3_K_M",
                "q3_K_S",
                "q4_0",
                "q4_1",
                "q4_K_M",
                "q4_K_S",
                "q5_0",
                "q5_1",
                "q5_K_M",
                "q5_K_S",
                "q6_K",
                "q8_0",
            ],
            url_generator=wizardlm_v1_0_url_generator,
            cls=WizardlmGgml,
        ),
    )

    vicuna_v1_3_url_generator = lambda model_size, quantization: (
        "https://huggingface.co/TheBloke/vicuna-7B-v1.3-GGML/resolve/main/"
        f"vicuna-7b-v1.3.ggmlv3.{quantization}.bin"
        if model_size == 7
        else (
            "https://huggingface.co/TheBloke/vicuna-13b-v1.3.0-GGML/resolve/main/"
            f"vicuna-13b-v1.3.0.ggmlv3.{quantization}.bin"
        )
    )
    MODEL_FAMILIES.append(
        ModelFamily(
            model_name="vicuna-v1.3",
            model_sizes_in_billions=[7, 13],
            model_format="ggmlv3",
            quantizations=[
                "q2_K",
                "q3_K_L",
                "q3_K_M",
                "q3_K_S",
                "q4_0",
                "q4_1",
                "q4_K_M",
                "q4_K_S",
                "q5_0",
                "q5_1",
                "q5_K_M",
                "q5_K_S",
                "q6_K",
                "q8_0",
            ],
            url_generator=vicuna_v1_3_url_generator,
            cls=VicunaCensoredGgml,
        ),
    )

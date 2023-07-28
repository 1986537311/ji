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

import json
import os
from typing import List, Optional, Tuple, Type

from .core import LLM
from .llm_family import (
    GgmlLLMSpecV1,
    LLMFamilyV1,
    LLMSpecV1,
    PromptStyleV1,
    PytorchLLMSpecV1,
)

_LLM_CLASSES: List[Type[LLM]] = []

LLM_FAMILIES: List["LLMFamilyV1"] = []


def match_llm(
    model_name: str,
    model_format: Optional[str] = None,
    model_size_in_billions: Optional[int] = None,
    quantization: Optional[str] = None,
) -> Optional[Tuple[LLMFamilyV1, LLMSpecV1, str]]:
    """
    Find an LLM family, spec, and quantization that satisfy given criteria.
    """
    for family in LLM_FAMILIES:
        if model_name != family.model_name:
            continue
        for spec in family.model_specs:
            if (
                model_format
                and model_format != spec.model_format
                or model_size_in_billions
                and model_size_in_billions != spec.model_size_in_billions
                or quantization
                and quantization not in spec.quantizations
            ):
                continue
            # by default, choose the most coarse-grained quantization.
            return family, spec, quantization or spec.quantizations[0]
    return None


def match_llm_cls(
    llm_family: LLMFamilyV1, llm_spec: "LLMSpecV1"
) -> Optional[Type[LLM]]:
    """
    Find an LLM implementation for given LLM family and spec.
    """
    for cls in _LLM_CLASSES:
        if cls.match(llm_family, llm_spec):
            return cls
    return None


def _install():
    from .ggml.chatglm import ChatglmCppChatModel
    from .ggml.llamacpp import LlamaCppChatModel, LlamaCppModel
    from .pytorch.baichuan import BaichuanPytorchChatModel, BaichuanPytorchModel
    from .pytorch.core import PytorchChatModel, PytorchModel

    _LLM_CLASSES.extend(
        [
            ChatglmCppChatModel,
            LlamaCppModel,
            LlamaCppChatModel,
            PytorchModel,
            PytorchChatModel,
            BaichuanPytorchModel,
            BaichuanPytorchChatModel,
        ]
    )

    json_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "llm_family.json"
    )
    for json_obj in json.load(open(json_path)):
        LLM_FAMILIES.append(LLMFamilyV1.parse_obj(json_obj))

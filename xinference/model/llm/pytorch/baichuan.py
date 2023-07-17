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

from typing import TYPE_CHECKING, Optional

from ....constants import XINFERENCE_CACHE_DIR
from .core import PytorchModel, PytorchModelConfig

if TYPE_CHECKING:
    from ... import ModelSpec


class BaichuanPytorch(PytorchModel):
    def __init__(
        self,
        model_uid: str,
        model_spec: "ModelSpec",
        model_path: str,
        pytorch_model_config: Optional[PytorchModelConfig] = None,
    ):
        super().__init__(
            model_uid,
            model_spec,
            model_path,
            pytorch_model_config=pytorch_model_config,
        )

    def _load_model(self, kwargs: dict):
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError:
            error_message = "Failed to import module 'transformers'"
            installation_guide = [
                "Please make sure 'transformers' is installed. ",
                "You can install it by `pip install transformers`\n",
            ]

            raise ImportError(f"{error_message}\n\n{''.join(installation_guide)}")

        tokenizer = AutoTokenizer.from_pretrained(
            self._model_path,
            trust_remote_code=True,
            revision=kwargs["revision"],
            cache_dir=XINFERENCE_CACHE_DIR,
        )
        model = AutoModelForCausalLM.from_pretrained(
            self._model_path,
            trust_remote_code=True,
            low_cpu_mem_usage=True,
            cache_dir=XINFERENCE_CACHE_DIR,
            **kwargs,
        )
        return model, tokenizer

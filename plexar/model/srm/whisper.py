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

import subprocess
from typing import List

import numpy as np

from ..srm.utils import convert_wav_to_array, record_unlimited
from .core import SpeechRecognitionModel

try:
    from whispercpp import Whisper
except ImportError:  # pragma: no cover
    subprocess.check_call(["pip", "install", "whispercpp"])


class WhisperGgml(SpeechRecognitionModel):
    pass


class WhisperCpp(SpeechRecognitionModel):
    def get_array_output(self) -> np.ndarray:
        return convert_wav_to_array(record_unlimited())

    def transcribe(self, inp: np.ndarray) -> List[str]:
        w = Whisper.from_pretrained("base")
        res = w.transcribe(inp)
        return [res]

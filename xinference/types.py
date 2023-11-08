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

from typing import Any, Callable, Dict, Iterable, List, Optional, Union

from pydantic import (
    BaseModel,
    create_model,
    validate_arguments,
    create_model_from_typeddict,
)
from typing_extensions import Literal, NotRequired, TypedDict

from .fields import (
    echo_field,
    max_tokens_field,
    none_field,
    repeat_penalty_field,
    stop_field,
    stream_field,
    stream_interval_field,
    temperature_field,
    top_k_field,
    top_p_field,
)


class Image(TypedDict):
    url: Optional[str]
    b64_json: Optional[str]


class ImageList(TypedDict):
    created: int
    data: List[Image]


class EmbeddingUsage(TypedDict):
    prompt_tokens: int
    total_tokens: int


class EmbeddingData(TypedDict):
    index: int
    object: str
    embedding: List[float]


class Embedding(TypedDict):
    object: Literal["list"]
    model: str
    data: List[EmbeddingData]
    usage: EmbeddingUsage


class CompletionLogprobs(TypedDict):
    text_offset: List[int]
    token_logprobs: List[Optional[float]]
    tokens: List[str]
    top_logprobs: List[Optional[Dict[str, float]]]


class CompletionChoice(TypedDict):
    text: str
    index: int
    logprobs: Optional[CompletionLogprobs]
    finish_reason: Optional[str]


class CompletionUsage(TypedDict):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class CompletionChunk(TypedDict):
    id: str
    object: Literal["text_completion"]
    created: int
    model: str
    choices: List[CompletionChoice]


class Completion(TypedDict):
    id: str
    object: Literal["text_completion"]
    created: int
    model: str
    choices: List[CompletionChoice]
    usage: CompletionUsage


class ChatCompletionMessage(TypedDict):
    role: str
    content: str
    user: NotRequired[str]


class ChatCompletionChoice(TypedDict):
    index: int
    message: ChatCompletionMessage
    finish_reason: Optional[str]


class ChatCompletion(TypedDict):
    id: str
    object: Literal["chat.completion"]
    created: int
    model: str
    choices: List[ChatCompletionChoice]
    usage: CompletionUsage


class ChatCompletionChunkDelta(TypedDict):
    role: NotRequired[str]
    content: NotRequired[str]


class ChatCompletionChunkChoice(TypedDict):
    index: int
    delta: ChatCompletionChunkDelta
    finish_reason: Optional[str]


class ChatCompletionChunk(TypedDict):
    id: str
    model: str
    object: Literal["chat.completion.chunk"]
    created: int
    choices: List[ChatCompletionChunkChoice]


class ChatglmCppModelConfig(TypedDict, total=False):
    pass


class ChatglmCppGenerateConfig(TypedDict, total=False):
    max_tokens: int
    top_p: float
    temperature: float
    stream: bool


StoppingCriteria = Callable[[List[int], List[float]], bool]


class StoppingCriteriaList(List[StoppingCriteria]):
    def __call__(self, input_ids: List[int], logits: List[float]) -> bool:
        return any([stopping_criteria(input_ids, logits) for stopping_criteria in self])


LogitsProcessor = Callable[[List[int], List[float]], List[float]]


class LogitsProcessorList(List[LogitsProcessor]):
    def __call__(self, input_ids: List[int], scores: List[float]) -> List[float]:
        for processor in self:
            scores = processor(input_ids, scores)
        return scores


class LlamaCppGenerateConfig(TypedDict, total=False):
    suffix: Optional[str]
    max_tokens: int
    temperature: float
    top_p: float
    logprobs: Optional[int]
    echo: bool
    stop: Optional[Union[str, List[str]]]
    frequency_penalty: float
    presence_penalty: float
    repetition_penalty: float
    top_k: int
    stream: bool
    tfs_z: float
    mirostat_mode: int
    mirostat_tau: float
    mirostat_eta: float
    model: Optional[str]
    grammar: Optional[Any]
    stopping_criteria: Optional["StoppingCriteriaList"]
    logits_processor: Optional["LogitsProcessorList"]


class LlamaCppModelConfig(TypedDict, total=False):
    n_ctx: int
    n_parts: int
    n_gpu_layers: int
    seed: int
    f16_kv: bool
    logits_all: bool
    vocab_only: bool
    use_mmap: bool
    use_mlock: bool
    embedding: bool
    n_threads: Optional[int]
    n_batch: int
    last_n_tokens_size: int
    lora_base: Optional[str]
    lora_path: Optional[str]
    low_vram: bool
    n_gqa: Optional[int]  # (TEMPORARY) must be 8 for llama2 70b
    rms_norm_eps: Optional[float]  # (TEMPORARY)
    verbose: bool


class PytorchGenerateConfig(TypedDict, total=False):
    temperature: float
    repetition_penalty: float
    top_p: float
    top_k: int
    stream: bool
    max_tokens: int
    echo: bool
    stop: Optional[Union[str, List[str]]]
    stop_token_ids: Optional[Union[int, List[int]]]
    stream_interval: int
    model: Optional[str]


class PytorchModelConfig(TypedDict, total=False):
    revision: Optional[str]
    device: str
    gpus: Optional[str]
    num_gpus: int
    max_gpu_memory: str
    gptq_ckpt: Optional[str]
    gptq_wbits: int
    gptq_groupsize: int
    gptq_act_order: bool
    trust_remote_code: bool


def get_pydantic_model_from_method(
    meth,
    exclude_fields: Iterable[str] = None,
    include_fields: Dict[str, Any] = None,
):
    f = validate_arguments(meth, config={"arbitrary_types_allowed": True})
    model = f.model
    model.__fields__.pop("self", None)
    model.__fields__.pop("args", None)
    model.__fields__.pop("kwargs", None)
    pydantic_private_keys = [
        key for key in model.__fields__.keys() if key.startswith("v__")
    ]
    for key in pydantic_private_keys:
        model.__fields__.pop(key)
    if exclude_fields is not None:
        for key in exclude_fields:
            model.__fields__.pop(key)
    if include_fields is not None:
        dummy_model = create_model("DummyModel", **include_fields)
        model.__fields__.update(dummy_model.__fields__)
    return model


class CreateCompletionTorch(BaseModel):
    model: str
    prompt: str
    echo: bool = echo_field
    max_tokens: int = max_tokens_field
    repetition_penalty: float = repeat_penalty_field
    stop: Optional[Union[str, List[str]]] = stop_field
    stop_token_ids: Optional[Union[int, List[int]]] = none_field
    stream: bool = stream_field
    stream_interval: int = stream_interval_field
    temperature: float = temperature_field
    top_p: float = top_p_field
    top_k: int = top_k_field


try:
    from llama_cpp import Llama

    CreateCompletionLlamaCpp = get_pydantic_model_from_method(
        Llama.create_completion, exclude_fields=["model"]
    )
except ImportError:
    CreateCompletionLlamaCpp = object


try:
    from ctransformers.llm import LLM

    CreateCompletionCTransformers = get_pydantic_model_from_method(
        LLM.generate,
        exclude_fields=["tokens"],
        include_fields={"max_tokens": (int, max_tokens_field)},
    )
except ImportError:
    CreateCompletionCTransformers = object


try:
    from openai.types.completion_create_params import CompletionCreateParamsNonStreaming

    CreateCompletionOpenAI = create_model_from_typeddict(
        CompletionCreateParamsNonStreaming,
    )
except ImportError:
    CreateCompletionOpenAI = object


class CreateCompletion(
    CreateCompletionTorch,
    CreateCompletionLlamaCpp,
    CreateCompletionCTransformers,
    CreateCompletionOpenAI,
):
    pass

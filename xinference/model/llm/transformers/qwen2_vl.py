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
import logging
import time
import uuid
from typing import Dict, Iterator, List, Optional, Union

from qwen_vl_utils import process_vision_info

from ....model.utils import select_device
from ....types import (
    ChatCompletion,
    ChatCompletionChunk,
    ChatCompletionMessage,
    Completion,
    CompletionChoice,
    CompletionChunk,
    CompletionUsage,
)
from ..llm_family import LLMFamilyV1, LLMSpecV1
from .core import PytorchChatModel, PytorchGenerateConfig

logger = logging.getLogger(__name__)


class Qwen2VLChatModel(PytorchChatModel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._tokenizer = None
        self._model = None
        self._device = None
        self._processor = None

    @classmethod
    def match(
        cls, model_family: "LLMFamilyV1", model_spec: "LLMSpecV1", quantization: str
    ) -> bool:
        llm_family = model_family.model_family or model_family.model_name
        if "qwen2-vl-instruct".lower() in llm_family.lower():
            return True
        return False

    def load(self):
        from transformers import AutoProcessor, Qwen2VLForConditionalGeneration

        device = self._pytorch_model_config.get("device", "auto")
        device = select_device(device)
        self._device = device
        # for multiple GPU, set back to auto to make multiple devices work
        device = "auto" if device == "cuda" else device

        self._processor = AutoProcessor.from_pretrained(
            self.model_path, trust_remote_code=True
        )
        self._tokenizer = self._processor.tokenizer
        self._model = Qwen2VLForConditionalGeneration.from_pretrained(
            self.model_path, device_map=device, trust_remote_code=True
        ).eval()

    def _transform_messages(
        self,
        prompt: Union[str, List[Dict]],
        chat_history: Optional[List[ChatCompletionMessage]],
    ):
        original_messages = chat_history or []
        original_messages.append(ChatCompletionMessage(role="user", content=prompt))
        transformed_messages = []
        for msg in original_messages:
            new_content = []
            role = msg["role"]
            content = msg["content"]
            if isinstance(content, str):
                new_content.append({"type": "text", "text": content})
            elif isinstance(content, List):
                for item in content:
                    if "text" in item:
                        new_content.append({"type": "text", "text": item["text"]})
                    elif "image_url" in item:
                        new_content.append(
                            {"type": "image", "image": item["image_url"]["url"]}
                        )
                    elif "video_url" in item:
                        new_content.append(
                            {"type": "video", "video": item["video_url"]["url"]}
                        )
            new_message = {"role": role, "content": new_content}
            transformed_messages.append(new_message)

        return transformed_messages

    def chat(
        self,
        prompt: Union[str, List[Dict]],
        chat_history: Optional[List[ChatCompletionMessage]] = None,
        generate_config: Optional[PytorchGenerateConfig] = None,
    ) -> Union[ChatCompletion, Iterator[ChatCompletionChunk]]:
        messages = self._transform_messages(prompt, chat_history)

        generate_config = generate_config if generate_config else {}

        stream = generate_config.get("stream", False) if generate_config else False

        if stream:
            it = self._generate_stream(messages, generate_config)
            return self._to_chat_completion_chunks(it)
        else:
            c = self._generate(messages, generate_config)
            return self._to_chat_completion(c)

    def _generate(
        self, messages: List, config: Optional[PytorchGenerateConfig] = {}
    ) -> Completion:
        # Preparation for inference
        text = self._processor.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        image_inputs, video_inputs = process_vision_info(messages)
        inputs = self._processor(
            text=[text],
            images=image_inputs,
            videos=video_inputs,
            padding=True,
            return_tensors="pt",
        )
        inputs = inputs.to("cuda")

        # Inference: Generation of the output
        generated_ids = self._model.generate(
            **inputs,
            max_new_tokens=config.get("max_tokens", 512),
            temperature=config.get("temperature", 1),
        )
        generated_ids_trimmed = [
            out_ids[len(in_ids) :]
            for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
        ]
        output_text = self._processor.batch_decode(
            generated_ids_trimmed,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False,
        )[0]
        # output_text = ""
        c = Completion(
            id=str(uuid.uuid1()),
            object="text_completion",
            created=int(time.time()),
            model=self.model_uid,
            choices=[
                CompletionChoice(
                    index=0, text=output_text, finish_reason="stop", logprobs=None
                )
            ],
            usage=CompletionUsage(
                prompt_tokens=-1, completion_tokens=-1, total_tokens=-1
            ),
        )
        return c

    def _generate_stream(
        self, messages: List, config: Optional[PytorchGenerateConfig] = {}
    ) -> Iterator[CompletionChunk]:
        from threading import Thread

        from transformers import TextIteratorStreamer

        text = self._processor.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        image_inputs, video_inputs = process_vision_info(messages)
        inputs = self._processor(
            text=[text],
            images=image_inputs,
            videos=video_inputs,
            padding=True,
            return_tensors="pt",
        )
        inputs = inputs.to(self._model.device)

        tokenizer = self._tokenizer
        streamer = TextIteratorStreamer(
            tokenizer, timeout=60.0, skip_prompt=True, skip_special_tokens=True
        )

        gen_kwargs = {
            "max_new_tokens": config.get("max_tokens", 512),
            "temperature": config.get("temperature", 1),
            "streamer": streamer,
            **inputs,
        }

        thread = Thread(target=self._model.generate, kwargs=gen_kwargs)
        thread.start()

        completion_id = str(uuid.uuid1())
        for new_text in streamer:
            chunk = CompletionChunk(
                id=completion_id,
                object="text_completion",
                created=int(time.time()),
                model=self.model_uid,
                choices=[
                    CompletionChoice(
                        index=0, text=new_text, finish_reason=None, logprobs=None
                    )
                ],
                usage=CompletionUsage(
                    prompt_tokens=-1, completion_tokens=-1, total_tokens=-1
                ),
            )
            yield chunk

        completion_choice = CompletionChoice(
            text="", index=0, logprobs=None, finish_reason="stop"
        )
        chunk = CompletionChunk(
            id=completion_id,
            object="text_completion",
            created=int(time.time()),
            model=self.model_uid,
            choices=[completion_choice],
            usage=CompletionUsage(
                prompt_tokens=-1, completion_tokens=-1, total_tokens=-1
            ),
        )
        yield chunk

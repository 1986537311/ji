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
import uuid
from typing import TYPE_CHECKING, Dict, List, Optional

import gradio as gr

from xinference.client import RESTfulClient
from xinference.locale.utils import Locale
from xinference.model.llm import BUILTIN_LLM_FAMILIES, LLMFamilyV1, match_llm
from xinference.model.llm.llm_family import cache

if TYPE_CHECKING:
    from xinference.types import ChatCompletionMessage

MODEL_TO_FAMILIES: Dict[str, LLMFamilyV1] = dict(
    (model_family.model_name, model_family)
    for model_family in BUILTIN_LLM_FAMILIES
    if "chat" in model_family.model_ability
)


class GradioApp:
    def __init__(
        self,
        endpoint: str,
        gladiator_num: int = 2,
        max_model_num: int = 3,
        use_launched_model: bool = False,
    ):
        self._api = RESTfulClient(endpoint)
        self._gladiator_num = gladiator_num
        self._max_model_num = max_model_num
        self._use_launched_model = use_launched_model
        self._locale = Locale()

    def _create_model(
        self,
        model_name: str,
        model_size_in_billions: Optional[int] = None,
        model_format: Optional[str] = None,
        quantization: Optional[str] = None,
    ):
        models = self._api.list_models()
        if len(models) >= self._max_model_num:
            self._api.terminate_model(list(models.keys())[0])
        return self._api.launch_model(
            model_name, model_size_in_billions, model_format, quantization
        )

    async def generate(
        self,
        model: str,
        message: str,
        chat: List[List[str]],
        max_token: int,
        temperature: float,
        top_p: float,
        window_size: int,
        show_finish_reason: bool,
    ):
        if not message:
            yield message, chat
        else:
            try:
                model_ref = self._api.get_model(model)
            except KeyError:
                raise gr.Error(self._locale(f"Please create model first"))

            history: "List[ChatCompletionMessage]" = []
            for c in chat:
                history.append({"role": "user", "content": c[0]})

                out = c[1]
                finish_reason_idx = out.find(f"[{self._locale('stop reason')}: ")
                if finish_reason_idx != -1:
                    out = out[:finish_reason_idx]
                history.append({"role": "assistant", "content": out})

            if window_size != 0:
                history = history[-(window_size // 2) :]

            # chatglm only support even number of conversation history.
            if len(history) % 2 != 0:
                history = history[1:]

            generate_config = dict(
                max_tokens=max_token,
                temperature=temperature,
                top_p=top_p,
                stream=False,
            )
            chat += [[message, ""]]
            chat_response = model_ref.chat(
                message,
                chat_history=history,
                generate_config=generate_config,
            )

            chat[-1][1] += chat_response["choices"][0]["message"]["content"]
            if show_finish_reason and chat_response is not None:
                chat[-1][
                    1
                ] += f"[{self._locale('stop reason')}: {chat_response['choices'][0]['finish_reason']}]"
            yield "", chat

    def _build_chatbot(self, model_uid: str, model_name: str):
        with gr.Accordion(self._locale("Parameters"), open=False):
            max_token = gr.Slider(
                128,
                1024,
                value=256,
                step=1,
                label=self._locale("Max tokens"),
                info=self._locale("The maximum number of tokens to generate."),
            )
            temperature = gr.Slider(
                0.2,
                1,
                value=0.8,
                step=0.01,
                label=self._locale("Temperature"),
                info=self._locale("The temperature to use for sampling."),
            )
            top_p = gr.Slider(
                0.2,
                1,
                value=0.95,
                step=0.01,
                label=self._locale("Top P"),
                info=self._locale("The top-p value to use for sampling."),
            )
            window_size = gr.Slider(
                0,
                50,
                value=10,
                step=1,
                label=self._locale("Window size"),
                info=self._locale("Window size of chat history."),
            )
            show_finish_reason = gr.Checkbox(
                label=f"{self._locale('Show stop reason')}"
            )
        chat = gr.Chatbot(label=model_name)
        text = gr.Textbox(visible=False)
        model_uid = gr.Textbox(model_uid, visible=False)
        text.change(
            self.generate,
            [
                model_uid,
                text,
                chat,
                max_token,
                temperature,
                top_p,
                window_size,
                show_finish_reason,
            ],
            [text, chat],
        )
        return (
            text,
            chat,
            max_token,
            temperature,
            top_p,
            show_finish_reason,
            window_size,
            model_uid,
        )

    def _build_chat_column(self):
        with gr.Column():
            with gr.Row():
                model_name = gr.Dropdown(
                    choices=list(MODEL_TO_FAMILIES.keys()),
                    label=self._locale("model name"),
                    scale=2,
                )
                model_format = gr.Dropdown(
                    choices=[],
                    interactive=False,
                    label=self._locale("model format"),
                    scale=2,
                )
                model_size_in_billions = gr.Dropdown(
                    choices=[],
                    interactive=False,
                    label=self._locale("model size in billions"),
                    scale=1,
                )
                quantization = gr.Dropdown(
                    choices=[],
                    interactive=False,
                    label=self._locale("quantization"),
                    scale=1,
                )
            create_model = gr.Button(value=self._locale("create"))

            def select_model_name(model_name: str):
                if model_name:
                    model_family = MODEL_TO_FAMILIES[model_name]
                    formats = list(
                        {spec.model_format for spec in model_family.model_specs}
                    )
                    formats.sort()
                    return (
                        gr.Dropdown.update(
                            choices=formats, interactive=True, value=None
                        ),
                        gr.Dropdown.update(choices=[], interactive=False, value=None),
                        gr.Dropdown.update(choices=[], interactive=False, value=None),
                    )
                else:
                    return (
                        gr.Dropdown.update(),
                        gr.Dropdown.update(),
                        gr.Dropdown.update(),
                    )

            def select_model_format(model_name: str, model_format: str):
                if model_name:
                    model_family = MODEL_TO_FAMILIES[model_name]
                    sizes = list(
                        {
                            spec.model_size_in_billions
                            for spec in model_family.model_specs
                            if spec.model_format == model_format
                        }
                    )
                    sizes.sort()
                    return (
                        gr.Dropdown.update(
                            choices=list(map(lambda s: str(s), sizes)),
                            interactive=True,
                            value=None,
                        ),
                        gr.Dropdown.update(choices=[], interactive=False, value=None),
                    )
                else:
                    return (
                        gr.Dropdown.update(),
                        gr.Dropdown.update(),
                    )

            def select_model_size(
                model_name: str, model_format: str, model_size_in_billions: str
            ):
                if model_name:
                    model_family = MODEL_TO_FAMILIES[model_name]
                    quantizations = list(
                        {
                            quantization
                            for spec in model_family.model_specs
                            if spec.model_format == model_format
                            and str(spec.model_size_in_billions)
                            == model_size_in_billions
                            for quantization in spec.quantizations
                        }
                    )
                    quantizations.sort()
                    return gr.Dropdown.update(
                        choices=quantizations,
                        interactive=True,
                    )
                else:
                    return gr.Dropdown.update()

            model_name.change(
                select_model_name,
                inputs=[model_name],
                outputs=[model_format, model_size_in_billions, quantization],
            )
            model_format.change(
                select_model_format,
                inputs=[model_name, model_format],
                outputs=[model_size_in_billions, quantization],
            )
            model_size_in_billions.change(
                select_model_size,
                inputs=[model_name, model_format, model_size_in_billions],
                outputs=[quantization],
            )

            components = self._build_chatbot("", "")
            model_text = components[0]
            chat, model_uid = components[1], components[-1]

        def select_model(
            _model_name: str,
            _model_format: str,
            _model_size_in_billions: str,
            _quantization: str,
            progress=gr.Progress(track_tqdm=True),
        ):
            match_result = match_llm(
                _model_name,
                _model_format,
                int(_model_size_in_billions),
                _quantization,
            )
            if not match_result:
                raise ValueError(
                    f"Model not found, name: {_model_name}, format: {_model_format},"
                    f" size: {_model_size_in_billions}, quantization: {_quantization}"
                )

            llm_family, llm_spec, _quantization = match_result
            cache(llm_family, llm_spec, _quantization)

            model_uid = self._create_model(
                _model_name, int(_model_size_in_billions), _model_format, _quantization
            )
            return gr.Chatbot.update(
                label="-".join(
                    [_model_name, _model_size_in_billions, _model_format, _quantization]
                ),
                value=[],
            ), gr.Textbox.update(value=model_uid)

        def clear_chat(
            _model_name: str,
            _model_format: str,
            _model_size_in_billions: str,
            _quantization: str,
        ):
            full_name = "-".join(
                [_model_name, _model_size_in_billions, _model_format, _quantization]
            )
            return str(uuid.uuid4()), gr.Chatbot.update(
                label=full_name,
                value=[],
            )

        invisible_text = gr.Textbox(visible=False)
        create_model.click(
            clear_chat,
            inputs=[model_name, model_format, model_size_in_billions, quantization],
            outputs=[invisible_text, chat],
        )

        invisible_text.change(
            select_model,
            inputs=[model_name, model_format, model_size_in_billions, quantization],
            outputs=[chat, model_uid],
            postprocess=False,
        )
        return chat, model_text

    def _build_arena(self):
        with gr.Box():
            with gr.Row():
                chat_and_text = [
                    self._build_chat_column() for _ in range(self._gladiator_num)
                ]
                chats = [c[0] for c in chat_and_text]
                texts = [c[1] for c in chat_and_text]

            msg = gr.Textbox(label=self._locale("Input"))

            def update_message(text_in: str):
                return "", text_in, text_in

            msg.submit(update_message, inputs=[msg], outputs=[msg] + texts)

        gr.ClearButton(components=[msg] + chats + texts)

    def build(self):
        with gr.Blocks() as blocks:
            self._build_arena()
        blocks.queue(concurrency_count=40)
        blocks.launch()


if __name__ == "__main__":
    import argparse
    import textwrap

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(
            """\
            instructions to run:

                1. Install Xinference, Llama-cpp-python, and other dependencies if necessary
                2. Run command `xinference --host "localhost"` in terminal
                3. You should see something similar to the following output:

                INFO:xinference:Xinference successfully started. Endpoint: http://localhost:9997
                INFO:xinference.core.service:Worker 127.0.0.1:21561 has been added successfully
                INFO:xinference.deploy.worker:Xinference worker successfully started.

                4. In the output, locate the endpoint. In the above case it is `http://localhost:9997`
                5. Run this python file in new terminal window, change the endpoint accordingly

                example run command (feel free to copy):

                python gradio_arena.py \\
                --endpoint http://localhost:9997
            """
        ),
    )

    parser.add_argument(
        "--endpoint", type=str, required=True, help="Xinference endpoint, required"
    )

    args = parser.parse_args()
    print(f"Xinference endpoint: {args.endpoint}")
    GradioApp(args.endpoint).build()

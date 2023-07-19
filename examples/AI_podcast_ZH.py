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
import argparse
import logging
import os
import queue
import re
import sys
import tempfile
import time
import warnings

warnings.filterwarnings("ignore")

try:
    import ffmpeg
except ImportError:
    raise ImportError(
        "Failed to import ffmpeg, please install ffmpeg with `brew install ffmpeg & pip install"
        " ffmpeg`"
    )

try:
    import sounddevice as sd
except ImportError:
    raise ImportError(
        "Failed to import sounddevice, please install sounddevice with `pip install sounddevice`"
    )

try:
    import soundfile as sf
except:
    raise ImportError(
        "Failed to import soundfile, please install soundfile with `pip install soundfile`"
    )

try:
    import emoji
except ImportError:
    raise ImportError(
        "Failed to import emoji, please check the "
        "correct package at https://pypi.org/project/emoji/"
    )

try:
    import numpy
except ImportError:
    raise ImportError(
        "Failed to import numpy, please check the "
        "correct package at https://pypi.org/project/numpy/1.24.1/"
    )

try:
    import whisper
except ImportError:
    raise ImportError(
        "Failed to import whisper, please check the "
        "correct package at https://pypi.org/project/openai-whisper/"
    )

try:
    from xinference.client import Client
    from xinference.types import ChatCompletionMessage
except ImportError:
    raise ImportError(
        "Falied to import xinference, please check the "
        "correct package at https://pypi.org/project/xinference/"
    )

# ------------------------------------- global variable initialization ---------------------------------------------- #
warnings.filterwarnings('ignore')
logger = logging.getLogger(__name__)
# global variable to store the audio device choices.
audio_devices = "-1"

# ----------------------------------------- decorator libraries ----------------------------------------------------- #
emoji_man = "\U0001F467"
emoji_women = emoji.emojize(":woman:")
emoji_system = emoji.emojize(":robot:")
emoji_user = emoji.emojize(":supervillain:")
emoji_speaking = emoji.emojize(":speaking_head:")
emoji_sparkiles = emoji.emojize(":sparkles:")
emoji_jack_o_lantern = emoji.emojize(":jack-o-lantern:")
emoji_microphone = emoji.emojize(":studio_microphone:")
emoji_rocket = emoji.emojize(":rocket:")


# --------------------------------- supplemented util to get the record --------------------------------------------- #
def get_audio_devices() -> str:
    import sounddevice as sd

    global audio_devices

    if audio_devices != "-1":
        return str(audio_devices)

    devices = sd.query_devices()
    print("\n")
    print(emoji_microphone, end="")
    print("  音频设备:")
    print(devices)
    print(emoji_microphone, end="")
    audio_devices = input("  请选择你想用作音频输入的设备: ")
    return audio_devices


q: queue.Queue = queue.Queue()


def callback(indata, frames, time, status):
    """This is called (from a separate thread) for each audio block."""
    if status:
        print(status, file=sys.stderr)
    q.put(indata.copy())


# function to take audio input and transcript it into text-file.
def record_unlimited() -> numpy.ndarray:
    user_device = int(get_audio_devices())
    print("")
    terminal_size = os.get_terminal_size()
    print("-" * terminal_size.columns)
    print(emoji_speaking, end="")
    input("  输入 Enter 键位开始录音，随后输入 Ctrl + C 停止录音:")
    filename = tempfile.mktemp(prefix="delme_rec_unlimited_", suffix=".wav", dir="")
    try:
        # Make sure the file is opened before recording anything:
        with sf.SoundFile(filename, mode="x", samplerate=48000, channels=1) as file:
            with sd.InputStream(
                    samplerate=48000, device=user_device, channels=1, callback=callback
            ):
                while True:
                    file.write(q.get())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(type(e).__name__ + ": " + str(e))

    try:
        y, _ = (
            ffmpeg.input(os.path.abspath(filename), threads=0)
            .output("-", format="s16le", acodec="pcm_s16le", ac=1, ar=16000)
            .run(cmd=["ffmpeg", "-nostdin"], capture_stdout=True, capture_stderr=True)
        )
    except ffmpeg.Error as e:
        raise RuntimeError(f"Failed to load audio: {e.stderr.decode()}") from e
    os.remove(filename)
    return numpy.frombuffer(y, numpy.int16).flatten().astype(numpy.float32) / 32768.0


def format_prompt(model, audio_input) -> str:
    # the second parameters of transcribe enable us to define the language we are speaking.
    return model.transcribe(audio_input)["text"]


# transcript the generated chatbot word to audio output so the user will hear the result.
def text_to_audio(response, voice_id):
    # for audio output, we apply the mac initiated "say" command to provide. For Windows users, if you want
    # audio output, you can try on pyttsx3 or gtts package to see their functionality!
    import subprocess

    # Text to convert to speech
    text = response
    if voice_id == "小红":
        voice = "Meijia"
    elif voice_id == "小花":
        voice = "Sinji"
    # anything not belongs to alice or bob are said by system voice.
    else:
        voice = "Tingting"
    # Execute the "say" command and wait the command to be completed.
    process = subprocess.Popen(["say", "-v", voice, text])
    process.wait()


# async function to chat with the bot.
def chat_with_bot(
        format_input, chat_history, alice_or_bob_state, system_prompt, model_ref, usname,
):
    # gen full prompt locally
    # full_prompt = _to_prompt(
    #     format_input, system_prompt, usname, alice_or_bob_state, chat_history=chat_history
    # )

    completion = model_ref.chat(
        prompt=format_input,
        system_prompt=system_prompt,
        chat_history=chat_history,
        generate_config={"max_tokens": 1024},
    )

    if alice_or_bob_state == "小红":
        print(emoji_women, end="")
        print(" 小红:", end="")
    else:
        print(emoji_man, end="")
        print(" 小花:", end="")

    # TODO: chat completion -> completion
    # this is the completion generated by "generate functions"
    content = completion["choices"][0]["message"]["content"]
    print(content)

    chat_history.append(ChatCompletionMessage(role="user", content=format_input))
    if alice_or_bob_state == "小红":
        chat_history.append(ChatCompletionMessage(role="assistant", content=content))
    else:
        chat_history.append(ChatCompletionMessage(role="assistant", content=content))

    return content


# ---------------------------------------- The program will run from below: ------------------------------------------#
if __name__ == "__main__":
    # define the starting address to launch the xoscar model,
    # for Using Http: supervisor_addr = "http://10.144.0.1:44935"
    # for Using local:supervisor_addr = "http://127.0.0.1:9997"

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-e", "--endpoint", type=str, help="Xinference endpoint, required", required=True
    )
    args = parser.parse_args()

    endpoint = args.endpoint
    model_a = "baichuan-chat"

    # Specify the model we need
    client = Client(endpoint)
    print(
        f"{emoji_rocket} 启动模型 {model_a}-1。初次下载需要的时间可能会比较长。"
    )
    model_a_uid = client.launch_model(
        model_name=model_a,
        model_format="pytorch",
        model_size_in_billions=13,
        quantization="int8",
    )
    model_a_ref = client.get_model(model_a_uid)
    print(
        f"{emoji_rocket} 启动模型 {model_a}-1。初次下载需要的时间可能会比较长。"
    )
    model_b_uid = client.launch_model(
        model_name=model_a,
        model_format="pytorch",
        model_size_in_billions=13,
        quantization="int8",
    )
    model_b_ref = client.get_model(model_b_uid)
    # ---------- program finally start! ------------ #
    # chat history to store every words each member is saying.
    chat_history = []
    alice_or_bob_state = "0"
    print("")
    print(emoji_jack_o_lantern, end="")
    print(" 欢迎来到 Xorbits inference 聊天室 ", end="")
    print(emoji_jack_o_lantern)
    print(emoji_sparkiles, end="")
    print(
        " 如果要退出聊天室，请说 '退出'，'离开', '再见', or '拜拜'",
        end=""
    )
    print(emoji_sparkiles)

    # Receive the username.
    print("")
    print(emoji_system, end="")
    welcome_prompt = ": 这位来宾，请告诉我你的名字: "
    text_to_audio(welcome_prompt, "0")
    username = input(welcome_prompt)

    # define names for the chatbots and create welcome message for chat-room.
    system_prompt_alice = (
        "这是一个充满好奇的人类用户和两个人工智能助手的聊天。人工智能助手们将对人类用户的问题提供有用的，详尽的，和有礼貌的回答。"
        "第一个人工智能助手的名字叫小红, 第二个人工智能助手的名字叫小花。"
        f"这位充满好奇的人类用户名字叫{username}"
    )
    system_prompt_bob = system_prompt_alice

    # We can change the scale of the model here, the bigger the model, the higher the accuracy
    # Due to the machine restrictions, I can only launch smaller model.
    model = whisper.load_model("medium")

    welcome_prompt2 = (
        f": 很高兴见到你, {username}。我们希望你能在未来速度推理聊天室与我们的两位"
        f"人工智能朋友度过一段难忘的聊天时光。随后，我们的系统将指引你选择和配置你的语音输入设备，请认真仔细阅读并完成。"
        f"我们希望你能享受这段不一样的快乐旅程。"
    )

    print("")
    print(emoji_system, end="")
    print(welcome_prompt2)
    text_to_audio(welcome_prompt2, "0")

    while True:
        audio_input = record_unlimited()

        start = time.time()
        format_input = format_prompt(model, audio_input)
        logger.info(f"Time spent on transcribing: {time.time() - start}")

        # set up the separation between each chat block.
        print("")
        print(emoji_user, end="")
        print(f" {username}:", end="")
        # format_input = input("type your prompt: ")
        print(format_input)

        # for un-natural exit audio inputs.
        if "离开" in format_input.lower() or "退出" in format_input.lower():
            break

        # for natural exit, both bot is expected to send greeting message.
        if "拜拜" in format_input.lower() or "再见" in format_input.lower():
            alice_or_bob_state = "小红"
            content_alice = f": 很高兴能与你交谈, {username}，再见！"
            print(emoji_women, end="")
            print(content_alice)
            text_to_audio(content_alice, alice_or_bob_state)
            alice_or_bob_state = "小花"
            content_bob = (
                f": 能与你交谈是我的荣幸, {username}. 希望能再次见到你！"
            )
            print(emoji_man, end="")
            print(content_bob)
            text_to_audio(content_bob, alice_or_bob_state)
            break

        system_prompt = system_prompt_alice
        # We choose to set Alice to default
        model_ref = model_a_ref

        # check whether alice and bob are both in the prompt and their position:
        def check_word_order(string, first_word, second_word) -> int:
            words = re.findall(
                r"\b\w+\b", string
            )  # Split the string into words, excluding punctuation

            if first_word in words and second_word in words:
                first_position = words.index(first_word)
                second_position = words.index(second_word)

                if first_position < second_position:
                    return 1
                if first_position > second_position:
                    return 2

            return -1  # Either of the words is not present in the string

        # if the user says alice first, we assume that the user want alice.
        if check_word_order(format_input.lower(), "小红", "小花") == 1:
            alice_or_bob_state = "小红"
            system_prompt = system_prompt_alice
            model_ref = model_a_ref
        # if bob is first, then we assume the user want bob.
        elif check_word_order(format_input.lower(), "小红", "小花") == 2:
            alice_or_bob_state = "小花"
            system_prompt = system_prompt_bob
            model_ref = model_b_ref
        # if not both of them presents, user says he wants to talk with Alice, we assign Alice, otherwise we assign Bob
        else:
            if "小红" in format_input.lower():
                alice_or_bob_state = "小红"
                system_prompt = system_prompt_alice
                model_ref = model_a_ref
            elif "小花" in format_input.lower():
                alice_or_bob_state = "小花"
                system_prompt = system_prompt_bob
                model_ref = model_b_ref
            # if both of them are not presents, if we don't have any assignment to agents,
            # we shall tell the user to do so
            else:
                if alice_or_bob_state == "0":
                    tips = ": 我们的人员已经准备就绪，请直接呼叫他们的名字与他们开始交谈吧。"
                    print(emoji_system, end="")
                    print(tips)
                    text_to_audio(tips, "0")
                    continue
        # call the chat function to chat with the bott=.
        content = chat_with_bot(
            format_input, chat_history, alice_or_bob_state, system_prompt, model_ref, username
        )

        text_to_audio(content, alice_or_bob_state)

    del chat_history
    bye_msg1 = (
        ": 感谢你关注我们未来速度公司的 Xinference 项目，并选择两位诞生于该项目的杰出人工智能工作人员"
    )
    bye_msg2 = (
        ": 我们会继续努力强化我们的已有的产品，并持续推出新产品，未来速度的目标始终是为大数据用户提供更好的产品与更广阔的平台"
    )
    print("\n")
    print(emoji_system, end="")
    print(bye_msg1)
    print(emoji_system, end="")
    print(bye_msg2)
    text_to_audio(bye_msg1, "0")
    text_to_audio(bye_msg2, "0")

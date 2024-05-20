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
import asyncio
import logging
import random
import time
from typing import List, Tuple

import numpy as np

from utils import generate_sorting_prompts, get_tokenizer, send_request


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REQUEST_LATENCY: List[Tuple[int, int, float]] = []


class BenchmarkRunner:

    def __init__(
        self,
        api_url: str,
        model_uid: str,
        input_requests: List[Tuple[str, int, int]],
        concurrency: int,
    ):

        self.api_url = api_url
        self.model_uid = model_uid
        self.input_requests = input_requests
        self.concurrency = concurrency
        self.sent = 0
        self.left = len(input_requests)

    async def run(self):
        tasks = []
        for i in range(0, self.concurrency):
            tasks.append(asyncio.create_task(self.worker(i)))
        await asyncio.gather(*tasks)

    async def worker(self, i: int):
        r = random.Random(i)
        index = r.randint(0, len(self.input_requests) - 1)
        while self.sent < len(self.input_requests):
            prompt, prompt_len, output_len = self.input_requests[index]
            index += 1
            self.sent += 1
            index = index % len(self.input_requests)
            await send_request(
                self.api_url,
                self.model_uid,
                prompt,
                prompt_len,
                output_len,
                REQUEST_LATENCY,
            )
            self.left -= 1
            # pring longer space to overwrite the previous when left decrease
            print("\rdone_request, left %d    " % (self.left), end="")
        # The last one
        print("")


def main(args: argparse.Namespace):
    if args.concurrency > args.num_prompts:
        print("Fix concurrency with num_prompts %d" % (args.num_prompts))
        args.concurrency = args.num_prompts
    print(args)

    api_url = f"http://{args.host}:{args.port}/v1/chat/completions"
    model_uid = args.model_uid

    logger.info("Preparing for benchmark.")
    tokenizer = get_tokenizer(args.tokenizer, trust_remote_code=args.trust_remote_code)
    # XXX: generate_sorting_prompts() currently only generate prompts 1/2 to 2/3 of context_length,
    # because tokenizers vary by models, consider improve in the future.
    input_requests = generate_sorting_prompts(
        args.concurrency, args.context_length, args.context_length / 2 - 20, tokenizer
    )

    logger.info("Benchmark starts.")
    benchmark_start_time = time.time()

    benchmark = BenchmarkRunner(
        api_url,
        model_uid,
        input_requests,
        concurrency=args.concurrency,
    )
    asyncio.run(benchmark.run())
    benchmark_end_time = time.time()
    benchmark_time = benchmark_end_time - benchmark_start_time
    print(f"Total time: {benchmark_time:.2f} s")
    print(f"Throughput: {args.num_prompts / benchmark_time:.2f} requests/s")

    # Compute the latency statistics.
    avg_latency = np.mean([latency for _, _, latency in REQUEST_LATENCY])
    print(f"Average latency: {avg_latency:.2f} s")
    avg_per_token_latency = np.mean(
        [
            latency / (prompt_len + output_len)
            for prompt_len, output_len, latency in REQUEST_LATENCY
        ]
    )
    print(f"Average latency per token: {avg_per_token_latency:.2f} s")
    avg_per_output_token_latency = np.mean(
        [latency / output_len for _, output_len, latency in REQUEST_LATENCY]
    )
    print("Average latency per output token: " f"{avg_per_output_token_latency:.2f} s")
    average_io_tokens = np.average(
        [(prompt_len + output_len) for prompt_len, output_len, _ in REQUEST_LATENCY]
    )
    print(f"Average io length:" f"{average_io_tokens}")
    throughput = (
        sum([output_len for _, output_len, _ in REQUEST_LATENCY]) / benchmark_time
    )
    print(f"Throughput: {throughput} tokens/s")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Benchmark the online serving throughput with long context."
    )
    parser.add_argument("--host", type=str, default="localhost")
    parser.add_argument("--port", type=int, default=9997)
    parser.add_argument(
        "--tokenizer", type=str, required=True, help="Name or path of the tokenizer."
    )
    parser.add_argument(
        "--context-length", type=int, default=32768, help="model context_length."
    )
    parser.add_argument(
        "--num-prompts", type=int, default=16, help="Number of prompts to process."
    )
    parser.add_argument(
        "--concurrency",
        "-c",
        type=int,
        default=16,
        help="Set the concurrency of request to send",
    )
    parser.add_argument(
        "--trust-remote-code",
        action="store_true",
        help="Trust remote code from huggingface.",
    )
    parser.add_argument("--model-uid", type=str, help="Xinference model UID.")
    args = parser.parse_args()
    main(args)

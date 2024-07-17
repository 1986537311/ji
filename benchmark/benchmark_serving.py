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
from typing import List, Tuple

import numpy as np

from utils import (
    ConcurrentBenchmarkRunner,
    sample_requests,
    get_tokenizer,
)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ServingBenchmarkRunner(ConcurrentBenchmarkRunner):
    def __init__(
        self,
        api_url: str,
        model_uid: str,
        input_requests: List[Tuple[str, int, int]],
        concurrency: int,
        request_rate: float,
    ):
        super().__init__(api_url, model_uid, input_requests, concurrency)
        self.request_rate = request_rate
        self.queue = asyncio.Queue(concurrency or 100)

    async def _run(self):
        tasks = []
        for req in iter(self.input_requests):
            await self.queue.put(req)

        for _ in range(self.concurrency):
            tasks.append(asyncio.create_task(self.worker()))

        await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

    async def worker(self):
        """
        wait request dispatch by run(), and then send_request.
        When all request is done, most worker will hang on self.queue,
        but at least one worker will exit"""
        while self.left > 0:
            request = await self.queue.get()
            await self.send_request(request)
            self.left -= 1
            print("\rdone_request, left %d    " % (self.left), end="")

            if self.request_rate != float("inf"):
                # If the request rate is infinity, then we don't need to wait.
                # Sample the request interval from the exponential distribution.
                interval = np.random.exponential(1.0 / self.request_rate)
                # The next request will be sent after the interval.
                await asyncio.sleep(interval)
        print("")


def main(args: argparse.Namespace):
    if args.concurrency > args.num_prompts:
        print("Fix concurrency with num_prompts %d" % (args.num_prompts))
        args.concurrency = args.num_prompts
    print(args)

    random.seed(args.seed)
    np.random.seed(args.seed)

    api_url = f"http://{args.host}:{args.port}/v1/chat/completions"
    model_uid = args.model_uid

    logger.info("Preparing for benchmark.")
    tokenizer = get_tokenizer(args.tokenizer, trust_remote_code=args.trust_remote_code)
    input_requests = sample_requests(
        args.dataset,
        args.num_prompts,
        tokenizer,
        prompt_len_limit=args.prompt_len_limit,
    )

    logger.info("Benchmark starts.")

    benchmark = ServingBenchmarkRunner(
        api_url,
        model_uid,
        input_requests,
        request_rate=args.request_rate,
        concurrency=args.concurrency,
    )
    asyncio.run(benchmark.run())

    benchmark.print_stats()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Benchmark the online serving throughput."
    )
    parser.add_argument("--host", type=str, default="localhost")
    parser.add_argument("--port", type=int, default=9997)
    parser.add_argument(
        "--dataset", type=str, required=True, help="Path to the dataset."
    )
    parser.add_argument(
        "--tokenizer", type=str, required=True, help="Name or path of the tokenizer."
    )
    parser.add_argument(
        "--num-prompts", type=int, default=100, help="Number of prompts to process."
    )
    parser.add_argument(
        "--prompt-len-limit", type=int, default=1024, help="Prompt length limitation."
    )
    parser.add_argument(
        "--concurrency",
        "-c",
        type=int,
        default=100,
        help="Set the concurrency of request to send",
    )
    parser.add_argument(
        "--request-rate",
        type=float,
        default=float("inf"),
        help="Number of requests per second. If this is inf, "
        "then all the requests are sent at time 0. "
        "Otherwise, we use Poisson process to synthesize "
        "the request arrival times.",
    )
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument(
        "--trust-remote-code",
        action="store_true",
        help="Trust remote code from huggingface.",
    )
    parser.add_argument("--model-uid", type=str, help="Xinference model UID.")
    args = parser.parse_args()
    main(args)

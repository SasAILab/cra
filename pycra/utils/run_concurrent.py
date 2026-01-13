import asyncio
from typing import Awaitable, Callable, List, Optional, TypeVar
from tqdm.asyncio import tqdm as tqdm_async
from pycra.utils.logger import logger

T = TypeVar("T")
R = TypeVar("R")

async def run_concurrent(
    coro_fn: Callable[[T], Awaitable[R]],
    items: List[T],
    *,
    desc: str = "processing",
    unit: str = "item",
) -> List[R]:
    tasks = [asyncio.create_task(coro_fn(it)) for it in items]

    completed_count = 0
    results = []

    pbar = tqdm_async(total=len(items), desc=desc, unit=unit)

    for future in asyncio.as_completed(tasks):
        try:
            result = await future
            results.append(result)
        except Exception as e:  # pylint: disable=broad-except
            logger.exception("Task failed: %s", e)
            # even if failed, record it to keep results consistent with tasks
            results.append(e)

        completed_count += 1
        pbar.update(1)
    pbar.close()

    # filter out exceptions
    results = [res for res in results if not isinstance(res, Exception)]

    return results

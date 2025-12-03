import asyncio
import random


async def coro_fn():
    val = random.randint(1, 30)
    print(f"sleeping for {val}")
    await asyncio.sleep(val)
    print("done")


async def main():
    # The task is created, but no reference is made to it.
    asyncio.create_task(coro_fn())
    # A reference is made, but the task is never awaited in the scope of main().
    # task = asyncio.create_task(coro_fn())
    # await task
    print("last")
    asyncio.create_task(coro_fn())


if __name__ == "__main__":
    asyncio.run(main(), debug=True)

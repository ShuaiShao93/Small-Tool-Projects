"""A script to showcase that coroutine never switch context if there is only compute and sync func, even if they are in nested async functions.

The printed outputs will be:

0 0
1 0
1 1
1 2
1 3
1 4
1 5
1 6
"""

import asyncio
import time

async def sync_sleep():
    x = 0
    for _ in range(10):
        x += 1
    # Change this to asyncio.sleep, we will see interleaved output
    time.sleep(1)

async def while_loop(idx, use_sync_sleep):
    i = 0
    while True:
        print(idx, i)
        i += 1
        if use_sync_sleep:
            await sync_sleep()
        else:
            await asyncio.sleep(1)
    
async def main():
    task0 = asyncio.create_task(while_loop(0, False))
    task1 = asyncio.create_task(while_loop(1, True))
    
    await asyncio.gather(task0, task1)


    
if __name__ == '__main__':
    asyncio.run(main())

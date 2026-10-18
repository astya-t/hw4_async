import asyncio
import time
import httpx
import requests

URLS = [f"https://picsum.photos/seed/{i}/800/600" for i in range(20)]

def timed(label, fn, *args):
    start = time.perf_counter()
    fn(*args)
    print(f"{label}: {time.perf_counter() - start:.2f}s")

# Задание 0. В цикле for каждый await fetch(...) ждёт, пока текущий запрос
# полностью завершится, и только потом цикл переходит к следующему URL.
# Запросы идут строго по очереди, время складывается (t1 + t2 + ... + t20).
# Слово async само по себе ничего не ускоряет: await подряд — это всё ещё 
# последовательно.
# Починка: все корутины запускаются одновременно через asyncio.gather,
# ожидания накладываются, время ≈ самому медленному запросу.
# follow_redirects=True нужен, т.к. picsum отвечает редиректом 302.

# Замеры:
#    slow  (await в цикле):   17.95 s
#    fixed (asyncio.gather):  7.46 s

async def fetch(client: httpx.AsyncClient, url: str) -> int:
    resp = await client.get(url)
    return resp.status_code
async def slow_main():
    async with httpx.AsyncClient(follow_redirects=True) as client:
         for url in URLS:
            await fetch(client, url) # <-- разобраться и починить

async def fixed_main():
    async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
        statuses = await asyncio.gather(*(fetch(client, url) for url in URLS))
    print("Статусы:", statuses)

timed("slow ", lambda: asyncio.run(slow_main()))
timed("fixed", lambda: asyncio.run(fixed_main()))

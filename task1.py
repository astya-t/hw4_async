import asyncio
import time
import httpx
import requests

URLS = [f"https://picsum.photos/seed/{i}/800/600" for i in range(20)]

def timed(label, fn, *args):
    start = time.perf_counter()
    fn(*args)
    print(f"{label}: {time.perf_counter() - start:.2f}s")

# Задание 1. Синхронно vs асинхронно
# Объяснение разницы:
# sync ждёт каждый ответ по очереди, и время складывается;
# async отправляет все запросы сразу, ожидания накладываются,
# и общее время ≈ времени самого медленного запроса.
# Замеры:
#    sync  (requests, по очереди):        68.59 s  
#    async (httpx.AsyncClient + gather):  6.75  s

async def fetch(client: httpx.AsyncClient, url: str) -> int:
    resp = await client.get(url)
    return resp.status_code

def sync_main():
    for url in URLS:
        requests.get(url, timeout=30) # по очереди, время складывается

async def fast_main():
    async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
        await asyncio.gather(*(fetch(client, url) for url in URLS))


if __name__ == "__main__":
    timed("sync ", sync_main)
    timed("async", lambda: asyncio.run(fast_main()))
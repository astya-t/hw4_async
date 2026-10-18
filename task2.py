# Задание 2. Реальный I/O и обработка ошибок

# Что сделано:
#  - Таймаут: timeout=8 на каждый запрос (httpx.TimeoutException,
#  если сервер не ответил за 8 с). 8 < 10, поэтому /delay/10 упадёт по таймауту.
#  5 с по умолчанию мало: при 20 одновременных соединениях picsum не успевал.
#  - Ретраи: не больше 3 попыток, пауза между ними растёт вдвое (1 с -> 2 с).
#  На последней попытке ошибка пробрасывается наверх.
#  Ошибки 4xx (кроме 429) не повторяются: повтор их не исправит.
#  - Устойчивость: asyncio.gather(..., return_exceptions=True) возвращает
#  исключения в общем списке, а не роняет всю пачку. robust_main
#  раскладывает их на (результаты, ошибки).

#  Битые адреса:
#  https://no-such-site.invalid — домена нет, ConnectError сразу, 3 попытки.
#  https://httpbin.org/delay/10 — отвечает 10 с, срабатывает таймаут,
#  3 попытки: 8 + 1 + 8 + 2 + 8 ≈ 27 с. Он и определяет общее время.

#  Замеры:
#  robust_main (20 картинок + 2 битых URL): 33.88 s
#  Успешно: 20, ошибок: 2


import asyncio
import time

import httpx
import requests

URLS = [f"https://picsum.photos/seed/{i}/800/600" for i in range(20)]
URLS += [
    "https://no-such-site.invalid",    
    "https://httpbin.org/delay/10",    
]

RETRIES = 3
TIMEOUT = 8


def timed(label, fn, *args):
    start = time.perf_counter()
    fn(*args)
    print(f"{label}: {time.perf_counter() - start:.2f}s")


async def robust_fetch(client: httpx.AsyncClient, url: str) -> int:
    for attempt in range(RETRIES):
        try:
            resp = await client.get(url, timeout=TIMEOUT)
            resp.raise_for_status()
            return resp.status_code
        except httpx.HTTPStatusError as e:
            code = e.response.status_code
            if 400 <= code < 500 and code != 429:
                raise                      
            error = e
        except httpx.HTTPError as e:         
            error = e

        if attempt == RETRIES - 1:
            raise error                     
        delay = 2 ** attempt                 
        print(f"{url}: попытка {attempt + 1} не удалась "
              f"({type(error).__name__}), жду {delay} с")
        await asyncio.sleep(delay)


async def robust_main():
    async with httpx.AsyncClient(follow_redirects=True) as client:
        outcomes = await asyncio.gather(
            *(robust_fetch(client, url) for url in URLS),
            return_exceptions=True,
        )

    results, errors = [], []
    for url, out in zip(URLS, outcomes):
        if isinstance(out, Exception):
            errors.append((url, f"{type(out).__name__}: {out}"))
        else:
            results.append((url, out))

    print(f"\nУспешно: {len(results)}, ошибок: {len(errors)}")
    for url, err in errors:
        print("  ОШИБКА", url, "->", err)
    return results, errors


if __name__ == "__main__":
    timed("robust", lambda: asyncio.run(robust_main()))
import os
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

SOURCE = "https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF/resolve/main/qwen2.5-3b-instruct-q4_k_m.gguf"
DEST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "qwen2.5-3b-instruct-q4_k_m.gguf")
CHUNK = 16 * 1024 * 1024
WORKERS = 8

head = urllib.request.urlopen(urllib.request.Request(SOURCE, method="HEAD"), timeout=60)
url = head.url
total = int(head.headers["Content-Length"])
count = (total + CHUNK - 1) // CHUNK
print(f"Downloading {total / 1024**3:.2f} GB in {count} chunks using {WORKERS} connections.", flush=True)

with open(DEST, "wb") as f:
    f.truncate(total)

def fetch(i):
    start = i * CHUNK
    end = min(total - 1, start + CHUNK - 1)
    req = urllib.request.Request(url, headers={"Range": f"bytes={start}-{end}"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=180) as response:
                data = response.read()
                if response.status != 206 or len(data) != end - start + 1:
                    raise RuntimeError(f"Bad range response for chunk {i}")
            with open(DEST, "r+b", buffering=0) as f:
                f.seek(start)
                f.write(data)
            return i
        except Exception:
            if attempt == 3:
                raise

done = 0
with ThreadPoolExecutor(max_workers=WORKERS) as pool:
    futures = [pool.submit(fetch, i) for i in range(count)]
    for future in as_completed(futures):
        future.result()
        done += 1
        if done % 4 == 0 or done == count:
            print(f"Completed {done}/{count} chunks ({done / count * 100:.0f}%).", flush=True)

print("MODEL DOWNLOAD COMPLETE:", round(os.path.getsize(DEST) / 1024**3, 2), "GB", flush=True)

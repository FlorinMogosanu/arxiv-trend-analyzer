import aiohttp
import asyncio
import threading
from bs4 import BeautifulSoup
from collections import Counter
import re
import os
import matplotlib.pyplot as plt
from datetime import datetime
import nltk
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

nltk.download("stopwords", quiet=True)
from nltk.corpus import stopwords

STOP_WORDS = set(stopwords.words("english"))

CATEGORIES    = ["cs.AI", "cs.LG", "cs.CV", "cs.CL", "cs.RO"]
N_GROUPS      = len(CATEGORIES)
PROCS_PER_GROUP = 4          # numărul de "workeri" simulați per grup

# ── chart output dir (creat de master, deci îl setăm global) ──────────────────
output_dir: str = ""
results_lock = threading.Lock()   # protejăm dicționarul de rezultate globale
all_results: dict[str, dict] = {}

start_time = time.time()


# ════════════════════════════════════════════════════════════════════════════════
# UTILITAR — identic cu varianta MPI
# ════════════════════════════════════════════════════════════════════════════════

async def _fetch_articles_async(category: str, retries: int = 3) -> list[str]:
    url    = f"https://arxiv.org/list/{category}/recent"
    params = {"skip": 0, "show": 2000}

    for attempt in range(1, retries + 1):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, params=params, timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status != 200:
                        raise aiohttp.ClientError(f"HTTP {response.status}")
                    html = await response.text()

            soup = BeautifulSoup(html, "lxml")
            articles = []
            for dd in soup.find_all("dd"):
                title   = dd.find("div", class_="list-title")
                subject = dd.find("span", class_="primary-subject")
                if title and subject:
                    articles.append(title.text.replace("Title:", "").strip())

            if not articles:
                raise ValueError(
                    "Niciun articol găsit — structura paginii s-ar putea fi schimbată"
                )
            return articles

        except Exception as e:
            print(f"[LEADER categorie={category}] Eroare la încercarea {attempt}/{retries}: {e}")
            if attempt < retries:
                await asyncio.sleep(2 * attempt)

    print(f"[LEADER categorie={category}] Toate încercările au eșuat, returnez listă goală")
    return []


def fetch_articles(category: str) -> list[str]:
    """Wrapper sincron pentru fetch async — fiecare thread are propriul event loop."""
    return asyncio.run(_fetch_articles_async(category))


def split_list(lst: list, n: int) -> list[list]:
    k = max(len(lst) // n, 1)
    return [
        lst[i * k : (i + 1) * k] if i < n - 1 else lst[i * k :]
        for i in range(n)
    ]


def extract_words(titles: list[str]) -> dict[str, int]:
    words = []
    for title in titles:
        clean = re.sub(r"[^a-zA-Z\s]", "", title)
        for word in clean.split():
            if word.lower() not in STOP_WORDS and len(word) > 2:
                words.append(word.lower())
    return dict(Counter(words))


def generate_chart(category: str, word_counts: dict[str, int]) -> None:
    if not word_counts:
        print(f"[MASTER] Niciun cuvânt pentru {category}, grafic omis")
        return

    top10 = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    labels, frequencies = zip(*top10)

    plt.figure(figsize=(10, 5))
    plt.bar(labels, frequencies, color="steelblue")
    plt.title(f"Top 10 cuvinte — arXiv {category}")
    plt.xlabel("Cuvinte")
    plt.ylabel("Frecvență")
    plt.xticks(rotation=45, ha="right")
    plt.ylim(0, max(frequencies) + 1)
    plt.tight_layout()

    filename = f"{output_dir}/{category.replace('.', '_')}.png"
    plt.savefig(filename)
    plt.close()
    print(f"[MASTER] Grafic salvat: {filename}")


# ════════════════════════════════════════════════════════════════════════════════
# WORKER — procesează un chunk de titluri (echivalentul unui proces non-leader)
# ════════════════════════════════════════════════════════════════════════════════

def worker_task(
    group_id: int,
    worker_id: int,
    chunk: list[str],
) -> dict[str, int]:
    tid = threading.current_thread().name
    print(f"[WORKER thread={tid} grup={group_id} worker={worker_id}] Procesez {len(chunk)} titluri")
    return extract_words(chunk)


# ════════════════════════════════════════════════════════════════════════════════
# LEADER — fetch + distribuie la workeri + agrega + trimite la master
# ════════════════════════════════════════════════════════════════════════════════

def leader_task(group_id: int, category: str) -> None:
    tid = threading.current_thread().name
    print(f"[LEADER thread={tid} grup={group_id}] Pornit pentru {category}")

    # 1. Fetch articole (echivalent asyncio.run din varianta MPI)
    articles = fetch_articles(category)
    print(
        f"[LEADER thread={tid} grup={group_id}] {category} — "
        f"{len(articles)} articole, împart la {PROCS_PER_GROUP} workeri"
    )

    # 2. Scatter — împarte lista în chunks și lansează workerii
    chunks = split_list(articles, PROCS_PER_GROUP)

    combined = Counter()
    with ThreadPoolExecutor(
        max_workers=PROCS_PER_GROUP,
        thread_name_prefix=f"worker_g{group_id}",
    ) as pool:
        futures = {
            pool.submit(worker_task, group_id, w_id, chunk): w_id
            for w_id, chunk in enumerate(chunks)
        }

        # 3. Gather — colectează rezultatele de la fiecare worker
        for future in as_completed(futures):
            worker_id = futures[future]
            try:
                partial = future.result()
                combined.update(partial)
            except Exception as e:
                print(
                    f"[LEADER grup={group_id}] Worker {worker_id} a eșuat: {e}"
                )

    print(
        f"[LEADER thread={tid} grup={group_id}] "
        f"{len(combined)} cuvinte unice combinate, trimit la master"
    )

    # 4. Send → scriere thread-safe în dicționarul global (înlocuiește comm.send)
    with results_lock:
        all_results[category] = dict(combined)


# ════════════════════════════════════════════════════════════════════════════════
# MASTER — lansează leaderii și procesează rezultatele
# ════════════════════════════════════════════════════════════════════════════════

def master() -> None:
    global output_dir

    total_threads = N_GROUPS * (PROCS_PER_GROUP + 1)   # 1 leader + N workeri per grup
    print(f"[MASTER] Pornit cu {total_threads} fire de execuție simulate ({PROCS_PER_GROUP} workeri per grup)")
    print("-" * 55)

    # Lansează câte un thread-leader pentru fiecare categorie
    leader_threads = []
    for group_id, category in enumerate(CATEGORIES):
        t = threading.Thread(
            target=leader_task,
            args=(group_id, category),
            name=f"leader_g{group_id}",
            daemon=True,
        )
        t.start()
        leader_threads.append(t)

    # Așteaptă toți leaderii (echivalent comm.recv din varianta MPI)
    for t in leader_threads:
        t.join()

    # Procesează și afișează rezultatele
    print("-" * 55)
    for category in CATEGORIES:
        result = all_results.get(category)
        if not result:
            print(f"[MASTER] {category} — date invalide, omis")
            continue
        top5 = sorted(result.items(), key=lambda x: x[1], reverse=True)[:5]
        print(f"[MASTER] {category} — top 5: {top5}")

    # Generează grafice
    output_dir = f"results/{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
    os.makedirs(output_dir, exist_ok=True)

    for category, word_counts in all_results.items():
        generate_chart(category, word_counts)

    elapsed = time.time() - start_time
    print("[MASTER] Gata!")
    print(f"[MASTER] Timp total: {elapsed:.2f} secunde")


# ════════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    master()
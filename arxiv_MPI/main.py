from mpi4py import MPI
import aiohttp
import asyncio
from bs4 import BeautifulSoup
from collections import Counter
import re
import os
import matplotlib.pyplot as plt
from datetime import datetime
import nltk
import time

nltk.download("stopwords", quiet=True)
from nltk.corpus import stopwords
STOP_WORDS = set(stopwords.words("english"))

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

CATEGORIES = ["cs.AI", "cs.LG", "cs.CV", "cs.CL", "cs.RO"]
N_GROUPS = len(CATEGORIES)
PROCS_PER_GROUP = (size - 1) // N_GROUPS
start_time = time.time()

async def fetch_articles(category, retries=3):
    url = f"https://arxiv.org/list/{category}/recent"
    params = {"skip": 0, "show": 2000}
    for attempt in range(1, retries + 1):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status != 200:
                        raise aiohttp.ClientError(f"HTTP {response.status}")
                    html = await response.text()

            soup = BeautifulSoup(html, "lxml")
            articles = []
            for dd in soup.find_all("dd"):
                title = dd.find("div", class_="list-title")
                subject = dd.find("span", class_="primary-subject")
                if title and subject:
                    articles.append(title.text.replace("Title:", "").strip())

            if not articles:
                raise ValueError("Niciun articol gasit — structura paginii s-ar putea fi schimbata")

            return articles

        except Exception as e:
            print(f"[LEADER categorie={category}] Eroare la incercarea {attempt}/{retries}: {e}")
            if attempt < retries:
                await asyncio.sleep(2 * attempt)

    print(f"[LEADER categorie={category}] Toate incercarile au esuat, returnez lista goala")
    return []

def split_list(lst, n):
    k = max(len(lst) // n, 1)
    return [lst[i*k : (i+1)*k] if i < n-1 else lst[i*k:] for i in range(n)]

def extract_words(titles):
    words = []
    for title in titles:
        clean = re.sub(r'[^a-zA-Z\s]', '', title)
        for word in clean.split():
            if word.lower() not in STOP_WORDS and len(word) > 2:
                words.append(word.lower())
    return dict(Counter(words))

def generate_chart(category, word_counts):
    if not word_counts:
        print(f"[MASTER] Niciun cuvant pentru {category}, grafic omis")
        return

    top10 = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    labels, frequencies = zip(*top10)

    plt.figure(figsize=(10, 5))
    plt.bar(labels, frequencies, color="steelblue")
    plt.title(f"Top 10 cuvinte — arXiv {category}")
    plt.xlabel("Cuvinte")
    plt.ylabel("Frecventa")
    plt.xticks(rotation=45, ha="right")
    plt.ylim(0, max(frequencies) + 1)
    plt.tight_layout()

    filename = f"{output_dir}/{category.replace('.', '_')}.png"
    plt.savefig(filename)
    plt.close()
    print(f"[MASTER] Grafic salvat: {filename}")

# ════════════════════════════════════════════════════════
if rank == 0:
    local_comm = comm.Split(color=MPI.UNDEFINED, key=0)
    print(f"[MASTER] Pornit cu {size} procese totale ({PROCS_PER_GROUP} procese per grup)")
    print("-" * 55)

    all_results = {}
    for group_id in range(N_GROUPS):
        leader_rank = group_id * PROCS_PER_GROUP + 1
        result = comm.recv(source=leader_rank)

        category = CATEGORIES[group_id]
        if not result:
            print(f"[MASTER] {category} — date invalide, omis")
            continue

        all_results[category] = result
        top10 = sorted(result.items(), key=lambda x: x[1], reverse=True)[:10]
        print(f"[MASTER] {category} — top 10: {top10}")

    print("-" * 55)

    # Creeaza folderul cu data si ora rularii
    output_dir = f"results/{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
    os.makedirs(output_dir, exist_ok=True)
    for category, word_counts in all_results.items():
        generate_chart(category, word_counts)

    elapsed = time.time() - start_time
    print("[MASTER] Gata!")
    print(f"[MASTER] Timp total: {elapsed:.2f} secunde")

else:
    group_id   = (rank - 1) // PROCS_PER_GROUP
    local_rank = (rank - 1)  % PROCS_PER_GROUP
    local_comm = comm.Split(color=group_id, key=local_rank)
    category   = CATEGORIES[group_id]

    # Leaderul fetch-uieste si pregateste chunks
    if local_rank == 0:
        articles = asyncio.run(fetch_articles(category))
        print(f"[LEADER grup={group_id}] {category} — {len(articles)} articole, impart la {PROCS_PER_GROUP} procese")
        chunks = split_list(articles, PROCS_PER_GROUP)
    else:
        chunks = None

    # Scatter — leaderul distribuie, workerii primesc
    my_chunk = local_comm.scatter(chunks, root=0)
    print(f"[proc rank={rank} grup={group_id}] Procesez {len(my_chunk)} titluri")

    # Fiecare proces extrage cuvintele din bucata lui
    my_words = extract_words(my_chunk)

    # Gather — toata lumea trimite rezultatul la leader
    all_word_dicts = local_comm.gather(my_words, root=0)

    # Leaderul combina si trimite la master
    if local_rank == 0:
        combined = Counter()
        for d in all_word_dicts:
            combined.update(d)
        print(f"[LEADER grup={group_id}] {len(combined)} cuvinte unice combinate, trimit la master")
        comm.send(dict(combined), dest=0)
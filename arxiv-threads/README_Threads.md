# arXiv Trend Analyzer — Parallel Version (Threads)

A parallel web scraping application that extracts and analyzes the most frequent words from scientific article titles on [arXiv](https://arxiv.org), using inter-thread communication via Python's `threading` and `concurrent.futures` modules.

---

## Technologies

| Library | Role |
|---|---|
| `threading` | Thread creation and synchronization (Lock, Thread) |
| `concurrent.futures` | `ThreadPoolExecutor` — parallel worker management with scatter/gather pattern |
| `aiohttp` | Asynchronous HTTP client for efficient parallel requests |
| `beautifulsoup4` | Parsing and extracting data from HTML |
| `lxml` | Fast parser for HTML/XML documents |
| `matplotlib` | Generating charts from the final results |
| `nltk` | Removing common words (stopwords) |

---

## Architecture

The program uses **Python threads** — each arXiv category is processed by a dedicated leader thread that manages a pool of worker threads working in parallel.

```
Main Thread (Master)
│
├── Leader Thread 0 — cs.AI  │ leader + N worker threads
├── Leader Thread 1 — cs.LG  │ leader + N worker threads
├── Leader Thread 2 — cs.CV  │ leader + N worker threads
├── Leader Thread 3 — cs.CL  │ leader + N worker threads
└── Leader Thread 4 — cs.RO  │ leader + N worker threads
```

### Data flow within a group

```
Leader Thread (per category)
  │
  ├─ HTTP fetch  → retrieves all articles for the category (asyncio.run)
  ├─ scatter     → distributes article chunks to ThreadPoolExecutor workers
  │
  │   [each worker thread extracts words from its chunk]
  │
  ├─ gather      → collects partial results via as_completed()
  ├─ combine     → merges all Counters
  └─ send        → writes final result to shared dict (protected by Lock)
```

### MPI → Threads equivalence

| MPI concept | Thread equivalent |
|---|---|
| `MPI.COMM_WORLD` + `rank` | `threading.Thread` + `ThreadPoolExecutor` |
| `comm.Split(color=group_id)` | One leader thread per category |
| `local_comm.scatter(chunks, root=0)` | `pool.submit(worker_task, ..., chunk)` |
| `local_comm.gather(my_words, root=0)` | `as_completed(futures)` + `Counter.update()` |
| `comm.send(dict, dest=0)` | Write to shared `all_results` dict with `threading.Lock` |
| `comm.recv(source=leader_rank)` | `leader_thread.join()` |

---

## System Requirements

- **Python** 3.10 or newer
- No external MPI runtime required — standard library only for parallelism

---

## Installation

**1. Clone the repository**
```bash
git clone <repository-url>
cd arxiv-trend-analyzer/arxiv_Threads
```

**2. Install Python dependencies**
```bash
pip install -r requirements.txt
```

---

## Running

Thread count formula:
```
total threads = 1 master + 5 groups × (1 leader + N workers/group)
```

**Default configuration** (`PROCS_PER_GROUP = 4`, i.e. 4 workers per group):
```bash
python main.py
```

**Adjusting parallelism** — edit `PROCS_PER_GROUP` in `main.py`:

| Workers/group | Total threads | Constant to set |
|---|---|---|
| 2 | 1 + 5×3 = 16 | `PROCS_PER_GROUP = 2` |
| 4 | 1 + 5×5 = 26 | `PROCS_PER_GROUP = 4` |
| 8 | 1 + 5×9 = 46 | `PROCS_PER_GROUP = 8` |

> Unlike MPI, Python threads share the same process and are subject to the **GIL (Global Interpreter Lock)**. For CPU-bound tasks this limits true parallelism, but since the bottleneck here is I/O (HTTP requests), threads remain effective. For CPU-bound workloads, consider switching `ThreadPoolExecutor` to `ProcessPoolExecutor`.

**Check your logical core count:**

```bash
# Linux / macOS
nproc

# Windows PowerShell
(Get-CimInstance Win32_Processor).NumberOfLogicalProcessors
```

---

## Output

After running, a `results/` folder is created automatically with the following structure:

```
results/
  2026-04-27_14-32-10/
      cs_AI.png
      cs_LG.png
      cs_CV.png
      cs_CL.png
      cs_RO.png
```

Each chart shows the **top 10 most frequent words** found in article titles for that category.

---

## Analyzed arXiv Categories

| Category | Description |
|---|---|
| `cs.AI` | Artificial Intelligence |
| `cs.LG` | Machine Learning |
| `cs.CV` | Computer Vision |
| `cs.CL` | Computation and Language |
| `cs.RO` | Robotics |

---

## Performance Benchmarks

Measured with `PROCS_PER_GROUP = 4` (4 worker threads per group, 26 threads total), 5 categories scraped in parallel.

| Data | Run | Time (s) |
|---|---|----------|
| 100 articles / category | Run 1 | 1.48     |
| 100 articles / category | Run 2 | 1.48     |
| 100 articles / category | Run 3 | 1.40     |
| 100 articles / category | **Average** | 1.45     |
| 500 articles / category | Run 1 | 3.26     |
| 500 articles / category | Run 2 | 3.39     |
| 500 articles / category | Run 3 | 3.28     |
| 500 articles / category | **Average** | 3.31     |
| 1000 articles / category | Run 1 | 4.24     |
| 1000 articles / category | Run 2 | 5.56     |
| 1000 articles / category | Run 3 | 4.16     |
| 1000 articles / category | **Average** | 4.65     |
| 2000 articles / category | Run 1 | 4.21     |
| 2000 articles / category | Run 2 | 4.50     |
| 2000 articles / category | Run 3 | 4.33     |
| 2000 articles / category | **Average** | 4.34     |

> Speedup is limited by network latency (I/O bottleneck) — all leader threads send HTTP requests simultaneously, but the slowest response from arXiv dictates the total execution time. Additionally, Python's GIL prevents true CPU parallelism for the word-extraction phase; however, since the workload is I/O-dominant, this has negligible impact in practice.

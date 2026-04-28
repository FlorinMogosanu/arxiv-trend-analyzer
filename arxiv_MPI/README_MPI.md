# arXiv Trend Analyzer — Parallel Version (MPI)

A parallel web scraping application that extracts and analyzes the most frequent words from scientific article titles on [arXiv](https://arxiv.org), using inter-process communication via MPI.

---

## Technologies

| Library | Role |
|---|---|
| `mpi4py` | Inter-process communication via MPI (scatter, gather, send, recv) |
| `aiohttp` | Asynchronous HTTP client for efficient parallel requests |
| `beautifulsoup4` | Parsing and extracting data from HTML |
| `lxml` | Fast parser for HTML/XML documents |
| `matplotlib` | Generating charts from the final results |
| `nltk` | Removing common words (stopwords) |
| `pandas` | Structuring collected data |

---

## Architecture

The program uses **MPI sub-communicators** — each arXiv category is processed by a dedicated group of processes working in parallel.

```
COMM_WORLD (26 processes)
│
├── Master (rank 0)
│     Global coordinator — collects results
│     and generates the final charts
│
├── Group 0 — cs.AI  │ rank 0 (leader) + N workers
├── Group 1 — cs.LG  │ rank 0 (leader) + N workers
├── Group 2 — cs.CV  │ rank 0 (leader) + N workers
├── Group 3 — cs.CL  │ rank 0 (leader) + N workers
└── Group 4 — cs.RO  │ rank 0 (leader) + N workers
```

### Data flow within a group

```
Leader (local rank 0)
  │
  ├─ HTTP fetch  → retrieves all articles for the category
  ├─ scatter     → distributes articles to workers
  │
  │   [each worker extracts words from its chunk]
  │
  ├─ gather      → collects partial results
  ├─ combine     → merges all Counters
  └─ send        → sends the final result to Master
```

---

## System Requirements

- **Python** 3.10 or newer
- **MS-MPI** (Windows) — download `msmpisetup.exe` and `msmpisdk.msi` from:
  https://github.com/microsoft/Microsoft-MPI/releases/latest

> Install `msmpisetup.exe` first, then `msmpisdk.msi`.

---

## Installation

**1. Clone the repository**
```bash
git clone <repository-url>
cd arxiv-trend-analyzer/arxiv_MPI
```

**2. Install Python dependencies**
```bash
py -m pip install -r requirements.txt
```

**3. Verify MPI installation**
```bash
mpiexec -n 4 py test_mpi.py
```
You should see 4 messages, one from each process.

---

## Running

Process count formula:
```
total processes = 1 master + 5 groups × N processes/group
```

**Recommended for 16 logical cores** (3 processes/group):
```bash
mpiexec -n 16 py main.py
```

**Other configurations:**

| Processes/group | Command | Total processes |
|---|---|---|
| 2 | `mpiexec -n 11 py main.py` | 11 |
| 3 | `mpiexec -n 16 py main.py` | 16 |
| 4 | `mpiexec -n 21 py main.py` | 21 |

> Do not exceed the number of available logical cores — extra processes will compete for the same resources and may slow down execution.

**Check your logical core count (Windows PowerShell):**
```powershell
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

Measured with **16 processes** (`mpiexec -n 16`), 5 categories scraped in parallel.

| Data | Run | Time (s) |
|---|---|----------|
| 100 articles / category | Run 1 | 2.61     |
| 100 articles / category | Run 2 | 1.82     |
| 100 articles / category | Run 3 | 1.96     |
| 100 articles / category | **Average** | 2.34     |
| 500 articles / category | Run 1 | 2.18     |
| 500 articles / category | Run 2 | 2.36     |
| 500 articles / category | Run 3 | 2.37     |
| 500 articles / category | **Average** | 2.30     |
| 1000 articles / category | Run 1 | 3.64     |
| 1000 articles / category | Run 2 | 2.42     |
| 1000 articles / category | Run 3 | 2.64     |
| 1000 articles / category | **Average** | 2.90     |
| 2000 articles / category | Run 1 | 3.43     |
| 2000 articles / category | Run 2 | 2.55     |
| 2000 articles / category | Run 3 | 2.52     |
| 2000 articles / category | **Average** | 2.83     |

> Speedup is limited by network latency (I/O bottleneck) — all groups send HTTP requests simultaneously, but the slowest response from arXiv dictates the total execution time.
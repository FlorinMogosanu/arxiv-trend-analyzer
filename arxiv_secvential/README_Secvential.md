# arXiv Trend Analyzer — Sequential Version

A sequential web scraping application that extracts and analyzes the most frequent words from scientific article titles on [arXiv](https://arxiv.org), processing each category one at a time.

---

## Technologies

| Library | Role |
|---|---|
| `requests` | HTTP client for fetching arXiv pages |
| `beautifulsoup4` | Parsing and extracting data from HTML |
| `nltk` | Removing common words (stopwords) |
| `pandas` | Structuring collected data |
| `matplotlib` | Generating charts from the final results |

---

## How It Works

The program processes each arXiv category sequentially — one after another. For each category it fetches the page, parses the article titles, extracts the most frequent words, and saves a chart.

```
For each category:
  │
  ├─ HTTP fetch   → retrieves all articles for the category
  ├─ parse HTML   → extracts titles from the page
  ├─ extract words → filters stopwords, counts frequency
  └─ save chart   → saves top 10 words as a .png file
```

---

## System Requirements

- **Python** 3.10 or newer

---

## Installation

**1. Clone the repository**
```bash
git clone <repository-url>
cd arxiv-trend-analyzer/arxiv_secvenital
```

**2. Install Python dependencies**
```bash
py -m pip install -r requirements.txt
```

---

## Running

```bash
py main.py
```

---

## Output

After running, a `results/` folder is created automatically with the following structure:

```
results/
  2026-04-27_14-32-10/
      cs.AI.png
      cs.LG.png
      cs.CV.png
      cs.CL.png
      cs.RO.png
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

| Data | Run | Time (s) |
|---|---|----------|
| 100 articles / category | Run 1 | 4.67     |
| 100 articles / category | Run 2 | 3.48     |
| 100 articles / category | Run 3 | 3.66     |
| 100 articles / category | **Average** | 3.93     |
| 500 articles / category | Run 1 | 5.39     |
| 500 articles / category | Run 2 | 5.33     |
| 500 articles / category | Run 3 | 5.25     |
| 500 articles / category | **Average** | 5.32     |
| 1000 articles / category | Run 1 | 5.89     |
| 1000 articles / category | Run 2 | 6.06     |
| 1000 articles / category | Run 3 | 6.01     |
| 1000 articles / category | **Average** | 5.98     |
| 2000 articles / category | Run 1 | 6.36     |
| 2000 articles / category | Run 2 | 8.81     |
| 2000 articles / category | Run 3 | 6.59     |
| 2000 articles / category | **Average** | 7.25     |

# ArXiv Trend Analyzer

**Proiect Algoritmi Paraleli și Distribuiți**  
**Student:** Mogosanu Florin  
**Grupa:** CR 3.3A

---

## Tema

**Tema 4: Web Scraping**  
Paralelizarea cererilor HTTP și analiza conținutului HTML permite un scraping mai eficient al site-urilor web.

---

## Descriere

ArXiv Trend Analyzer este un scraper web care colectează titluri de articole științifice de pe arXiv, analizează frecvența cuvintelor cheie și vizualizează topicurile în trend printr-un grafic.

---

## Tehnologii și librării utilizate

| Librărie | Descriere |
|----------|-----------|
| `requests` | Cereri HTTP secvențiale |
| `aiohttp` | Client HTTP asincron pentru cereri paralele eficiente |
| `mpi4py` | Interfață Python pentru comunicare între procese MPI |
| `BeautifulSoup4` | Parsarea și extragerea datelor din HTML |
| `lxml` | Parser rapid și eficient pentru documente HTML/XML |
| `pandas` | Structurarea, procesarea și exportul datelor colectate |
| `nltk` | Eliminarea stopwords |
| `matplotlib` | Generarea graficului bar chart |
| `json` | Serializarea și salvarea rezultatelor în format JSON |

---

## Configurație hardware și software

| Componentă | Detalii |
|------------|---------|
| Sistem de operare | Windows 11 |
| Procesor | AMD Ryzen 7 7730U |
| Memorie RAM | 16GB |
| Versiune Python | 3.13.2 |
| Mediu virtual | venv |

---

## Rezultate experimentale


| Data | Secvenital  | MPI | Threads |
|---|-------------|----|---------|
| 100 articles / category | 3.93 | 2.34 | 1.45    |
| 500 articles / category | 5.32 | 2.30 | 3.31    |
| 1000 articles / category | 5.98 | 2.90 | 4.65    |
| 2000 articles / category | 7.25  | 2.83   | 4.34 |

---
The benchmark results indicate that MPI consistently outperforms both the sequential and threaded implementations, maintaining stable execution times between 2.30s and 2.90s regardless of article volume. Threads perform competitively at low data volumes (1.45s at 100 articles) but degrade significantly as workload increases, exposing the inherent limitations of Python's GIL on CPU-bound tasks such as regex processing and frequency counting.
It is worth noting that a substantial portion of total execution time is attributable to the HTTP GET request latency towards arXiv's servers — an external factor that no parallelization strategy can fully eliminate. This network bottleneck explains the relatively narrow performance gap between all three variants, as the slowest server response effectively dictates the minimum achievable runtime. Consequently, the true benefit of parallelism manifests primarily in the data processing phase, where MPI's process-level isolation enables genuine multi-core utilization, while Python threads remain constrained by the GIL.
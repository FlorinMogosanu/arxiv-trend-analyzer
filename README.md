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

## Rezultate experimentale — Varianta secvențială

| Rulare | Timp (s) |
|--------|----------|
| 1 | 1.34 |
| 2 | 1.36 |
| 3 | 1.56 |
| **Medie** | **1.42** |
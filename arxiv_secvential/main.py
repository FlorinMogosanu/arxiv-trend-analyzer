import requests
import time
import os
import re
import pandas as pd
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
from nltk.corpus import stopwords
from collections import Counter
from datetime import datetime

stop_words = set(stopwords.words("english"))

CATEGORIES = ["cs.AI", "cs.LG", "cs.CV", "cs.CL", "cs.RO"]


def fetch_page(category_url, par=None):
    result = requests.get(category_url, params=par)
    html_soup = BeautifulSoup(result.text, "html.parser")
    return html_soup


def parse_articles(html_soup):
    articles_list = []
    all_articles = html_soup.find_all("dd")
    for article in all_articles:
        title   = article.find("div", class_="list-title")
        authors = article.find_all("a")
        subject = article.find("span", class_="primary-subject")
        if title and authors and subject:
            articles_list.append({
                "title":   title.text.replace("Title:", "").strip(),
                "authors": [a.text for a in authors],
                "subject": subject.text.strip(),
            })
    return pd.DataFrame(articles_list)


def extract_words(df):
    titles = df["title"].tolist()
    words_list = []
    for title in titles:
        title = re.sub(r'[^a-zA-Z\s]', '', title)
        local_words = title.split()
        for word in local_words:
            if word not in stop_words and len(word) > 2:
                words_list.append(word.lower())
    return words_list


def generate_chart(words_list, category, run_folder):
    top_10_words = Counter(words_list).most_common(10)

    labels      = [w[0] for w in top_10_words]
    frequencies = [w[1] for w in top_10_words]

    plt.figure(figsize=(10, 6))
    plt.bar(labels, frequencies)
    plt.title(f"Top 10 words from arXiv {category} titles")
    plt.xlabel("Words")
    plt.ylabel("Frequency")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.ylim(0, max(frequencies) + 1)

    filename = os.path.join(run_folder, f"{category}.png")
    plt.savefig(filename)
    plt.close()
    print(f"  Chart salvat: {filename}")


if __name__ == "__main__":
    total_start = time.time()

    params = {
        "skip": 0,
        "show": 2000,
    }

    run_folder = os.path.join("results", datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
    os.makedirs(run_folder, exist_ok=True)
    print(f"Charturile vor fi salvate în: {run_folder}/")

    for i, category in enumerate(CATEGORIES, start=1):
        print(f"\n[{i}/{len(CATEGORIES)}] Se procesează categoria: {category}")
        cat_start = time.time()

        url      = f"https://arxiv.org/list/{category}/recent"
        soup     = fetch_page(url, par=params)
        articles = parse_articles(soup)

        print(f"  Articole găsite: {len(articles)}")

        words = extract_words(articles)
        generate_chart(words, category, run_folder)

        print(f"  Timp categorie: {time.time() - cat_start:.2f} secunde")

    print(f"\nFinalizat! Timp total: {time.time() - total_start:.2f} secunde")
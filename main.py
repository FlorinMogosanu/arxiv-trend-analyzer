import requests
from bs4 import BeautifulSoup
import pandas as pd
from nltk.corpus import stopwords
import re
from collections import Counter
import matplotlib.pyplot as plt
from datetime import datetime
import os
stop_words = set(stopwords.words("english"))

def fetch_page(category_url):
    result = requests.get(category_url)
    html_soup = BeautifulSoup(result.text, "html.parser")
    return html_soup


def parse_articles(html_soup):
    articles_list = []
    all_articles = html_soup.find_all("dd")
    for article in all_articles:
        title = article.find("div", class_="list-title")
        authors = article.find_all("a")
        subject = article.find("span", class_="primary-subject")
        if title and authors and subject:
            articles_list.append({"title": title.text.replace("Title:", "").strip(), "authors": [a.text for a in authors], "subject": subject.text.strip()})
    return pd.DataFrame(articles_list)

# Keep going creating functions.

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

def generate_chart(words_list):
    top_10_words = Counter(words_list).most_common(10)

    labels = []
    frequencies = []

    for word in top_10_words:
        labels.append(word[0])
        frequencies.append(word[1])

    plt.bar(labels, frequencies)
    plt.title("Top 10 words from arXiv cs.AI titles")
    plt.xlabel("Words")
    plt.ylabel("Frequency")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.ylim(0, max(frequencies) + 1)
    os.makedirs("results", exist_ok=True)
    plt.savefig(f"results/{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.png")
    plt.show()

if __name__ == "__main__":
    url = "https://arxiv.org/list/cs.AI/recent"
    soup = fetch_page(url)
    articles = parse_articles(soup)
    articles.to_csv("articles.csv", index=False)
    words = extract_words(articles)
    generate_chart(words)



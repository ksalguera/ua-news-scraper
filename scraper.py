import requests
from bs4 import BeautifulSoup

ROOT_URL = "https://www.unionarena-tcg.com"
NEWS_URL = f"{ROOT_URL}/na/news/"

def clean_url(url):
    url = url.replace("/na/news//na/news/", "/na/news/")
    
    if not url.startswith("http"):
        url = ROOT_URL + url
    
    return url

def fetch_latest_articles():
    try:
        response = requests.get(NEWS_URL)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        articles = soup.select("ul.newsBox li.newsDetail")

        article_data = []
        for article in articles:
            link = article.find("a").get("href")
            date = article.select_one("dd.newsDate").text.strip()
            if link:
                link = clean_url(link)
            article_data.append({"link": link, "date": date})

        return article_data
    except Exception as e:
        print(f"Error fetching articles: {e}")
        return []

# local testing
if __name__ == "__main__":
    articles = fetch_latest_articles()
    print("Fetched Articles:")
    for article in articles:
        print(article)

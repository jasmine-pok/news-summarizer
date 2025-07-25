from dotenv import load_dotenv
import os
import requests
from bs4 import BeautifulSoup
import openai

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def scrape_hackernews_articles(limit=5):
    url = "https://news.ycombinator.com/"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    links = soup.select(".titleline > a")
    articles = []

    for link in links[:limit]:
        title = link.get_text()
        href = link['href']
        articles.append({"title": title, "url": href})

    return articles 

openai.api_key = OPENAI_API_KEY

def summarize_text(text):
    prompt = f"Summarize the following article:\n\n{text}\n\nSummary:"

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You're a helpful assistant that summarizes articles."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150
        )

        summary = response['choices'][0]['message']['content'].strip()
        return summary
    except Exception as e:
        return f"Error: {e}"
    
if __name__ == "__main__":
    articles = scrape_hackernews_articles(limit=3)

    for article in articles:
        print(f"\n Title: {article['title']}")
        print(f"URL: {article['url']}")

        summary = summarize_text(article['title'])
        print(f"Summary: {summary}")

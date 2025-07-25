from dotenv import load_dotenv
import os
import requests
from bs4 import BeautifulSoup
import openai
import psycopg2

# env vars
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

openai.api_key = OPENAI_API_KEY

def get_db_connection():
    print(f"Connecting to {DB_NAME} at {DB_HOST}:{DB_PORT} as {DB_USER}")
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )

def scrape_hackernews_articles(limit=5):
    url = "https://news.ycombinator.com/"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    links = soup.select(".titleline > a")
    articles = []

    for link in links[:limit]:
        title = link.get_text()
        href = link['href']
        content = extract_article_text(href)
        articles.append({"title": title, "url": href, "content": content})

    return articles 

def extract_article_text(article_url):
    try:
        response = requests.get(article_url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        # Get visible text from paragraphs (common structure for articles)
        paragraphs = soup.find_all('p')
        article_text = "\n".join(p.get_text() for p in paragraphs)

        # Limit the length for token efficienty
        return article_text[:3000]
    
    except Exception as e:
        return f"Failed to extract article: {e}"


def summarize_text(text):
    prompt = f"Summarize the following article:\n\n{text}\n\nSummary:"

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You're a helpful assistant that summarizes articles."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300
        )

        summary = response['choices'][0]['message']['content'].strip()
        return summary
    except Exception as e:
        return f"Error: {e}"
    
def insert_article_to_db(article):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO ARTICLES (url, title, content, summary)
            VALUES (%s, %s, %s, %s);
            """,
            (article['url'], article['title'], article['content'], article['summary'])
        )
        conn.commit()
        cur.close()
        conn.close()

    except Exception as e:
        print(f"Failed to insert article: {e}")
    
if __name__ == "__main__":
    articles = scrape_hackernews_articles(limit=3)

    for article in articles:
        print(f"\n Title: {article['title']}")
        print(f"URL: {article['url']}\n")

        if "Failed to extract" in article["content"]:
            print(f"Could not extract content: {article['content']}")
            continue

        summary = summarize_text(article['content'])
        article["summary"] = summary

        print(f"Summary: {summary[:200]}...")

        insert_article_to_db(article)
        print(f"Inserted into database.")

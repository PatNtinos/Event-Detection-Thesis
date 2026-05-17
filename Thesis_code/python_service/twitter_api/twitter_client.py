import os
import requests
from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv()


WEBZ_API_KEY = os.getenv("WEBZ_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")


# ========================
# COMMON EVENT FORMAT
# ========================
def normalize_event(source, source_id, text, created_at=None, lang=None, url=None):
    return {
        "source": source,
        "source_id": source_id,
        "text": text,
        "created_at": created_at,
        "lang": lang,
        #"url": url
    }


# ========================
# REDDIT FETCHER
# ========================
def fetch_reddit(limit=50):
    url = "https://www.reddit.com/r/news.json"
    headers = {"User-Agent": "event-pipeline-test"}

    try:
        response = requests.get(url, headers=headers, params={"limit": limit})

        if response.status_code != 200:
            print(f"⚠️ Reddit error {response.status_code}")
            return []

        data = response.json()

        events = []
        for post in data["data"]["children"]:
            p = post["data"]

            events.append(normalize_event(
                source="reddit",
                source_id=p["id"],
                text=p.get("title"),
                created_at=datetime.now(timezone.utc).isoformat(),
    #            url=p.get("url"),
                lang="en"  # safe assumption for r/news
            ))

        return events

    except Exception as e:
        print(f"⚠️ Reddit failed: {e}")
        return []





# ========================
# WEBZ.io FETCHER
# ========================
def fetch_webz(limit=10):

    url = "https://api.webz.io/newsApiLite"

    params = {
        "token": WEBZ_API_KEY,

        # GOOD generic event query
        "q": (
            "earthquake OR disaster OR war "
            "OR emergency "
            "OR news"
        ),

        "size": limit
    }

    try:
        response = requests.get(url, params=params)

        if response.status_code != 200:
            print(f"⚠️ Webz error {response.status_code}")
            return []

        data = response.json()

        events = []

        # IMPORTANT:
        # Webz articles are inside "posts"
        for post in data.get("posts", []):

            thread = post.get("thread", {})

            events.append(normalize_event(
                source="webz.io",
                source_id=thread.get("uuid"),
                text=thread.get("title"),
                created_at=datetime.now(timezone.utc).isoformat(),
                lang=post.get("language", "en")
            ))

        return events

    except Exception as e:
        print(f"⚠️ Webz failed: {e}")
        return []




# ========================
# NEWS API FETCHER
# ========================
def fetch_newsapi(limit=50):

    url = "https://newsapi.org/v2/everything"

    params = {

        "q": (
            "earthquake OR disaster OR war "
            "OR protest OR environment OR sports "
            "OR outbreak OR emergency "
            "OR news OR  breaking "
        ),

        "language": "en",

        "sortBy": "publishedAt",

        "pageSize": limit,

        "apiKey": NEWS_API_KEY
    }

    try:
        response = requests.get(url, params=params)

        if response.status_code != 200:
            print(f"⚠️ NewsAPI error {response.status_code}")
            print(response.text)
            return []

        data = response.json()

        events = []

        for article in data.get("articles", []):

            # Skip empty titles
            if not article.get("title"):
                continue

            events.append(normalize_event(
                source="newsapi",
                source_id=article.get("url"),
                text=article.get("title"),
                created_at=datetime.now(timezone.utc).isoformat(),
                lang="en"
                #url=article.get("url")
            ))

        return events

    except Exception as e:
        print(f"⚠️ NewsAPI failed: {e}")
        return []





# ========================
# NEWSDATA FETCHER
# ========================
def fetch_newsdata(limit=20):
    api_key = os.getenv("NEWSDATA_API_KEY")

    url = "https://newsdata.io/api/1/latest"

    params = {
        "apikey": api_key,

        # Event-oriented keywords
        "q": (
            "earthquake OR disaster OR war "
            "OR emergency "
            "OR news"
        ),

        # English only
        "language": "en"
    }

    try:
        response = requests.get(url, params=params)

        if response.status_code != 200:
            print(f"⚠️ NewsData error {response.status_code}")
            return []

        data = response.json()

        events = []

        for article in data.get("results", [])[:limit]:

            # Skip duplicates
            if article.get("duplicate") is True:
                continue

            events.append(normalize_event(
                source="newsdata",
                source_id=article.get("article_id"),
                text=article.get("title"),
                created_at=datetime.now(timezone.utc).isoformat(),
                lang="en"
            ))

        return events

    except Exception as e:
        print(f"⚠️ NewsData failed: {e}")
        return []



# ========================
# CURRENTS API FETCHER
# ========================
def fetch_currents(limit=50):
    api_key = os.getenv("CURRENTS_API_KEY")

    url = "https://api.currentsapi.services/v1/latest-news"

    params = {
        "language": "en",
        "page_size": limit,
        "apiKey": api_key,
        "order-by": "newest",
        "q": (
            "earthquake OR disaster OR war "
            "OR protest OR environment OR sports "
            "OR outbreak OR emergency "
            "OR news OR  breaking "
            
        )
    }

    try:
        response = requests.get(url, params=params)

        if response.status_code != 200:
            print(f"⚠️ Currents API error {response.status_code}")
            return []

        data = response.json()

        events = []

        for article in data.get("news", []):

            events.append(normalize_event(
                source="currents",
                source_id=article.get("id"),
                text=article.get("title"),
                created_at=datetime.now(timezone.utc).isoformat(),
                lang="en"
            ))

        return events

    except Exception as e:
        print(f"⚠️ Currents API failed: {e}")
        return []



# ========================
# GUARDIAN FETCHER
# ========================
def fetch_guardian(limit=50):

    api_key = os.getenv("GUARDIAN_API_KEY")

    url = "https://content.guardianapis.com/search"

    params = {
        "api-key": api_key,
        "page-size": limit,
        "order-by": "newest"
    }

    try:
        response = requests.get(url, params=params)

        if response.status_code != 200:
            print(f"⚠️ Guardian error {response.status_code}")
            return []

        data = response.json()

        events = []

        for article in data["response"]["results"]:

            events.append(normalize_event(
                source="guardian",
                source_id=article.get("id"),
                text=article.get("webTitle"),

                # INSERTION TIME
                created_at=datetime.now(timezone.utc).isoformat(),

                lang="en"
            ))

        return events

    except Exception as e:
        print(f"⚠️ Guardian failed: {e}")
        return []




# ========================
# MAIN AGGREGATOR
# ========================
def fetch_all_events():
    events = []

    # Add sources here
    events.extend(fetch_reddit())
    events.extend(fetch_webz())
    events.extend(fetch_newsapi())
    events.extend(fetch_newsdata())
    events.extend(fetch_currents())

    return events


# ========================
# TEST
# ========================
if __name__ == "__main__":
    events = fetch_all_events()

    print(f"Fetched {len(events)} total events")

    for e in events[:5]:
        print(e)
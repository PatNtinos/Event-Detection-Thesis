import os
import requests
import finnhub
from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv()

# API KEYS
WEBZ_API_KEY = os.getenv("WEBZ_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
MEDIASTACK_API_KEY = os.getenv("MEDIASTACK_API_KEY")
GNEWS_API_KEY = os.getenv("GNEWS_API_KEY")
NEWSDATA_API_KEY = os.getenv("NEWSDATA_API_KEY")
CURRENTS_API_KEY = os.getenv("CURRENTS_API_KEY")
GUARDIAN_API_KEY = os.getenv("GUARDIAN_API_KEY")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

# ========================
# COMMON EVENT FORMAT
# ========================
def normalize_event(source, source_id, text, created_at=None, lang=None, url=None):
    # Skip any event with empty text
    if not text or not text.strip():
        return None
    
    return {
        "source": source,
        "source_id": source_id,
        "text": text,
        # The created_at is set to the current time, as not all APIs provide a timestamp, when a full pipeline is made, and more APIs are used, this can be changed.
        "created_at": created_at,
        "lang": lang,
        # The URL is not used in the specs of this Thesis, it can be added for future use
        #"url": url
    }


# ========================
# REDDIT FETCHER
# ========================
def fetch_reddit(limit=30):
    url = "https://www.reddit.com/r/news/.json"
    headers = {"User-Agent": "linux:event-pipeline-test:v1.0 (by /u/Chance_Ad4466)"}

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
                lang="en"  
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

        # Generic event query
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
                created_at=datetime.now(timezone.utc).isoformat(),

                lang="en"
            ))

        return events

    except Exception as e:
        print(f"⚠️ Guardian failed: {e}")
        return []

# ========================
# MEDIASTACK FETCHER
# ========================

def fetch_mediastack(limit=5):

    url = "https://api.mediastack.com/v1/news"

    params = {
        "access_key": MEDIASTACK_API_KEY,

        # Event-focused query
        "keywords": (
            "earthquake OR disaster OR war OR protest "
            "OR crash OR explosion OR emergency OR flood"
        ),

        "languages": "en",

        "sort": "published_desc",

        "limit": limit
    }

    try:
        response = requests.get(url, params=params)

        if response.status_code != 200:
            print(f"⚠️ Mediastack error {response.status_code}")
            print(response.text)
            return []

        data = response.json()

        events = []

        for article in data.get("data", []):

            # skip empty titles
            if not article.get("title"):
                continue

            events.append(normalize_event(
                source="mediastack",
                source_id=article.get("url"),  # best unique ID
                text=article.get("description") or article.get("title"),
                created_at=datetime.now(timezone.utc).isoformat(),
                lang=article.get("language", "en"),
            ))

        return events

    except Exception as e:
        print(f"⚠️ Mediastack failed: {e}")
        return []


# ========================
# GNEWS FETCHER
# ========================

def fetch_gnews(limit=10):

    url = "https://gnews.io/api/v4/search"

    params = {
        "q": (
            "earthquake OR disaster OR war OR protest "
            "OR explosion OR emergency OR crash OR flood"
        ),
        "lang": "en",
        "max": limit,
        "apikey": GNEWS_API_KEY
    }

    try:
        response = requests.get(url, params=params)

        if response.status_code != 200:
            print(f"⚠️ GNews error {response.status_code}")
            print(response.text)
            return []

        data = response.json()

        events = []

        for article in data.get("articles", []):

            if not article.get("title"):
                continue

            events.append(normalize_event(
                source="gnews",
                source_id=article.get("id"),
                text=article.get("description") or article.get("title"),
                created_at=datetime.now(timezone.utc).isoformat(),
                lang="en",
            ))

        return events

    except Exception as e:
        print(f"⚠️ GNews failed: {e}")
        return []
    

# ========================
# FINNHUB FETCHER
# ========================

def fetch_finnhub(limit=20):

    try:
        finnhub_client = finnhub.Client(api_key=FINNHUB_API_KEY)

        data = finnhub_client.general_news("general")

        events = []

        for article in data[:limit]:

            events.append(normalize_event(
                source="finnhub",
                source_id=article.get("id"),
                text=article.get("summary"),
                created_at=datetime.now(timezone.utc).isoformat(),
                lang="en"
            ))

        return events

    except Exception as e:
        print(f"⚠️ Finnhub failed: {e}")
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
    events.extend(fetch_guardian())
    events.extend(fetch_mediastack())
    events.extend(fetch_gnews())
    events.extend(fetch_finnhub())

    return events


# ========================
# TEST
# ========================
if __name__ == "__main__":
    events = fetch_all_events()

    print(f"Fetched {len(events)} total events")

    for e in events[:5]:
        print(e)
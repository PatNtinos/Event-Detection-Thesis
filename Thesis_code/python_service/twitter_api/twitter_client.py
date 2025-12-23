
# To access file paths and environment variables
import os
# Get/Post requests API repsonses
import requests
# Load environment variables from a .env file for security
from dotenv import load_dotenv

# Read the .env file
load_dotenv()

# Reads the token from the .env file
BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")
# Error if there is no Bearer Token. To know what happened
if not BEARER_TOKEN:
    raise RuntimeError("TWITTER_BEARER_TOKEN not found in .env")


# A function to call Twitter API and print the response
def fetch_from_twitter_api(query="python", max_results=13):
    # Twitter API endpoint
    url = "https://api.twitter.com/2/tweets/search/recent"
    headers = {
        "Authorization": f"Bearer {BEARER_TOKEN}"
    }
    # What Twitter returns
    params = {
        "query": query,
        # Number of tweets to return min 10 max 100
        "max_results": max_results,
        # Fields to return
        "tweet.fields": "created_at,text,lang"
    }

    # Make the GET request to Twitter API
    response = requests.get(url, headers=headers, params=params)

    # Print the status code if something went wrong
    if response.status_code != 200:
        raise RuntimeError(
            f"Twitter API error {response.status_code}: {response.text}"
        )
    
    # Convert the Json to a Python dictionary
    data = response.json()
    # Extract tweets on a list
    tweets = []

    # Twitter returns tweets under the "data" key
    for tweet in data.get("data", []):
        # Add the tweets to the list
        tweets.append({
            "id": tweet["id"],
            "text": tweet["text"],
            "created_at": tweet.get("created_at"),
            "lang": tweet.get("lang"),
            "source": "twitter"
        })

    return tweets

# Run the test function if this file is executed directly
if __name__ == "__main__":
    # Call main function 
    tweets = fetch_from_twitter_api()
    # Prints how many tweets were fetched
    print(f"Fetched {len(tweets)} tweets")
    # Print the first tweet as a sample
    print(tweets[0])
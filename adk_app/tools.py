
import os
import json
import pathlib
import sys

# Try importing googlesearch, handle if not installed (though it should be)
try:
    from googlesearch import search
except ImportError:
    search = None

from .models import Signal, BNIMember

ROOT = str(pathlib.Path(__file__).resolve().parents[1])

def get_knowledge_base() -> str:
    """
    Returns the full BNI member knowledge base + trigger rules.
    Use this to understand who you are finding recommendations for.
    """
    members_path = os.path.join(ROOT, "data", "members.json")
    try:
        with open(members_path, "r") as f:
            return f.read()
    except Exception as e:
        return f"Error loading knowledge base: {e}"

def search_google(query: str) -> str:
    """
    Executes a Google Search using the official Custom Search JSON API.
    Returns a list of results (title + url + description).
    """
    api_key = os.getenv("SEARCH_API_KEY")
    cse_id = os.getenv("GOOGLE_CSE_ID")

    if not api_key or not cse_id:
        return "Error: SEARCH_API_KEY or GOOGLE_CSE_ID not found in environment."

    import datetime
    seven_days_ago = (datetime.datetime.now() - datetime.timedelta(days=7)).strftime('%Y-%m-%d')
    query_with_date = f"{query} after:{seven_days_ago}"
    
    print(f"DEBUG: Agent executes Google API search query: {query_with_date}")
    
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": api_key,
        "cx": cse_id,
        "q": query_with_date,
        "num": 5,
        "hl": "nl",
        "gl": "nl"
    }

    try:
        import requests
        response = requests.get(url, params=params)
        response.raise_for_status()
        search_data = response.json()
        
        results = []
        if "items" in search_data:
            for item in search_data["items"]:
                results.append({
                    "title": item.get("title"),
                    "url": item.get("link"),
                    "description": item.get("snippet")
                })
        
        if not results:
            print("DEBUG: API Search returned 0 results.")
            return "No results found."

        return json.dumps(results, indent=2)

    except Exception as e:
        print(f"DEBUG: API Search failed: {e}")
        return f"Search API failed: {e}"

    return json.dumps(results, indent=2)

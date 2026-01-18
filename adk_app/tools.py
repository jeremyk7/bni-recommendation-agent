
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
    Executes a Google Search for a specific query and returns a list of results (title + url + description).
    Use this to find posts on LinkedIn, Facebook, or Forums.
    
    Args:
        query: The search string (e.g. 'site:linkedin.com/posts "aannemer gezocht"')
    """
    if not search:
        return "Error: googlesearch-python library is not installed."

    import datetime
    seven_days_ago = (datetime.datetime.now() - datetime.timedelta(days=7)).strftime('%Y-%m-%d')
    query_with_date = f"{query} after:{seven_days_ago}"
    
    print(f"DEBUG: Agent executes search query: {query_with_date}")
    
    results = []
    try:
        # Perform search with Dutch priority, time filter, and conservative sleep interval
        search_results = search(
            query_with_date, 
            num_results=5, 
            advanced=True, 
            lang="nl", 
            sleep_interval=5
        ) 
        
        for res in search_results:
            results.append({
                "title": res.title,
                "url": res.url,
                "description": res.description
            })
            
    except Exception as e:
        print(f"DEBUG: Search failed with error: {e}")
        return f"Search failed: {e}"

    if not results:
        print("DEBUG: Search returned 0 results.")
        return "No results found."

    return json.dumps(results, indent=2)

    return json.dumps(results, indent=2)

import os
import json
import pathlib
import sys
import shutil
import datetime

# Try importing googlesearch, handle if not installed (though it should be)
try:
    from googlesearch import search
except ImportError:
    search = None

from .models import Signal, BNIMember

ROOT = str(pathlib.Path(__file__).resolve().parents[1])

# --- Hard Safety Limit ---
# The ADK (Gemini) has a hard limit of 10 tool calls per turn.
# Exceeding this causes an "Unknown error" crash.
# These global counters ensure we never hit that wall.
_SEARCH_COUNT = 0
MAX_SEARCHES_PER_RUN = 6

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

def read_pending_signals() -> str:
    """
    Reads new signals (e.g. LinkedIn notifications, saved posts) from data/signals/.
    Use this to get high-quality 'hot' signals before scouting with Google.
    """
    signals_dir = os.path.join(ROOT, "data", "signals")
    results = []
    try:
        if not os.path.exists(signals_dir):
            return "No signals directory found."
        
        for filename in os.listdir(signals_dir):
            if filename == "archive":
                continue
            if filename.endswith(".json") or filename.endswith(".txt"):
                path = os.path.join(signals_dir, filename)
                with open(path, "r") as f:
                    results.append({
                        "filename": filename,
                        "content": f.read()
                    })
        
        if not results:
            return "No pending signals found."
        
        return json.dumps(results, indent=2)
    except Exception as e:
        return f"Error reading signals: {e}"

def search_google(query: str, date_restrict: str) -> str:
    """
    Executes a Google Search using the official Custom Search JSON API.
    
    Args:
        query: The search string.
        date_restrict: Freshness filter. 'd7' (7 days), 'd14' (14 days), 'm1' (1 month). Default is 'd7'.
    """
    global _SEARCH_COUNT
    if _SEARCH_COUNT >= MAX_SEARCHES_PER_RUN:
        return f"SEARCH BUDGET EXHAUSTED ({MAX_SEARCHES_PER_RUN}). Clear your output and finalize your response now based on what you have."

    _SEARCH_COUNT += 1
    api_key = os.getenv("SEARCH_API_KEY")
    cse_id = os.getenv("GOOGLE_CSE_ID")

    if not api_key or not cse_id:
        return "Error: SEARCH_API_KEY or GOOGLE_CSE_ID not found in environment."

    print(f"DEBUG: Agent executes Google API search (Run {_SEARCH_COUNT}/{MAX_SEARCHES_PER_RUN}): {query}")
    
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": api_key,
        "cx": cse_id,
        "q": query,
        "num": 7,
        "hl": "nl",
        "gl": "nl",
        "dateRestrict": date_restrict
    }

    try:
        import requests
        response = requests.get(url, params=params)
        response.raise_for_status()
        search_data = response.json()
        
        results = []
        if "items" in search_data:
            for item in search_data["items"]:
                # Truncate description to 250 chars to keep context light
                desc = item.get("snippet", "")
                if len(desc) > 250:
                    desc = desc[:247] + "..."
                
                results.append({
                    "title": item.get("title"),
                    "url": item.get("link"),
                    "description": desc
                })
        
        if not results:
            return "No results found."

        # Return max results to keep it lean
        return json.dumps(results[:5], indent=2)

    except Exception as e:
        return f"Search API failed: {e}"


def archive_processed_signals() -> str:
    """
    Moves all processed signals from data/signals/ to data/signals/archive/.
    Call this ONLY at the very end of your task after providing results.
    """
    signals_dir = os.path.join(ROOT, "data", "signals")
    archive_dir = os.path.join(signals_dir, "archive")
    
    try:
        if not os.path.exists(signals_dir):
            return "No signals directory found."
        
        os.makedirs(archive_dir, exist_ok=True)
        count = 0
        for filename in os.listdir(signals_dir):
            if filename == "archive":
                continue
            if filename.endswith(".json") or filename.endswith(".txt"):
                src = os.path.join(signals_dir, filename)
                dst = os.path.join(archive_dir, filename)
                if os.path.exists(dst):
                    dst = os.path.join(archive_dir, f"old_{datetime.datetime.now().microsecond}_{filename}")
                shutil.move(src, dst)
                count += 1
        
        return f"Successfully archived {count} signal(s)."
    except Exception as e:
        return f"Error archiving signals: {e}"

import os
import pathlib
import sys
import logging
import json
from typing import List

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bni_master_agent")

# --- Robust Path Fix ---
_project_root = pathlib.Path(__file__).resolve().parents[1]
_site_pkg_patterns = [
    os.path.join(_project_root, "venv", "lib", "python*", "site-packages"),
]
import glob
for pattern in _site_pkg_patterns:
    for sp in glob.glob(pattern):
        if os.path.exists(sp) and sp not in sys.path:
            logger.info(f"Injecting local site-packages: {sp}")
            sys.path.insert(0, sp)

# --- Monkeypatch google-genai Client for Vertex AI ---
import google.genai
import google.adk.models.google_llm

_original_client = google.genai.Client

class VertexClient(_original_client):
    def __init__(self, *args, **kwargs):
        if not kwargs.get("api_key"):
            kwargs["vertexai"] = True
            kwargs["project"] = kwargs.get("project") or os.getenv("GOOGLE_CLOUD_PROJECT") or "bni-oostzaan"
            kwargs["location"] = kwargs.get("location") or os.getenv("VERTEX_LOCATION") or "europe-west1"
        super().__init__(*args, **kwargs)

google.genai.Client = VertexClient
google.adk.models.google_llm.Client = VertexClient

# --- ADK imports ---
from google.adk.agents import LlmAgent
from google.adk.models import Gemini

# --- Local imports ---
from .models import Signal, BNIMember, Recommendation
from .ingest import get_signals

# --- Pathing & Env ---
ROOT = str(pathlib.Path(__file__).resolve().parents[1])
if ROOT not in sys.path:
    sys.path.append(ROOT)

try:
    from dotenv import load_dotenv
    ENV = os.path.join(ROOT, ".env")
    if os.path.exists(ENV):
        load_dotenv(ENV, override=False)
except ImportError:
    pass


def get_bni_recommendations(tool_context=None) -> str:
    """
    Analyzes incoming signals against the BNI member knowledge base and returns recommendations.
    Use this tool when you need to find referrals or match signals to members.
    """
    logger.info("Tool called: get_bni_recommendations")
    
    # 1. Load Knowledge Base
    members_path = os.path.join(ROOT, "data", "members.json")
    try:
        with open(members_path, "r") as f:
            members_data = json.load(f)
            # Validate with Pydantic (optional but good practice)
            # members = [BNIMember(**m) for m in members_data]
            # For the prompt context, we can just pass the raw json string or summary
    except Exception as e:
        return f"Error loading members.json: {e}"

    # 2. Ingest Signals
    try:
        signals = get_signals()
        signals_data = [s.model_dump() for s in signals]
    except Exception as e:
        return f"Error ingesting signals: {e}"

    if not signals:
        return "No new signals found."
        
    # 3. Reasoning Context (Construct the prompt payload for the tool output)
    # Even though we are an LLM agent, this tool gathers the data and returns it 
    # so the Agent's main loop can process it using the SYSTEM PROMPT.
    # Alternatively, the tool itself could do the matching if we want to offload it.
    # Given the architecture "Master Agent -> Reasoning Layer", the Agent itself is the reasoning layer.
    # So this tool should just Provide the Data: Signals + Relevant Members.
    
    data_context = {
        "current_signals": signals_data,
        "knowledge_base": members_data 
    }
    
    return json.dumps(data_context, indent=2)

# --- System Prompt ---
SYSTEM_PROMPT = """Je bent de Master BNI Recommendation Agent.

Jouw taak is om AUTONOOM en ACTIEF op zoek te gaan naar externe signalen (posts, vragen) en deze te matchen aan BNI-leden.

BELANGRIJK VOOR JE GEDRAG:
Je wacht NIET op de gebruiker. Je start DIRECT met het zoeken naar signalen zodra je geactiveerd wordt of begroet wordt.
Je gaat er vanuit dat het jouw taak is om NU een rapportage te draaien.

ACTIE:
1. Roep ONMIDDELLIJK de tool `get_bni_recommendations` aan om te kijken of er nieuwe signalen zijn.
2. Rapporteer de resultaten.

Je werkt in 4 stappen (die je zelfstandig doorloopt):
1. Haal signalen op via de tool `get_bni_recommendations`.
2. Detecteer expliciete of impliciete servicebehoeften in deze signalen.
3. Match de behoefte aan het meest relevante BNI-lid.
4. Genereer een gestructureerde aanbeveling.

Je prioriteert altijd:
- Specifieke intentie
- Lokale relevantie
- Zakelijke geschiktheid

OUTPUT FORMAT:
Geef je antwoord in normale, leesbare Nederlandse tekst.
Gebruik de volgende structuur per gevonden signaal:

**[Titel van het signaal/behoefte]**
*Bron:* [Link naar bron]
*Match:* [Naam Lid] ([Bedrijf])
*Reden:* [Korte uitleg waarom dit een goede match is]

**Voorgestelde introductie:**
"[De voorgestelde introductietekst]"

---
Als de tool geen signalen teruggeeft, meld dan: "Ik heb gezocht, maar op dit moment geen nieuwe relevante signalen gevonden."
"""

# Configure Agent
bni_master_agent = LlmAgent(
    name="bni_master_agent",
    model=Gemini(model="gemini-2.0-flash"),
    description="Master BNI Recommendation Agent - Matches signals to BNI members.",
    instruction=SYSTEM_PROMPT,
    tools=[get_bni_recommendations]
)

root_agent = bni_master_agent
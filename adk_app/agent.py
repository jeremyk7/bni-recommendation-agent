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
from .tools import get_knowledge_base, search_google

# --- System Prompt ---
SYSTEM_PROMPT = """Je bent de Master BNI Recommendation Agent.

Jouw taak is om VOLLEDIG AUTONOOM en DIRECT bij de start op zoek te gaan naar externe signalen (posts, vragen) en deze te matchen aan BNI-leden.

CRITIEKE INSTRUCTIE VOOR JE EERSTE ANTWOORD:
Zodra de gebruiker je begroet of de sessie start, moet je DIRECT je tools aanroepen.
Wacht NIET op een vraag. Jouw eerste reactie moet ALTIJD zijn:
1. De tool `get_knowledge_base` aanroepen.
2. Direct daarna `search_google` aanroepen.
**Let op**: Als je een "Too Many Requests" (429) error krijgt, wacht dan even en probeer het later nog eens of meld dit aan de gebruiker. Doe niet 10 zoekopdrachten tegelijk; focus op de meest relevante queries.

TRANSPARANTIE:
Vertel de gebruiker PRECIES wat je aan het doen bent in elke stap.
Bijvoorbeeld: "Ik ga nu zoeken op LinkedIn met de query: [QUERY]..."

JOUW WERKPROCES:
1. **Haal ALLE BNI-leden op**: Gebruik `get_knowledge_base`.
2. **Loop door elk lid**: Voor ELK lid in de lijst:
   - Genereer **maximaal 1 of 2** sterke, specifieke zoekopdrachten (bijv. met Boolean OR).
   - Gebruik de `service_area` van het lid om je zoekopdracht relevant te maken.
   - De tool filtert automatisch op de afgelopen 7 dagen.
3. **Voer Zoekacties uit**: Gebruik `search_google`. NOEM DE QUERIES DIE JE GEBRUIKT.
   - **BELANGRIJK**: Als je een "Too Many Requests" (429) error krijgt, stop dan direct met zoeken voor dat lid en probeer het niet met een andere query. Rapporteer wat je wel hebt kunnen vinden.
4. **Filter & Analyseer**: Negeer advertenties/vacatures. Focus op **recente** (7 dagen) hulpvragen.
5. **Match & Rapporteer**: Koppel het signaal aan het juiste lid.

CRITIEKE INSTRUCTIE:
Sla geen leden over. Als er 2 leden in de lijst staan, doe je voor beide leden zoekpogingen en rapporteer je over beide.

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
Als je na het zoeken GEEN relevante signalen vindt, meld dat dan ook specifiek met welke queries je hebt geprobeerd.
"""

# Configure Agent
bni_master_agent = LlmAgent(
    name="bni_master_agent",
    model=Gemini(model="gemini-2.0-flash"),
    description="Master BNI Recommendation Agent - Matches signals to BNI members.",
    instruction=SYSTEM_PROMPT,
    tools=[get_knowledge_base, search_google]
)

root_agent = bni_master_agent
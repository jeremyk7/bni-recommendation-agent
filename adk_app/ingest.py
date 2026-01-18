from typing import List
from .models import Signal

def get_signals() -> List[Signal]:
    """
    Returns a list of mock signals for testing the Master BNI Agent.
    In a real scenario, this would connect to Cloud Functions, DBs, or APIs.
    """
    # Mock signal based on the user prompt
    mock_signal = Signal(
        source="linkedin",
        author="Jan de Vries",
        content="Wie kent een goede aannemer voor een uitbouw?",
        url="https://linkedin.com/in/jandevries/posts/123456",
        timestamp="2026-01-10",
        location="Noord-Holland"
    )
    
    return [mock_signal]

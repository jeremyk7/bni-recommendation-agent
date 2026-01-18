from pydantic import BaseModel, Field
from typing import List, Optional

class BNIMember(BaseModel):
    member_id: str
    name: str
    company: str
    expertise: str
    triggers: List[str]
    good_match_rules: List[str]
    bad_match_rules: List[str]
    preferred_sources: List[str]
    intro_template: str

class Signal(BaseModel):
    source: str
    author: str
    content: str
    url: str
    timestamp: str
    location: str

class MatchResult(BaseModel):
    member: str
    company: str
    confidence: str = Field(description="low, medium, or high")
    reason: str

class Recommendation(BaseModel):
    signal_summary: str
    source: str
    match: MatchResult
    proposed_intro: str
    link: str

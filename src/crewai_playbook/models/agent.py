from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class AgentDefinition(BaseModel):
    role: str
    goal: str
    backstory: str
    tools: Optional[List[str]] = None
    llm: Optional[str] = None
    allow_delegation: bool = False
    verbose: bool = False
    groups: Optional[List[str]] = None
    leader: bool = False


class AgentInventory(BaseModel):
    agents: Dict[str, AgentDefinition]

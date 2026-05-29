from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from crewai_playbook.models.playbook import Task, Handler


class RoleDefinition(BaseModel):
    name: str
    defaults: Dict[str, Any] = {}
    tasks: List[Task | dict] = []
    handlers: Optional[List[Handler]] = None

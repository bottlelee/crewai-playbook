from __future__ import annotations

from typing import Any, List, Optional

from pydantic import BaseModel, Field


class Task(BaseModel):
    model_config = {"populate_by_name": True}
    name: str
    agents: List[str]
    task: str
    src: Optional[str] = None
    dest: Optional[str] = None
    register_var: Optional[str] = Field(default=None, alias="register")
    when: Optional[str] = None
    notify: Optional[List[str]] = None
    until: Optional[str] = None
    retries: Optional[int] = None
    delay: Optional[int] = None
    tags: Optional[List[str]] = None
    vars: Optional[dict[str, Any]] = None


class Block(BaseModel):
    block: List[Task]
    rescue: Optional[List[Task]] = None
    always: Optional[List[Task]] = None
    when: Optional[str] = None
    tags: Optional[List[str]] = None


class Handler(BaseModel):
    name: str
    tasks: List[Task]


class VarPrompt(BaseModel):
    """A single ``vars_prompt`` entry that asks the user for input."""
    name: str
    prompt: Optional[str] = None
    default: Optional[str] = None
    private: bool = False
    choices: Optional[List[str]] = None


class Role(BaseModel):
    role: str
    vars: Optional[dict[str, Any]] = None
    tags: Optional[List[str]] = None
    when: Optional[str] = None


class Play(BaseModel):
    name: str
    agents: List[str]
    vars: Optional[dict[str, Any]] = None
    vars_prompt: Optional[List[VarPrompt]] = None
    tasks: Optional[List[Task | Block]] = None
    roles: Optional[List[Role]] = None
    handlers: Optional[List[Handler]] = None
    become: bool = False
    gather_facts: bool = True
    tags: Optional[List[str]] = None
    process: str = "sequential"


class Playbook(BaseModel):
    """A playbook is a list of plays."""
    plays: List[Play]

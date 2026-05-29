# CrewAI Overview

> Source: https://docs.crewai.com/ (official docs)
> Last fetched: 2026-05-29

## What is CrewAI?

CrewAI is the leading open-source framework for orchestrating autonomous AI agents and building complex workflows. It empowers developers to build production-ready multi-agent systems by combining the collaborative intelligence of **Crews** with the precise control of **Flows**.

### Key Facts
- **Stars**: ~52,000+ on GitHub
- **Latest Release**: 1.14.6a1 (2026-05-21)
- **License**: MIT
- **Used by**: 60% of US Fortune 500
- **Scale**: ~450 million agents/month (early 2026)
- **Contributors**: 300+

## Architecture

CrewAI has two primary abstractions that work together:

### 1. Flows (The Backbone)
- Event-driven workflow orchestration
- State management across steps
- Conditional logic, loops, branching
- `@start()`, `@listen()`, `@router()` decorators
- `@persist` decorator for state persistence

### 2. Crews (The Intelligence)
- Teams of role-playing agents
- Autonomous collaboration
- Task delegation
- Sequential or hierarchical processes

### How They Work Together
1. **Flow** triggers an event or starts a process
2. **Flow** manages state and decides next steps
3. **Flow** delegates complex tasks to a **Crew**
4. **Crew** agents collaborate to complete the task
5. **Crew** returns results to the **Flow**
6. **Flow** continues execution based on results

## Key Features
- Production-grade Flows with state management
- Autonomous Crews with role-based agents
- 40+ built-in tools (search, scraping, databases, etc.)
- MCP (Model Context Protocol) support
- Enterprise security (RBAC, SSO, secrets management)
- Observability (tracing, monitoring, 15+ integrations)
- Memory systems (short-term, long-term, entity)
- Knowledge sources (RAG)
- Human-in-the-loop workflows
- Structured outputs (Pydantic/JSON)
- Task guardrails and validation

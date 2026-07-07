---
name: context-retriever
display_name: Context Retriever
description: Retrieves relevant context from repository, history, and memory
agent_types:
  - orchestrator
  - coder
  - architect
intent_triggers:
  - get context
  - retrieve information
provides:
  - context
  - relevant_files
estimated_tokens: 1000
---

Skill for retrieving and assembling relevant context from the repository, git history,
project memory, and related sources. Enables agents to have sufficient information to make
informed decisions and produce quality output.

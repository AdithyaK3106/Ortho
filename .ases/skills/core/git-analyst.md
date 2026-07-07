---
name: git-analyst
display_name: Git Analyst
description: Analyzes git history, commits, authors, and change patterns
agent_types:
  - analyst
  - debugger
intent_triggers:
  - analyze git history
  - track changes
provides:
  - git_history
  - change_analysis
estimated_tokens: 2000
---

Skill for analyzing git history, tracking who changed what, identifying patterns in
commits, and understanding how code has evolved. Useful for analysts and debuggers to
understand change context and potential causes of issues.

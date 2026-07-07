---
name: code-reviewer
display_name: Code Reviewer
description: Reviews code for correctness, style, and quality
agent_types:
  - reviewer
intent_triggers:
  - review code
  - quality check
provides:
  - review_comments
  - quality_verdict
estimated_tokens: 2500
---

Skill for conducting thorough code reviews that assess correctness, performance, security,
and adherence to standards. Essential for reviewer agents to maintain code quality and
catch issues before integration.

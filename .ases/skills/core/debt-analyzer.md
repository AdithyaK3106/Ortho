---
name: debt-analyzer
display_name: Debt Analyzer
description: Analyzes technical debt, code quality metrics, and refactoring needs
agent_types:
  - analyst
  - reviewer
intent_triggers:
  - analyze debt
  - quality metrics
provides:
  - debt_report
  - refactoring_recommendations
estimated_tokens: 2000
---

Skill for identifying and analyzing technical debt in codebases, measuring code quality,
and recommending refactoring opportunities. Helps analysts and reviewers understand quality
issues and prioritize improvement work.

---
name: test-generator
display_name: Test Generator
description: Generates test cases and test plans for code
agent_types:
  - tester
  - coder
intent_triggers:
  - generate tests
  - test plan
provides:
  - test_code
  - test_plan
estimated_tokens: 3000
---

Skill for generating comprehensive test cases and test plans that cover requirements,
edge cases, and error scenarios. Enables tester and coder agents to ensure code quality
and maintainability through systematic testing.

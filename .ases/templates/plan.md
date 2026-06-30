task: [task-id]
title: [task-title]
owner: Solo Developer
created: [YYYY-MM-DD]

summary: [2-3 sentences describing what and why]

atomic_tasks:
  - task: [subtask-1-title]
    scope: [what changes, files affected]
    duration_min: 30
    duration_max: 90
    dependencies: [task-id or "none"]
    acceptance: [criterion1, criterion2, ...]
  - task: [subtask-2-title]
    scope: [...]
    duration_min: 45
    duration_max: 75
    dependencies: [task-id]
    acceptance: [...]

task_order: task-1 → task-2 → task-3 [diagram if parallel branches exist]

risks:
  - risk: [title] — [what fails] — [impact] — [mitigation]
  - risk: [...]

acceptance:
  - [testable criterion 1]
  - [criterion 2]
  - [criterion N - must all be true]

notes_for_architect: [architectural flags: new modules? APIs? dependencies? security?]
notes_for_builder: [implementation guidance, constraints, edge cases]

---

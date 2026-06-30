task: [task-id]
title: [task-title]
owner: Solo Developer
created: [YYYY-MM-DD]
status: DRAFT | APPROVED | IN PROGRESS
architecture_impact: NONE | MAJOR (if MAJOR, architect-review.md required)

objective: [One sentence. Specific. What exactly changes?]

files_create: [path1, path2, ...] | none
files_modify: [path1, path2, ...] | none
files_forbid: [path1, path2, ...] | none (list what BUILDER must NOT touch)

contract_in: [Input schema or "none"]
contract_out: [Output schema or "none"]

acceptance:
  - [testable criterion 1] — evidence: [how to verify]
  - [testable criterion 2] — evidence: [how to verify]
  - [criterion N]

dependencies: [task-id, task-id, ...] | none

risk: LOW | MEDIUM | HIGH — [one sentence description]

verification_commands: |
  tsc --noEmit [files]
  jest [test-path]
  [other commands]

change_impact:
  modules: [new/modified modules]
  apis: [new endpoints or contracts]
  regression_candidates: [existing tests that might break]

notes_for_builder: [key implementation guidance or constraints]

---

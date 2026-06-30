task: [task-id]
title: [task-title]
builder: Solo Developer
implemented: [YYYY-MM-DD]
status: IMPLEMENTED | BLOCKED

built:
  [path/file1.ts]: [one-line description of what was built/modified]
  [path/file2.ts]: [description]
  [path/fileN.sql]: [description]

not_built:
  - [feature from spec NOT built — why]
  - [feature from spec NOT built — why]

deviations:
  - [deviation from spec — justification]
  - [or: "None. Implementation matches spec exactly."]

files_modified:
  created: [path1, path2, ...]
  modified: [path1, path2, ...]

verification_commands: |
  tsc --noEmit [files]
  eslint [files]
  jest [test-path]

honest_assessment:
  assumptions:
    - [assumption 1] — mitigation: [how to handle]
    - [assumption 2] — mitigation: [...]
  edge_cases_not_tested: [list or "none"]
  performance_risks: [list or "none"]

code_quality_notes: [shortcuts, tech debt, or "clean"]
testing_notes_for_designer: [critical paths, edge cases, performance considerations]

---

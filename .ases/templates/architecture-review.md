task: [task-id]
title: [task-title]
architect: ARCHITECT
created: [YYYY-MM-DD]
status: DRAFT | PROPOSED | APPROVED | REJECTED

module_boundaries:
  new_modules: [module1 (responsibility), module2, ...]
  modified_modules: [module1, module2, ...]
  assessment: [PASS | issues: specific concern, specific concern, ...]

dependency_analysis:
  graph: [text visualization or "none — no new dependencies"]
  circular_deps: [PASS | found: cycle description]
  assessment: [PASS | issues: dependency X is questionable because ...]

api_contracts:
  new_endpoints: [POST /path (input/output), GET /path, ...]
  consistency: [PASS | issues: endpoint X diverges from pattern Y]
  assessment: [PASS | issues: ...]

data_flow:
  validation_layers: [boundary, business logic, database] ✓
  data_integrity: [constraints present, cascades handled] ✓
  assessment: [PASS | issues: ...]

risk_flags:

### Security
- **Input Validation** ✓ — Name and description validated for length and format
- **SQL Injection** ✓ — Parameterized queries used (no string interpolation)
- **Access Control** — No user-based access control needed (all users see all categories)
- **Secrets** ✓ — No secrets in category data
- **Risk Level:** LOW

### Scalability
- **Database Queries** ✓ — GET /categories with pagination (limit/offset)
- **Index Strategy** — Category name indexed for fast lookups?
  - ⚠ **Flag:** Consider adding index on category.name for performance at scale
  - **Mitigation:** Add index if category table grows to >10k records
- **Concurrent Writes** — POST same category name simultaneously?
  - ✓ Database unique constraint prevents duplicates
- **Risk Level:** LOW (with mitigation: add index at scale)

### Extensibility
- **Future Features** — Can this design accommodate category tags, hierarchies, permissions?
  - ✓ Schema is simple and can be extended with new columns
  - ⚠ Hierarchies (parent_category_id) would require redesign
  - **Mitigation:** Document limitations, revisit if hierarchies needed
- **Risk Level:** LOW

### Data Integrity
- **Race Conditions** — Two simultaneous POSTs with same name?
  - ✓ Unique constraint prevents both from inserting
- **Orphaned Records** — Delete category with active expenses?
  - ✓ DELETE validation prevents deletion if expenses exist
- **Cascade Behavior** — Clear and documented
- **Risk Level:** LOW

### Breaking Changes
- **Backward Compatibility** ✓ — New APIs, no changes to existing APIs
- **Database Schema** ✓ — New table, no modifications to existing tables
- **Risk Level:** LOW

---

## ADR References

[Which existing ADRs apply to this feature?]

- **ADR-001:** ASES as multi-agent system — Applies ✓ (being built under ASES)
- **ADR-002:** Bootstrap protocol — Applies ✓ (Phase 0 development)
- **ADR-003:** Evidence from terminal only — Applies ✓ (will be verified)

[Any new ADRs needed? See Part 5.2 of FRD for mandatory ADR triggers.]

### ADRs to Create
[If this feature triggers mandatory ADR creation:]
- **If new module:** ADR-004: "CategoryService module creation"
- **If new database table:** ADR-005: "Category table schema design"
- **If new dependency:** [List and create]

---

## Architecture Compliance Check

[Before verdict, verify:]
- [ ] All module boundaries are clear
- [ ] No circular dependencies
- [ ] All APIs are defined and consistent
- [ ] Data flow is validated at correct layers
- [ ] All risks identified and mitigated
- [ ] Related ADRs reviewed or created
- [ ] No violations of existing decisions

---

## Explicit Verdict

**APPROVED** ✓ or **REJECTED** ✗

### If APPROVED:
Architecture is sound. No structural concerns. Module boundaries are clear. API contracts are defined. Risks are identified and acceptable. Safe to proceed to BUILDER.

### If REJECTED:
[Be specific about what must change before proceeding]
- Issue 1: [What is wrong] — [Must be fixed] — [Reference spec section or ADR]
- Issue 2: [What is wrong] — [Must be fixed] — [Reference]

Return to PLANNER with specific issues. Do not proceed to BUILDER.

---

## Reviewer Notes

[Any additional context or recommendations?]

---

## Approval Checklist

- [ ] Module boundaries evaluated
- [ ] Dependency graph reviewed (no cycles)
- [ ] All APIs defined and consistent
- [ ] Data flow and validation reviewed
- [ ] All risks identified and mitigated
- [ ] ADRs created if required
- [ ] Explicit verdict: APPROVED or REJECTED

---

*End of architecture-review.md template*

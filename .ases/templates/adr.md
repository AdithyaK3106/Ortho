# ADR-[NNN]: [Title]

**Status:** DRAFT | PROPOSED | ACCEPTED | SUPERSEDED BY ADR-[NNN]  
**Date:** [YYYY-MM-DD]  
**Author:** [Agent Role — e.g., ARCHITECT]  
**Approved by:** [Human Name] on [YYYY-MM-DD]

---

## Context

[What situation led to this decision needing to be made? Provide background and constraints.]

Example:
> The expense tracking system requires categories to organize user spending. As the system grows, we need to decide: Should categories be stored in a separate database table (separate entity) or embedded in expense records as an enumeration? This decision will affect data model, query performance, and feature extensibility for years to come.

---

## Problem Statement

[What specific problem does this decision solve? Be concrete.]

Example:
> We need a flexible category system that can:
> 1. Allow users to define custom categories (not fixed enum)
> 2. Support unlimited number of categories (not predefined list)
> 3. Enable efficient queries like "all expenses in category X"
> 4. Allow future features like category hierarchies or tags without rework
>
> Fixed enums won't work because users need custom categories. Embedded data won't work because queries become complex and categories can't be easily reused or updated.

---

## Alternatives Considered

[List every alternative evaluated, not just the winner. For each: what it is, why it was rejected.]

### Option A: Fixed Enum (rejected)
**Description:** Categories hardcoded as enum in code (e.g., `GROCERIES | UTILITIES | ENTERTAINMENT`)

**Pros:**
- Simple to implement
- Fast queries (category is just a string or int)
- No separate table needed

**Cons:**
- Users cannot define custom categories
- Adding new categories requires code deployment
- Not scalable to user-defined categories

**Rejection Reason:** Spec requires custom user-defined categories. Enum doesn't support this.

### Option B: Categories Embedded in Expense Records (rejected)
**Description:** Store category data directly in expense table (category_name VARCHAR, category_color VARCHAR, etc.)

**Pros:**
- No separate table join needed
- All data in one record

**Cons:**
- Category data is duplicated across all expenses in that category
- Updating category (e.g., rename) requires updating all expenses
- Queries are inefficient (can't easily query "all categories")
- Violates database normalization (1NF — atomic values)

**Rejection Reason:** Data duplication and inefficient updates. Separate table is standard practice.

### Option C: Separate Categories Table (chosen) ✓
**Description:** Create separate `categories` table with id, name, description. Foreign key in expenses table references category.

**Pros:**
- Canonical source of truth for each category
- Efficient updates (change once, reflects everywhere)
- Supports queries like "get all categories" or "all expenses in category X"
- Extensible (can add category_color, category_budget, etc. without touching expenses table)
- Follows database normalization best practices
- Supports future features (hierarchies, tags, permissions)

**Cons:**
- Requires JOIN for expense queries
- Slight query performance overhead (minimal with proper indexing)
- More complex than enum or embedded data

**Selection Reason:** Scalable, maintainable, extensible. Best balance of simplicity and power.

---

## Decision

We will implement categories as a separate database table with the following design:

**Categories table:**
- `id` (UUID) — primary key
- `name` (VARCHAR 100) — category name, unique, not null
- `description` (VARCHAR 500) — optional category description
- `created_at` (TIMESTAMP) — creation timestamp
- `updated_at` (TIMESTAMP) — last update timestamp

**Expenses table (modified):**
- Add `category_id` (UUID) — foreign key to categories.id, not null
- Add `NOT NULL` constraint after backfilling existing records

**API:**
- POST /categories — create new category
- GET /categories — list all categories with pagination
- GET /categories/:id — get specific category
- PUT /categories/:id — update category
- DELETE /categories/:id — delete category (reject if expenses exist)

---

## Rationale

Why this option over the alternatives?

**Scalability:** Separate table allows unlimited categories and users to create custom ones. Enum doesn't scale. Embedded data violates normalization.

**Maintainability:** Changing a category name requires one UPDATE (in categories table). If embedded, would require updating all expense records. Error-prone and slow.

**Performance:** With proper indexing (index on category.name), queries are fast. JOIN is negligible cost. Enum queries are slightly faster but not meaningfully so for the cost of losing extensibility.

**Extensibility:** New features (category budget, category hierarchies, category permissions) can be added by adding columns to categories table. With enum or embedded data, would require schema redesign.

**Consistency with Industry Practice:** Separate table is standard database pattern for one-to-many relationships. Developers will expect this design.

---

## Consequences

### Positive
- ✓ Users can create unlimited custom categories
- ✓ Category updates are efficient (atomic)
- ✓ Queries are clear and performant (with indexes)
- ✓ Data is normalized (follows ACID principles)
- ✓ Extensible (can add features without major rework)
- ✓ Familiar pattern (developers expect this design)

### Negative
- ✗ Query complexity slightly increased (requires JOIN for expense details with category name)
- ✗ One more table to manage and backup
- ✗ Delete validation required (cannot delete category with active expenses)

### Neutral
- ~ CategoryService layer introduces slight abstraction overhead
- ~ Migration complexity (if adding to existing system, requires backfill)

---

## Future Considerations

What might cause this decision to be revisited?

1. **If custom categories are not needed:** If system changes to only support predefined categories, could simplify to enum. Would require database migration and API change.

2. **If category hierarchies are needed:** Would add `parent_category_id` column to support parent-child relationships. This is non-breaking — just add column and update service logic.

3. **If performance becomes critical:** If queries with multiple JOINs become slow, could denormalize (cache category_name in expense records). Mitigation: Add indexes, query optimization, or caching layer.

4. **If soft deletes are needed for audit trail:** Would add `deleted_at` column and change DELETE endpoints to soft-delete. Non-breaking change.

---

## Related Tasks

- task-001: Category management feature (uses this ADR)
- task-002: Expense features that reference categories (depends on this ADR)

---

## Related ADRs

- ADR-001: ASES multi-agent system — This ADR created under ASES governance
- ADR-003: Evidence capture from terminal only — Verification of this ADR happens via tests
- [Future] ADR-NNN: Category hierarchies — If parent-child categories needed, will supersede this ADR's design

---

## Implementation Checklist

- [ ] Database migration created (create categories table)
- [ ] Schema file updated (Category TypeScript interface)
- [ ] Repository layer implemented (CategoryRepository)
- [ ] Service layer implemented (CategoryService)
- [ ] Controller endpoints implemented
- [ ] Tests written (unit, integration, edge cases)
- [ ] Verification passed (build, lint, tests, regression)
- [ ] Code review approved
- [ ] Merged to main branch

---

*End of ADR template*

# Feature Specification

**Task ID:** [task-id]  
**Task Title:** [task title]  
**Owner:** [Solo Developer]  
**Created:** [YYYY-MM-DD]  
**Status:** DRAFT | APPROVED | IN PROGRESS

---

## Objective

[One sentence. Specific. What exactly changes?]

✓ Good: "Add POST /categories endpoint that accepts category name and returns 201 with category object"

✗ Bad: "Add expense categories"

---

## Files to Create or Modify

[Explicit paths. No patterns, no guessing.]

### Create
- `src/controllers/CategoryController.ts` — HTTP layer for category operations
- `src/services/CategoryService.ts` — Business logic layer
- `src/schemas/Category.ts` — TypeScript interfaces and database schema
- `src/database/migrations/001_create_categories_table.sql` — Schema migration

### Modify
- `src/index.ts` — Register new routes
- `src/types/index.ts` — Export new types

---

## Files That Must NOT Be Touched

[State this explicitly. Helps BUILDER know scope boundaries.]

- Database schema for expenses table
- API versioning endpoints (/v1/*, /v2/*)
- Authentication middleware
- Existing ExpenseController

---

## Input/Output Contracts

### POST /categories

**Input:**
```typescript
{
  name: string,        // 1-100 characters, alphanumeric + spaces
  description?: string // Optional, max 500 characters
}
```

**Output (201 Created):**
```typescript
{
  id: string,              // UUID
  name: string,
  description: string | null,
  created_at: ISO8601,     // e.g., "2026-06-27T23:55:00Z"
  updated_at: ISO8601
}
```

**Errors:**
```typescript
400 Bad Request: {
  error: "INVALID_NAME",
  message: "Category name must be 1-100 characters"
}

400 Bad Request: {
  error: "INVALID_DESCRIPTION",
  message: "Description must be max 500 characters"
}

409 Conflict: {
  error: "CATEGORY_EXISTS",
  message: "Category with this name already exists"
}

500 Internal Server Error: {
  error: "DATABASE_ERROR",
  message: "Failed to create category"
}
```

### GET /categories

**Input:** None (query params: `?limit=50&offset=0` optional)

**Output (200 OK):**
```typescript
[
  {
    id: string,
    name: string,
    description: string | null,
    created_at: ISO8601,
    updated_at: ISO8601
  },
  ...
]
```

**Errors:**
```typescript
400 Bad Request: {
  error: "INVALID_LIMIT",
  message: "Limit must be 1-100"
}

500 Internal Server Error: {
  error: "DATABASE_ERROR"
}
```

### GET /categories/:id

**Input:**
```
:id = UUID string (category ID)
```

**Output (200 OK):**
```typescript
{
  id: string,
  name: string,
  description: string | null,
  created_at: ISO8601,
  updated_at: ISO8601
}
```

**Errors:**
```typescript
404 Not Found: {
  error: "CATEGORY_NOT_FOUND",
  message: "Category with ID not found"
}

500 Internal Server Error: {
  error: "DATABASE_ERROR"
}
```

### PUT /categories/:id

**Input:**
```typescript
{
  name?: string,        // Optional, if provided, 1-100 characters
  description?: string  // Optional, max 500 characters
}
```

**Output (200 OK):**
```typescript
{
  id: string,
  name: string,
  description: string | null,
  created_at: ISO8601,
  updated_at: ISO8601  // Updated timestamp
}
```

**Errors:**
```typescript
404 Not Found: {
  error: "CATEGORY_NOT_FOUND"
}

400 Bad Request: {
  error: "INVALID_NAME" | "INVALID_DESCRIPTION"
}

409 Conflict: {
  error: "CATEGORY_EXISTS",
  message: "Another category already has this name"
}

500 Internal Server Error: {
  error: "DATABASE_ERROR"
}
```

### DELETE /categories/:id

**Input:**
```
:id = UUID string (category ID)
```

**Output (204 No Content):**
```
(empty body)
```

**Errors:**
```typescript
404 Not Found: {
  error: "CATEGORY_NOT_FOUND"
}

409 Conflict: {
  error: "CATEGORY_HAS_EXPENSES",
  message: "Cannot delete category with active expenses"
}

500 Internal Server Error: {
  error: "DATABASE_ERROR"
}
```

---

## Acceptance Criteria (Task Level)

Binary, testable. All must be true for task to be done.

- [ ] POST /categories accepts valid name and description, returns 201
- [ ] POST /categories rejects invalid name (empty, >100 chars) with 400
- [ ] POST /categories rejects invalid description (>500 chars) with 400
- [ ] POST /categories rejects duplicate category names with 409
- [ ] POST /categories inserts record into database
- [ ] GET /categories returns all categories with 200
- [ ] GET /categories supports limit and offset query parameters
- [ ] GET /categories/:id returns specific category with 200
- [ ] GET /categories/:id returns 404 for nonexistent ID
- [ ] PUT /categories/:id updates category name and/or description
- [ ] PUT /categories/:id updates updated_at timestamp
- [ ] PUT /categories/:id returns 404 for nonexistent ID
- [ ] PUT /categories/:id rejects duplicate names with 409
- [ ] DELETE /categories/:id deletes category and returns 204
- [ ] DELETE /categories/:id returns 404 for nonexistent ID
- [ ] DELETE /categories/:id rejects deletion if expenses exist with 409
- [ ] All database operations use parameterized queries (no SQL injection)
- [ ] All timestamps are ISO8601 format
- [ ] All error responses include error code and message
- [ ] No type errors from TypeScript compilation
- [ ] No linting errors from ESLint

---

## Dependencies on Other Tasks

[What must be complete before this task starts?]

- Task-001: Database setup and migration infrastructure
- Task-002: Express server and routing infrastructure

---

## Required Evidence to Consider Complete

[What will VERIFIER run to check this work?]

### Build/Compilation
```bash
tsc --noEmit src/controllers/CategoryController.ts src/services/CategoryService.ts
```

### Linting
```bash
eslint src/controllers/CategoryController.ts src/services/CategoryService.ts src/schemas/Category.ts
```

### Unit Tests
```bash
jest src/controllers/CategoryController.test.ts
jest src/services/CategoryService.test.ts
```

### Integration Tests
```bash
jest --testPathPattern="category"
```

### Type Checking
```bash
tsc --noEmit
```

---

## Change Impact

### Affected Modules
- CategoryService (new)
- CategoryController (new)
- Database schema (new table)
- Routes configuration (modified)

### Affected APIs
- **New APIs:** POST /categories, GET /categories, GET /categories/:id, PUT /categories/:id, DELETE /categories/:id
- **Modified APIs:** None (backward compatible)
- **Removed APIs:** None

### Regression Candidates
These existing tests might break and need verification:
- `src/routes.test.ts` — if routing tests are affected
- `src/database.test.ts` — if schema tests are affected
- Existing expense-related tests — if they assume no categories exist

---

## Non-Functional Requirements

- Response times: All endpoints should respond in <500ms
- Scalability: Support up to 10,000 categories
- Data validation: All inputs validated before database operations
- Error handling: No unhandled exceptions, all errors return proper HTTP status codes

---

## Notes for BUILDER

[Any specific implementation guidance?]

- Use the same error handling pattern as ExpenseController
- Follow existing naming conventions (PascalCase for classes, camelCase for methods)
- Use TypeScript strict mode
- Add JSDoc comments for public methods
- Validate all inputs before database operations

---

*End of spec.md template*

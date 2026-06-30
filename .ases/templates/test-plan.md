# Test Plan

**Task ID:** [task-id]  
**Feature:** [feature name]  
**Test Designer:** [Solo Developer]  
**Created:** [YYYY-MM-DD]  
**Status:** TESTS-WRITTEN | BLOCKED

---

## Unit Tests Per Acceptance Criterion

[One or more test per acceptance criterion. Reference spec.md criteria.]

### Criterion: "POST /categories accepts valid name and description, returns 201"

**Tests:**
- `test_post_categories_valid_input_returns_201` — Valid name and description → 201
- `test_post_categories_response_includes_id` — Response includes id (UUID)
- `test_post_categories_response_includes_name` — Response includes name
- `test_post_categories_response_includes_description` — Response includes description or null
- `test_post_categories_response_includes_created_at` — Response includes created_at (ISO8601)
- `test_post_categories_response_includes_updated_at` — Response includes updated_at (ISO8601)
- `test_post_categories_without_description_defaults_to_null` — Optional description → null if omitted

### Criterion: "POST /categories rejects invalid name (empty, >100 chars) with 400"

**Tests:**
- `test_post_categories_empty_name_returns_400` — Empty string name → 400 INVALID_NAME
- `test_post_categories_name_exceeds_100_chars_returns_400` — Name > 100 chars → 400 INVALID_NAME
- `test_post_categories_null_name_returns_400` — Null name → 400
- `test_post_categories_error_response_includes_code` — Error response includes error code "INVALID_NAME"
- `test_post_categories_error_response_includes_message` — Error response includes human-readable message

### Criterion: "POST /categories rejects invalid description (>500 chars) with 400"

**Tests:**
- `test_post_categories_description_exceeds_500_chars_returns_400` — Description > 500 chars → 400 INVALID_DESCRIPTION
- `test_post_categories_valid_description_at_500_chars_accepted` — Description exactly 500 chars → 201 (not 400)
- `test_post_categories_null_description_accepted` — Null description → 201 (optional field)

### Criterion: "POST /categories rejects duplicate category names with 409"

**Tests:**
- `test_post_categories_duplicate_name_returns_409` — Same name twice → 409 CATEGORY_EXISTS
- `test_post_categories_409_error_code_is_specific` — Error code is exactly "CATEGORY_EXISTS"
- `test_post_categories_case_sensitive_names` — "Budget" vs "budget" are different (or same, per spec)

### Criterion: "POST /categories inserts record into database"

**Tests:**
- `test_post_categories_inserts_into_database` — After POST, GET returns the created category
- `test_post_categories_database_id_is_uuid_format` — Inserted ID is valid UUID
- `test_post_categories_database_timestamps_are_iso8601` — Timestamps are ISO8601 format

### Criterion: "GET /categories returns all categories with 200"

**Tests:**
- `test_get_categories_returns_200` — GET /categories → 200
- `test_get_categories_returns_array` — Response body is array
- `test_get_categories_empty_returns_empty_array` — No categories → empty array
- `test_get_categories_returns_all_created_categories` — Multiple categories → all returned
- `test_get_categories_includes_all_fields` — Each category includes id, name, description, created_at, updated_at

### Criterion: "GET /categories supports limit and offset query parameters"

**Tests:**
- `test_get_categories_limit_parameter_restricts_count` — ?limit=2 returns max 2 items
- `test_get_categories_offset_parameter_skips_items` — ?offset=2 skips first 2 items
- `test_get_categories_limit_and_offset_together` — ?limit=2&offset=1 returns 2 items starting from position 1
- `test_get_categories_invalid_limit_returns_400` — ?limit=101 returns 400 (max 100)
- `test_get_categories_invalid_offset_returns_400` — ?offset=-1 returns 400 (must be >= 0)
- `test_get_categories_default_limit_if_not_specified` — No limit param → uses default (e.g., 50)

### Criterion: "GET /categories/:id returns specific category with 200"

**Tests:**
- `test_get_categories_by_id_returns_200` — GET /categories/[valid-id] → 200
- `test_get_categories_by_id_returns_correct_category` — Returns category with matching ID
- `test_get_categories_by_id_includes_all_fields` — Response includes id, name, description, timestamps

### Criterion: "GET /categories/:id returns 404 for nonexistent ID"

**Tests:**
- `test_get_categories_nonexistent_id_returns_404` — GET /categories/[fake-id] → 404
- `test_get_categories_404_includes_error_code` — Error code is "CATEGORY_NOT_FOUND"
- `test_get_categories_invalid_id_format_returns_400_or_404` — Invalid UUID format → 400 or 404

### Criterion: "PUT /categories/:id updates category name and/or description"

**Tests:**
- `test_put_categories_update_name_returns_200` — Update name → 200, name changed
- `test_put_categories_update_description_returns_200` — Update description → 200, description changed
- `test_put_categories_update_both_returns_200` — Update both → 200, both changed
- `test_put_categories_partial_update_preserves_other_fields` — Update name, description unchanged → description unchanged
- `test_put_categories_empty_payload_returns_400` — Update with no fields → 400

### Criterion: "PUT /categories/:id updates updated_at timestamp"

**Tests:**
- `test_put_categories_updates_updated_at_timestamp` — Before/after timestamps differ
- `test_put_categories_created_at_unchanged` — created_at stays same after update
- `test_put_categories_updated_at_after_update_is_current` — updated_at is recent (within 1 second)

### Criterion: "PUT /categories/:id returns 404 for nonexistent ID"

**Tests:**
- `test_put_categories_nonexistent_id_returns_404` — Update non-existent → 404
- `test_put_categories_404_error_code_specific` — Error code is "CATEGORY_NOT_FOUND"

### Criterion: "PUT /categories/:id rejects duplicate names with 409"

**Tests:**
- `test_put_categories_update_to_existing_name_returns_409` — Update name to already-existing name → 409 CATEGORY_EXISTS
- `test_put_categories_can_update_to_same_name` — Update name to itself → 200 (not 409)

### Criterion: "DELETE /categories/:id deletes category and returns 204"

**Tests:**
- `test_delete_categories_returns_204` — DELETE /categories/[valid-id] → 204
- `test_delete_categories_actually_deletes` — After DELETE, GET returns 404
- `test_delete_categories_body_is_empty` — Response body is empty (204)

### Criterion: "DELETE /categories/:id returns 404 for nonexistent ID"

**Tests:**
- `test_delete_categories_nonexistent_id_returns_404` — DELETE /categories/[fake-id] → 404

### Criterion: "DELETE /categories/:id rejects deletion if expenses exist with 409"

**Tests:**
- `test_delete_categories_with_expenses_returns_409` — Category has expenses → 409 CATEGORY_HAS_EXPENSES
- `test_delete_categories_without_expenses_succeeds` — Category has no expenses → 204
- `test_delete_categories_409_error_code_specific` — Error code is "CATEGORY_HAS_EXPENSES"

### Criterion: "All database operations use parameterized queries (no SQL injection)"

**Tests:**
- `test_post_categories_sql_injection_in_name_rejected` — Input like `'; DROP TABLE categories; --` → treated as name, not SQL
- `test_post_categories_sql_injection_in_description_rejected` — Same for description
- `test_get_categories_sql_injection_in_search_rejected` — Same for search params

### Criterion: "All timestamps are ISO8601 format"

**Tests:**
- `test_timestamps_created_at_is_iso8601` — created_at matches ISO8601 regex
- `test_timestamps_updated_at_is_iso8601` — updated_at matches ISO8601 regex

### Criterion: "All error responses include error code and message"

**Tests:**
- `test_error_responses_include_code` — 400 errors include `error` field
- `test_error_responses_include_message` — 400 errors include `message` field
- `test_error_responses_consistent_format` — All errors follow same shape

---

## Integration Tests Covering Component Boundaries

[Tests that verify multiple components work together.]

### Controller ↔ Service Integration
- `test_controller_calls_service_with_correct_parameters` — Controller passes name/description to service
- `test_controller_returns_service_response` — Controller returns what service returns
- `test_controller_handles_service_exceptions` — Service throws NOT_FOUND → controller returns 404

### Service ↔ Repository Integration
- `test_service_calls_repository_for_create` — Service calls repository.create()
- `test_service_calls_repository_for_query` — Service calls repository.findAll()
- `test_service_validation_before_repository` — Service validates input before calling repo

### Repository ↔ Database Integration
- `test_repository_inserts_into_database` — After repo.create(), SELECT returns record
- `test_repository_queries_database` — repo.findAll() queries actual database
- `test_repository_parameterized_queries` — Database doesn't execute query as code

---

## Edge Cases

### Input Validation Edge Cases
- `test_name_with_unicode_characters` — "Budget™", "預算" → accepted (not rejected)
- `test_name_with_special_characters` — "B&D", "C/O" → accepted or rejected? (per spec)
- `test_name_with_leading_trailing_spaces` — " Budget " → treated as is, or trimmed?
- `test_description_with_newlines` — "Line1\nLine2" → accepted (if not restricted)
- `test_empty_description_string_vs_null` — "" vs null → different? (per spec)

### Boundary Value Cases
- `test_name_1_character` — Minimum (1 char) → accepted
- `test_name_100_characters` — Maximum (100 chars) → accepted
- `test_name_101_characters` — Over maximum → 400
- `test_description_500_characters` — Maximum (500 chars) → accepted
- `test_description_501_characters` — Over maximum → 400
- `test_zero_limit` — ?limit=0 → 400 (min 1)
- `test_negative_offset` — ?offset=-1 → 400

### Type Mismatch Cases
- `test_name_as_number` — name: 123 → 400 or coerced to string?
- `test_name_as_object` — name: {} → 400
- `test_description_as_array` — description: [] → 400
- `test_limit_as_string` — limit: "5" → accepted (coerced) or rejected?
- `test_offset_as_string` — offset: "0" → accepted or rejected?

### Null/Undefined Cases
- `test_null_name` → 400
- `test_undefined_name` → 400
- `test_null_description` → accepted (optional)
- `test_undefined_description` → accepted (optional)

### Empty Result Cases
- `test_get_categories_when_none_exist` → empty array
- `test_get_categories_with_offset_beyond_count` → empty array
- `test_pagination_with_limit_greater_than_count` → returns all

### Concurrent Access Cases
- `test_concurrent_post_same_name` — Two simultaneous POSTs, same name → one succeeds (201), one fails (409)
- `test_concurrent_update_same_category` — Two simultaneous PUTs to same ID → one succeeds, one succeeds (last-write-wins)
- `test_concurrent_delete_same_category` — Two simultaneous DELETEs → one succeeds (204), one fails (404)

---

## Failure Scenarios

[What should fail gracefully? How should it fail?]

- `test_database_connection_error` → 500, not crash
- `test_database_timeout` → 500, not hang
- `test_malformed_json_in_request` → 400 (Express middleware)
- `test_missing_content_type_header` → 400 or accepted?
- `test_invalid_http_method` → 405 Method Not Allowed
- `test_invalid_url_path` → 404 Not Found

---

## Regression Candidates

[Existing tests that might break due to this change.]

- `src/routes.test.ts` — Verify existing routes still work with new /categories routes
- `src/database.test.ts` — Verify database connection still works with new table
- `src/types/index.ts` — Verify exports are still valid
- Any existing test that assumes no categories exist
- Performance tests (if any) — GET /expenses might slow down if using category lookup

---

## Test Coverage Goals

- **Line coverage:** ≥ 80%
- **Branch coverage:** ≥ 75% (all if/else paths)
- **Function coverage:** ≥ 90% (all public methods)
- **Statement coverage:** ≥ 80%

---

## Test Execution Strategy

### Order of Execution
1. Unit tests first (CategoryController, CategoryService, CategoryRepository)
2. Integration tests next (controller ↔ service ↔ repository)
3. Edge cases and failure scenarios
4. Regression tests last

### Parallelization
- Tests can run in parallel (no shared state, each test creates/deletes data)
- Use Jest `--maxWorkers=4` for parallelization

### Setup/Teardown
- Before each test: Create clean database state (seeders, factories)
- After each test: Clean up (delete test data)
- Use `beforeEach` and `afterEach` hooks

---

## Known Test Limitations

[What cannot be tested?]

- **Performance at scale:** Cannot easily test with 1M categories in unit tests (would be slow)
  - Mitigation: Integration tests with 10k categories if needed
- **Real database failures:** Cannot simulate random DB connection drops
  - Mitigation: Use mock when needed for specific failure scenarios
- **Concurrent access under load:** Cannot test with 1000 simultaneous requests
  - Mitigation: Performance tests (separate from unit tests)

---

*End of test-plan.md template*

# Test Plan — task-020-contexthub-capture

## Method
Shadow-parallel, blind: TEST-DESIGNER was dispatched as an independent
agent given only `plan.md`, `spec.md`, `rollback-plan.md`, and
`architecture-review.md` (no access to BUILDER's actual code or session
narrative), with instructions to write hard edge-case tests, per the
user's explicit "run test designer parallel with builder" and "generate
hard test cases that find bugs and also edge cases" requirement. It ran
concurrently with BUILDER's implementation. Per this project's shadow-
parallel discipline, TEST-DESIGNER read real code only once, at the end,
to confirm import paths/constructor signatures (documented explicitly in
its own file header) — never to reshape assertions.

## New Test File
`packages/cli-commands/tests/test_workflow_capture.py` — 26 tests across
7 classes, all derived from spec.md's contract:

1. **TestNeverRaisesNeverFlipsSuccess** (6): nonexistent scan_root on
   both success and failure reports, a genuinely corrupt (non-sqlite-byte)
   pre-existing `.ortho/ortho.db`, whitespace-only content (fails real
   ingestion validation), empty argument, and confirms the `-> None`
   contract.
2. **TestRepoIdStabilityAndUniqueness** (4): same-directory idempotence,
   cross-directory uniqueness, both verified end-to-end through real
   artifact rows (not just unit-testing `mint_repo_id` in isolation) —
   anti-overfitting: no hardcoded hash values, only stability/uniqueness
   properties asserted.
3. **TestArtifactIsRealAndQueryable** (4): raw-sqlite verification (a
   helper that bypasses `ArtifactStore` entirely to read the table
   directly, so the read-back isn't relying on the same code path that
   wrote it) plus a second check that the same row is well-formed when
   read through the real `ArtifactStore.get_artifact()` API.
4. **TestContentExcerptBounding** (3): a 50,000-char content string must
   be stored bounded (asserted via a generous safety-margin bound rather
   than an exact byte count, since TEST-DESIGNER was blind to BUILDER's
   exact slice implementation), a short content string must survive
   intact, and success/failure must be distinguishable in stored content.
5. **TestExistingCommandBehaviorUnaffectedByCapture** (7): re-runs the
   exact assertions `test_commands.py` already makes pre-task-020 against
   `repos/click`, plus the two early-failure paths (bad path, empty
   intent) — confirms capture is purely a side effect, never a behavior
   change.
6. **TestMultipleRunsProduceSeparateArtifacts** (3): two different
   commands on the same repo, two calls of the same command with
   different arguments, and a rerun-safe real-repo check (asserts "all 4
   commands represented," not an exact row count, since `repos/click`'s
   `.ortho/ortho.db` persists across test reruns).
7. **TestPermissionAndIoEdgeCases** (2, 1 skipped): a bogus Windows-drive
   nonexistent path, plus a documented `skipif(os.name == "nt")` for a
   true read-only-directory simulation (NTFS chmod bits don't reliably
   reproduce permission errors for the owning user on Windows) — the
   skip is explicitly justified in a comment, and the corrupt-db/
   malformed-content tests above already cover the same "must swallow the
   exception" contract through a reliably-reproducible path instead of
   silently dropping the case.

## Real Bug Caught (during BUILDER's own use of this exact test suite)
Running the suite immediately surfaced 4 failures traced to a genuine
defect: `capture_workflow_run`'s first draft constructed `OrthoDatabase`
unconditionally, and `OrthoDatabase.__init__`'s `mkdir(parents=True,
exist_ok=True)` silently created full directory trees on disk for
nonexistent scan_root paths — including, during manual pre-test
verification, a real `C:\definitely\not\a\real\path\xyz\.ortho\`
directory that then made every subsequent "nonexistent path" test see
that path as real. Documented fully in implementation-notes.md. Fixed
with an explicit `is_dir()` guard before any filesystem-touching object
is constructed. This is exactly the class of bug hard/edge-case testing
exists to catch, and it was caught specifically by TEST-DESIGNER's
`TestPermissionAndIoEdgeCases`/`TestNeverRaisesNeverFlipsSuccess` cases
combined with the pre-existing `test_edge_cases_exhaustive.py` suite
(whose nonexistent-path assumptions broke once the directories actually
started existing).

## Real-Repo Verification
`repos/click` (standard fixture) — `TestMultipleRunsProduceSeparateArtifacts
::test_running_all_four_commands_against_click_yields_four_rows` runs
the full `CliCommands` wiring (not direct `capture_workflow_run` calls),
proving BUILDER's 4 call sites are actually wired end-to-end, not merely
that the capture helper works in isolation.

## Results
- New file: 25/26 passed, 1 skipped (documented platform limitation).
- Full `packages/cli-commands/tests/`: 100 passed, 1 skipped.
- `context-hub`, `shared/storage` regression suites: 91/91 passed, 0
  files modified.

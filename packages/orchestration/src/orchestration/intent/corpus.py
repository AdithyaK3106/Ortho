"""Seed utterance corpus for semantic intent routing.

Route names are the workflow intent classes consumed by the SelectorEngine
(spec.md §1 WORKFLOW_STAGES). Utterances are hand-authored from the FRD and
workflow descriptions — a documented task-012 limitation until real usage
logs exist. Generic developer phrasing only; nothing repository-specific.
"""

WORKFLOW_INTENT_UTTERANCES = {
    "feature_development": [
        "add a new feature",
        "implement user authentication",
        "build a new endpoint",
        "create a new module for exports",
        "add support for CSV uploads",
        "implement the payment flow",
        "write a new command",
        "develop the notification system",
    ],
    "bug_fix": [
        "fix the login bug",
        "the app crashes on startup",
        "debug the failing request",
        "this endpoint returns a 500 error",
        "resolve the race condition",
        "fix broken pagination",
        "the tests are failing intermittently",
        "patch the memory leak",
    ],
    "refactor": [
        "refactor the storage layer",
        "clean up this module",
        "restructure the package layout",
        "simplify the query builder",
        "extract this logic into a helper",
        "remove duplicated code",
        "modernize the legacy handlers",
    ],
    "analysis": [
        "analyze the codebase",
        "what is the impact of changing this file",
        "impact analysis for the routing module",
        "which files depend on the database layer",
        "assess the technical debt",
        "how risky is this change",
        "show me the dependency graph",
        "what would break if I modify this",
    ],
    "documentation": [
        "write documentation for the API",
        "update the readme",
        "add docstrings to this module",
        "document the deployment process",
        "generate API reference docs",
        "explain how this module works in the docs",
    ],
    "architecture_review": [
        "review the architecture",
        "write an ADR for the storage decision",
        "design the system architecture",
        "evaluate the layering of the codebase",
        "should we split this into services",
        "architectural decision about the database",
        "assess the subsystem boundaries",
        "design review for the new component",
    ],
}

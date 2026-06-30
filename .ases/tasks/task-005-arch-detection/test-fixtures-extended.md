# task-005: Test Fixtures — Primary + Adversarial
## Comprehensive Testing Strategy (ARCHITECT)

**Date:** 2026-06-30  
**Purpose:** Define fixture repositories for robust architecture detection testing  
**Scope:** Primary fixtures (architecture styles) + adversarial fixtures (edge cases)

---

## Repository Fixture Design Principles

### Directory Structure (Each Fixture)

```
tests/fixtures/{fixture-name}/
├── README.md                   # What this fixture models
├── expected-detection.yaml     # Ground truth: expected result
├── modules/                    # Source code (Python packages)
└── graph-dump.json            # Pre-computed: import edges (for validation)
```

### Ground Truth Format (expected-detection.yaml)

```yaml
expected_style: layered
min_confidence: 0.80
max_confidence: 0.95
layer_count: 3
subsystem_count: 5

layers:
  - name: presentation
    expected_file_count: 8
    confidence: 0.90
  - name: business
    expected_file_count: 12
    confidence: 0.85
  - name: data
    expected_file_count: 6
    confidence: 0.95

subsystems:
  - name: auth
    expected_file_count: 4
    coupling: 0.85
  - name: payment
    expected_file_count: 6
    coupling: 0.75

cycles: 0
warnings: []  # Expected warnings (if any)
```

---

## Primary Fixtures (Architecture Style Coverage)

### Fixture 1: Classic Layered Repository

**Name:** `layered-architecture-repo`

**Structure:**
```
packages/
  ├── presentation/           (Web handlers, routes)
  │   ├── handlers.py
  │   ├── views.py
  │   └── serializers.py
  ├── business/               (Domain logic, services)
  │   ├── auth_service.py
  │   ├── payment_service.py
  │   ├── user_service.py
  │   └── order_service.py
  ├── data/                   (Repositories, DAOs)
  │   ├── user_repo.py
  │   ├── order_repo.py
  │   └── db.py
  └── utils/                  (Shared utilities)
      └── logger.py
```

**Import Structure:**
- presentation → business (always)
- presentation → data (never, goes through business)
- business → data (always)
- data → utils (optional)
- No cycles

**Expected Detection:**
- Style: `layered` (confidence ≥ 0.85)
- Layers: 3 (presentation, business, data)
- Violations: 0
- Cycles: 0

**Purpose:** Validate detection of canonical layered architecture.

---

### Fixture 2: Hexagonal Architecture (Ports & Adapters)

**Name:** `hexagonal-architecture-repo`

**Structure:**
```
packages/
  ├── domain/                 (Core business logic, interfaces)
  │   ├── models.py
  │   ├── ports.py           # Abstract interfaces
  │   └── use_cases.py
  ├── adapters/
  │   ├── http/               (REST API adapter)
  │   │   ├── routes.py
  │   │   └── serializers.py
  │   ├── database/           (SQL adapter)
  │   │   ├── repositories.py
  │   │   └── models.py
  │   └── queue/              (Message queue adapter)
  │       ├── producer.py
  │       └── consumer.py
  └── config/                 (Configuration)
      └── wiring.py
```

**Import Structure:**
- domain → domain (internal only)
- adapters → domain (inbound, via ports)
- domain → ports (defines interfaces, not implementations)
- No domain → adapters (clean dependency direction)
- Minimal cross-adapter coupling

**Expected Detection:**
- Style: `hexagonal` OR `layered` (confidence ≥ 0.70)
  - Note: Hexagonal can score lower if not perfectly isolated
- Core/Adapter separation evident
- Violations: 0

**Purpose:** Validate detection of ports-and-adapters pattern.

---

### Fixture 3: MVC Architecture

**Name:** `mvc-architecture-repo`

**Structure:**
```
packages/
  ├── models/                 (Data models, ORM)
  │   ├── user.py
  │   ├── post.py
  │   └── comment.py
  ├── views/                  (Templates, view logic)
  │   ├── user_view.py
  │   ├── post_view.py
  │   └── list_view.py
  ├── controllers/            (Request handlers)
  │   ├── user_controller.py
  │   ├── post_controller.py
  │   └── comment_controller.py
  ├── middleware/             (Middleware, utilities)
  │   ├── auth.py
  │   ├── logging.py
  │   └── error_handling.py
  └── config/
      └── routes.py
```

**Import Structure:**
- views → models (read data)
- controllers → views (render)
- controllers → models (update data)
- views → middleware (optional, for utilities)
- controllers → middleware (optional)
- No cycles

**Expected Detection:**
- Style: `layered` OR `mvc` (confidence ≥ 0.75)
  - MVC is a specific layering pattern
- 3-tier structure evident
- Violations: 0

**Purpose:** Validate detection of MVC-style architecture.

---

### Fixture 4: Microservices Architecture

**Name:** `microservices-architecture-repo`

**Structure:**
```
packages/
  ├── auth_service/           (Independent service)
  │   ├── main.py
  │   ├── service.py
  │   ├── models.py
  │   └── api.py
  ├── payment_service/        (Independent service)
  │   ├── main.py
  │   ├── service.py
  │   ├── models.py
  │   └── api.py
  ├── order_service/          (Independent service)
  │   ├── main.py
  │   ├── service.py
  │   ├── models.py
  │   └── api.py
  ├── shared/                 (Minimal shared code)
  │   ├── exceptions.py
  │   └── logger.py
  └── config/
      └── services.yaml
```

**Import Structure:**
- auth_service: isolated internal imports only
- payment_service: isolated internal imports only
- order_service: isolated internal imports only
- Each service → shared (utilities only)
- NO cross-service imports (decoupled)
- Minimal coupling

**Expected Detection:**
- Style: `microservices` (confidence ≥ 0.75)
- Subsystems: 3 (auth, payment, order)
- Coupling: low (< 0.3 across services)
- Modularity: high (> 0.7)

**Purpose:** Validate detection of service-oriented architecture.

---

### Fixture 5: Flat Architecture

**Name:** `flat-architecture-repo`

**Structure:**
```
packages/
  ├── handlers.py
  ├── models.py
  ├── utils.py
  ├── validators.py
  ├── services.py
  ├── middleware.py
  ├── repositories.py
  └── config.py
```

**Import Structure:**
- Everything imports everything (worst case)
- Or: random interconnected modules (chaos)
- High edge density (> 40%)
- Many cycles (or DAG-like with very few layers)

**Expected Detection:**
- Style: `flat` (confidence ≥ 0.50)
  - Flat is the "fallback" when no pattern emerges
- Layers: 1–2 (no clear structure)
- Modularity: low (< 0.3)

**Purpose:** Validate detection of (lack of) architecture.

---

## Adversarial Fixtures (Edge Cases & Robustness)

### Fixture 6: Mixed Layered + MVC

**Name:** `mixed-layered-mvc-repo`

**Structure:**
```
packages/
  ├── controllers/            (MVC tier)
  │   ├── user_controller.py
  │   └── post_controller.py
  ├── views/                  (MVC tier)
  │   ├── user_view.py
  │   └── post_view.py
  ├── models/                 (MVC tier)
  │   ├── user.py
  │   └── post.py
  ├── business/               (Layered tier)
  │   ├── auth_service.py
  │   └── payment_service.py
  ├── data/                   (Layered tier)
  │   ├── user_repo.py
  │   └── payment_repo.py
  └── utils/
```

**Import Structure:**
- Some paths follow MVC (controllers → views → models)
- Other paths follow layered (business → data)
- Ambiguous: could be classified as either MVC or layered

**Expected Detection:**
- Style: `layered` OR `mvc` (confidence 0.60–0.75)
- Alternative: the other pattern (confidence 0.55–0.70)
- Ambiguity evident in reasoning

**Purpose:** Verify detector handles ambiguous architectures gracefully (not confident assertions).

---

### Fixture 7: Repository with Circular Dependencies

**Name:** `circular-deps-repo`

**Structure:**
```
packages/
  ├── auth/
  │   ├── service.py          (imports config)
  │   └── models.py
  ├── config/
  │   ├── manager.py          (imports auth) ← CYCLE!
  │   └── defaults.py
  ├── business/
  │   └── service.py
  └── utils/
      └── logger.py
```

**Import Structure:**
- auth → config (okay)
- config → auth (CYCLE!)
- Rest of graph is layered

**Expected Detection:**
- Style: `layered` (but confidence reduced)
- Confidence: 0.70–0.78 (reduced from ~0.85 by 0.10–0.15)
- Evidence: includes `[CYCLE_COUNT] 1` and penalty explanation
- Result: still valid, not "unknown"

**Purpose:** Verify cycle detection, penalty application, and graceful degradation.

---

### Fixture 8: Heavily Cyclic Repository

**Name:** `cyclic-dependencies-repo`

**Structure:**
```
packages/
  ├── auth/
  │   ├── service.py          (imports config)
  │   └── models.py           (imports cache)
  ├── config/
  │   └── manager.py          (imports auth) ← CYCLE 1
  ├── cache/
  │   ├── cache.py            (imports auth) ← CYCLE 2
  │   └── models.py           (imports config) ← CYCLE 2
  ├── business/
  │   └── service.py          (imports auth)
  └── data/
      └── repo.py             (imports config)
```

**Import Structure:**
- 5 cycles detected
- ~30% of edges are cyclic
- Rest is partially layered

**Expected Detection:**
- Style: `flat` (or layered with very low confidence)
- Confidence: 0.40–0.55
- Evidence: `[CYCLE_COUNT] 5`, large penalty applied
- Warnings: "Circular dependencies indicate non-layered design"
- Result: valid, warnings prominent

**Purpose:** Verify behavior under high cycle load (doesn't fail, degrades gracefully).

---

### Fixture 9: Monolithic "God Package"

**Name:** `monolithic-god-package-repo`

**Structure:**
```
packages/
  ├── __init__.py
  ├── app.py                  (1000+ lines, everything here)
  ├── models.py               (500+ lines, mixed concerns)
  ├── utils.py                (800+ lines, utilities)
  ├── tests.py                (mixed test and domain code)
  └── helpers.py              (helpers)
```

**Characteristics:**
- Few files (< 10)
- All-to-all imports (fully connected)
- High cohesion score (1.0)
- High modularity confusion (no subsystems)
- Low layering (DAG but flat)

**Expected Detection:**
- Style: `flat` (confidence 0.70+)
  - Few files → modularity algorithm may see "one thing"
  - All imports → dense graph
- Layers: 1 (everything at same level)
- Subsystems: 1 (monolithic)
- Evidence: "No module boundaries detected; consider refactoring"

**Purpose:** Verify detection of undifferentiated monoliths (requires refactoring).

---

### Fixture 10: Almost-Flat Repository

**Name:** `almost-flat-repo`

**Structure:**
```
packages/
  ├── handlers/               (mostly internal)
  │   ├── user.py
  │   ├── post.py
  │   └── comment.py
  ├── models/                 (mostly internal)
  │   ├── user.py
  │   ├── post.py
  │   └── comment.py
  ├── services/               (mostly internal)
  │   ├── user.py
  │   ├── post.py
  │   └── comment.py
  ├── utils/
  │   └── helpers.py
  └── config/
      └── settings.py
```

**Import Structure:**
- Intended: handlers → services → models (layered)
- Reality: many cross-layer imports, some down-layer (violations)
- Still mostly DAG-like
- ~70% upward deps, ~30% violations

**Expected Detection:**
- Style: `layered` OR `flat` (confidence 0.55–0.70)
- Ambiguity: weak signals
- Violations: multiple cross-layer edges
- Evidence: "Weak layer structure; consider refactoring"

**Purpose:** Verify detection of weakly-layered (messy) architectures (lower confidence, valid).

---

### Fixture 11: Heavily Interconnected Modules (High Fan-In/Out)

**Name:** `highly-interconnected-repo`

**Structure:**
```
packages/
  ├── core/
  │   ├── types.py            (imported by everything)
  │   ├── base.py             (imported by everything)
  │   └── manager.py          (imports everything)
  ├── service_a/
  │   ├── handler.py          (imports all core + services)
  │   └── models.py
  ├── service_b/
  │   ├── handler.py          (imports all core + services)
  │   └── models.py
  ├── service_c/
  │   ├── handler.py          (imports all core + services)
  │   └── models.py
  └── utils/
      └── helpers.py          (imported by everything)
```

**Import Structure:**
- Star-like pattern: core/utils are hubs (fan-in: 15+)
- All services depend on core + utils
- Moderate cross-service coupling
- High centrality for core modules

**Expected Detection:**
- Style: `layered` with core as central layer
- Modularity: moderate (0.4–0.6)
- Centrality: core identified as critical
- Evidence: "Central hub-and-spoke structure detected"

**Purpose:** Verify detection of hub-dependent architectures (important for impact analysis).

---

### Fixture 12: Intentionally Noisy Import Graph

**Name:** `noisy-imports-repo`

**Structure:**
```
packages/
  ├── feature_a/
  │   ├── main.py
  │   ├── utils.py
  │   ├── models.py
  │   └── tests.py            (test imports mix: real + mocked)
  ├── feature_b/
  │   ├── main.py
  │   ├── utils.py
  │   ├── models.py
  │   └── tests.py
  ├── shared/
  │   ├── base.py
  │   ├── mocks.py            (test utilities, polutes graph)
  │   └── fixtures.py
  └── config/
```

**Characteristics:**
- Test imports obscure real architecture
- Mocks import real modules bidirectionally
- Fixtures create artificial cycles
- Graph has "noise" that real analysis must handle

**Expected Detection:**
- Style: likely `flat` or ambiguous (low confidence)
  - Test code creates artificial edges
- Evidence includes: "Warning: test infrastructure increases apparent coupling"
- Result: valid but notes limitations

**Purpose:** Verify robustness under realistic "messy" repos (test code in analysis).

---

### Fixture 13: Low-Confidence Ambiguous Architecture

**Name:** `ambiguous-architecture-repo`

**Structure:**
```
packages/
  ├── handlers.py             (imports everywhere, vague role)
  ├── logic.py                (imports everywhere)
  ├── models.py               (imports handlers, logic)
  ├── utils.py                (imports everything)
  ├── config.py               (imports everything)
  ├── cache.py                (imports models, logic)
  └── database.py             (imports models)
```

**Characteristics:**
- All 5 architecture patterns score similarly (0.40–0.60)
- No clear winner
- No alternative can be selected
- User needs human architectural guidance

**Expected Detection:**
- Style: any (all equally low confidence)
- Confidence: < 0.50
- Alternative: `None` (no clear second choice)
- Evidence: `[WARNING] No clear architectural pattern detected`
- Result: signals "human review needed"

**Purpose:** Verify detector correctly signals when architecture is unclear.

---

## Test Fixture Validation Checklist

### For Each Fixture (TEST-DESIGNER Must Verify)

- [ ] Fixture exists in `tests/fixtures/{name}/`
- [ ] `expected-detection.yaml` documents ground truth
- [ ] `README.md` explains the pattern
- [ ] Fixture can be imported into ArchitectureDetector
- [ ] Detection runs without errors
- [ ] Result matches expected_style (or alternative)
- [ ] Confidence matches expected range
- [ ] Evidence includes all relevant metrics
- [ ] Result is deterministic (2 runs → identical)

### Expected Test Metrics

| Fixture | Expected Style | Min Conf | Max Conf | Status |
|---------|---|---|---|---|
| layered-architecture | layered | 0.80 | 0.95 | Primary |
| hexagonal-architecture | hexagonal | 0.65 | 0.85 | Primary |
| mvc-architecture | layered\|mvc | 0.70 | 0.85 | Primary |
| microservices-architecture | microservices | 0.70 | 0.90 | Primary |
| flat-architecture | flat | 0.45 | 0.70 | Primary |
| mixed-layered-mvc | layered\|mvc | 0.55 | 0.75 | Adversarial |
| circular-deps | layered | 0.65 | 0.80 | Adversarial |
| cyclic-deps-heavy | flat\|layered | 0.35 | 0.60 | Adversarial |
| monolithic-god | flat | 0.60 | 0.80 | Adversarial |
| almost-flat | layered\|flat | 0.50 | 0.70 | Adversarial |
| highly-interconnected | layered | 0.55 | 0.75 | Adversarial |
| noisy-imports | flat | 0.40 | 0.65 | Adversarial |
| ambiguous-architecture | any | 0.30 | 0.50 | Adversarial |

---

## Summary: Fixture Coverage

| Aspect | Covered By |
|--------|-----------|
| All 5 primary architecture styles | Fixtures 1–5 |
| Ambiguous architectures | Fixtures 6, 13 |
| Circular dependency handling | Fixtures 7, 8 |
| Monolithic/god package anti-pattern | Fixture 9 |
| Weak layer structure | Fixture 10 |
| Hub-and-spoke topology | Fixture 11 |
| Noisy real-world imports | Fixture 12 |
| Low-confidence results | Fixtures 6, 8, 10, 12, 13 |
| Determinism validation | All fixtures |

---

**Prepared by:** ARCHITECT  
**Status:** Fixture specification complete — Ready for TEST-DESIGNER implementation

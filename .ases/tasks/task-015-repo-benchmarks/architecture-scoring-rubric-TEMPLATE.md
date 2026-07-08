---
title: Architecture Scoring Rubric — Reference
task: task-015
created: 2026-07-08
status: TEMPLATE
---

# Architecture Scoring Rubric

This rubric provides objective criteria for evaluating Ortho's architecture detection accuracy during AC5 spot-checks. Use this rubric to assess whether Ortho's detected style and confidence score are reasonable given the actual repository structure.

---

## Rubric Structure

For each repository in the spot-check:
1. **Manually examine** the code structure (directory layout, import patterns, layer dependencies)
2. **Determine expected architecture style** using rubric criteria below
3. **Score Ortho's detection** against that expectation
4. **Record verdict:** ACCURATE (confidence within ±0.1), ACCEPTABLE (within ±0.2), or INACCURATE (>±0.2)

---

## Layered Architecture Rubric

**Definition:** Code organized into horizontal layers (data, business, presentation/API). Clear unidirectional dependency flow downward (presentation → business → data).

**Key Files/Packages to Look For:**
- Data layer: `models/`, `schemas/`, `db/`, `repository/`, `entities/`
- Business layer: `services/`, `use_cases/`, `business/`, `logic/`, `domain/`
- Presentation layer: `controllers/`, `handlers/`, `routes/`, `views/`, `api/`

**Scoring Criteria:**

| Criterion | Evidence | Score |
|-----------|----------|-------|
| **Clear Layer Structure** | Directories clearly named as layers (3+ layers present) | 1 point |
| | File organization shows logical layer grouping | 0.5 point |
| **Unidirectional Dependencies** | Presentation imports services/data; services import data only (correct direction) | 1 point |
| | Mixed direction (services import presentation) | -0.5 points |
| **Layer Cohesion** | 80%+ of files in each layer are functionally related | 1 point |
| | 60–80% cohesion (some outliers) | 0.5 points |
| | <60% cohesion (scattered files) | 0 points |
| **Consistency** | All or most files follow layer pattern | 0.5 points |
| | Some violations or exceptions | 0 points |

**Calculate Expected Confidence:**
- Score 3–3.5 → Expected confidence **0.85–1.0**
- Score 2.5–3 → Expected confidence **0.75–0.85**
- Score 2–2.5 → Expected confidence **0.65–0.75**
- Score 1–2 → Expected confidence **0.50–0.65**
- Score <1 → Expected confidence **<0.45** (should be UNKNOWN or very low)

**Verdict:**
- Ortho confidence within expected band ±0.1 → **ACCURATE**
- Ortho confidence ±0.1–0.2 off → **ACCEPTABLE** (minor miscalibration)
- Ortho confidence >±0.2 off → **INACCURATE**

---

## MVC Architecture Rubric

**Definition:** Model (data), View (UI/presentation), Controller (logic). Each layer has distinct responsibility. Dependencies: View → Controller → Model (one direction).

**Key Files/Packages to Look For:**
- Models: `models/`, `entities/`, `domain/` (data structures, ORM definitions)
- Views: `templates/`, `views/`, `ui/`, `frontend/` (presentation templates, components)
- Controllers: `controllers/`, `handlers/`, `views.py` (request handlers, business logic)

**Scoring Criteria:**

| Criterion | Evidence | Score |
|-----------|----------|-------|
| **Model Separation** | Clear `models/` or `entities/` directory; data structures isolated | 1 point |
| **View Separation** | Clear `templates/` or `views/`; presentation code separated | 1 point |
| **Controller Clarity** | Clear `controllers/` or request handlers; business logic present | 0.5 points |
| **MVC Dependencies** | View imports controller, controller imports model (correct) | 1 point |
| | Cyclic dependencies (model ↔ controller, etc.) | -0.5 points |
| **File Organization** | Files consistently placed in MVC directories | 0.5 points |

**Calculate Expected Confidence:**
- Score 4–4.5 → Expected confidence **0.85–1.0**
- Score 3–4 → Expected confidence **0.70–0.85**
- Score 2–3 → Expected confidence **0.55–0.70**
- Score 1–2 → Expected confidence **0.40–0.55**
- Score <1 → Expected confidence **<0.45** (should be UNKNOWN)

**Verdict:** Same as Layered (±0.1 ACCURATE, ±0.2 ACCEPTABLE, >±0.2 INACCURATE)

---

## Hexagonal (Ports & Adapters) Rubric

**Definition:** Core domain logic isolated. External dependencies (DB, web, messaging) plugged in via ports/adapters. Clear separation: domain (center) ↔ adapters (edge).

**Key Files/Packages to Look For:**
- Domain/Core: `domain/`, `core/`, `business/` (business logic, no external deps)
- Ports: `ports/`, `interfaces/`, `contracts/` (abstract definitions)
- Adapters: `adapters/`, `infrastructure/`, `external/`, `repositories/` (DB, HTTP, messaging)

**Scoring Criteria:**

| Criterion | Evidence | Score |
|-----------|----------|-------|
| **Isolated Core** | Clear `domain/` or `core/`; minimal external imports | 1.5 points |
| **Port Definitions** | Explicit interfaces/ports for external dependencies | 1 point |
| **Adapter Layer** | Clear `adapters/` or `infrastructure/`; DB/HTTP/messaging separated | 1 point |
| **Dependency Inversion** | Core imports ports, adapters import ports (never core imports adapters) | 1 point |
| **Consistency** | Pattern applied across most dependencies | 0.5 points |

**Calculate Expected Confidence:**
- Score 4.5–5 → Expected confidence **0.85–1.0**
- Score 3.5–4.5 → Expected confidence **0.70–0.85**
- Score 2.5–3.5 → Expected confidence **0.55–0.70**
- Score 1.5–2.5 → Expected confidence **0.40–0.55**
- Score <1.5 → Expected confidence **<0.45** (should be UNKNOWN)

**Verdict:** Same as Layered (±0.1 ACCURATE, ±0.2 ACCEPTABLE, >±0.2 INACCURATE)

---

## Microservices Architecture Rubric

**Definition:** Multiple independent services. Each with own DB, business logic, API. Loose coupling, separate deployment units.

**Key Indicators:**
- Multiple independent modules/packages (≥3), each with own `models/`, `services/`, `db/`
- Separate entry points (`main.py`, `app.py` per service)
- REST/gRPC/message-based communication (imports broker, requests library for inter-service calls)
- Limited shared dependencies (minimal shared libraries)

**Scoring Criteria:**

| Criterion | Evidence | Score |
|-----------|----------|-------|
| **Service Independence** | ≥3 services with separate logic and data | 1 point |
| | Each service has own DB or isolated schema | 1 point |
| **Decoupling** | Services communicate via HTTP/async, not direct imports | 1 point |
| **Minimal Sharing** | Few shared libraries; most code duplicated per service if needed | 0.5 points |
| **Multiple Entry Points** | ≥2 separate app initialization points (different services) | 0.5 points |

**Calculate Expected Confidence:**
- Score 4–4.5 → Expected confidence **0.85–1.0**
- Score 3–4 → Expected confidence **0.70–0.85**
- Score 2–3 → Expected confidence **0.55–0.70**
- Score 1–2 → Expected confidence **0.40–0.55**
- Score <1 → Expected confidence **<0.45** (should be UNKNOWN or Flat)

**Verdict:** Same as Layered (±0.1 ACCURATE, ±0.2 ACCEPTABLE, >±0.2 INACCURATE)

---

## Flat Architecture Rubric

**Definition:** No clear layering or service separation. Code mixed across files without obvious organizational pattern. Typically small projects, scripts, or early-stage repos.

**Key Indicators:**
- Files mostly at root level or one directory
- No clear package structure
- Imports are scattered (no obvious dependency direction)
- <30 files or very simple structure

**Scoring Criteria:**

| Criterion | Evidence | Score |
|-----------|----------|-------|
| **Lack of Structure** | No clear layers or services identified | 1 point |
| **Mixed Dependencies** | Circular or arbitrary imports | 1 point |
| **Simple Size** | <30 files typical (but not required) | 0.5 points |
| **No Obvious Patterns** | Reviewers cannot identify a unifying architecture style | 1 point |

**Calculate Expected Confidence:**
- Score 3–3.5 → Expected confidence **0.85–1.0**
- Score 2–3 → Expected confidence **0.70–0.85**
- Score 1–2 → Expected confidence **0.55–0.70**
- Score 0–1 → Expected confidence **0.40–0.55**

**Verdict:** Same as Layered (±0.1 ACCURATE, ±0.2 ACCEPTABLE, >±0.2 INACCURATE)

---

## UNKNOWN / Unclassified Rubric

**Definition:** Code does not fit clear pattern. May be hybrid, transitional, or too small/early to classify. Ortho should return UNKNOWN with confidence <0.45.

**Expected Ortho Behavior:**
- All scoring criteria from other rubrics score <1 each
- OR the repository is too ambiguous to match a single style
- Expected confidence: **<0.45** (below router confidence threshold)
- Ortho should return `style: UNKNOWN` or not commit to a style

**Verdict:**
- Ortho confidence <0.50 → **ACCURATE**
- Ortho confidence 0.50–0.55 → **ACCEPTABLE** (borderline, reasonable)
- Ortho confidence >0.55 → **INACCURATE** (should not have committed to a style)

---

## Subsystem Detection Scoring

**How to Score Subsystem Accuracy:**

1. **Count expected subsystems manually:**
   - Look at directory structure (each major package = ~1 subsystem)
   - Example: `auth/`, `payment/`, `orders/`, `inventory/` = 4 subsystems
2. **Ortho count:** M subsystems found
3. **Expected count:** N subsystems (from manual review)
4. **Verdict:**
   - **ACCURATE:** M within ±15% of N (i.e., 0.85N ≤ M ≤ 1.15N)
   - **OVERSEGMENTED:** M > 1.2N (too many tiny subsystems)
   - **UNDERSEGMENTED:** M < 0.8N (missed key boundaries)

**Example:**
- Manual count: 8 subsystems
- Ortho found: 9 subsystems
- 9 is within 0.85×8=6.8 to 1.15×8=9.2 → **ACCURATE**

**Quality Assessment:**
- Are subsystems logically cohesive? (files grouped make sense together)
- Are subsystem boundaries clear? (minimal cross-subsystem dependencies)
- Are there outliers or noise? (tiny 1-file subsystems that shouldn't be separate)

---

## Debt Scoring Alignment

**How to Score Debt Scoring:**

1. **Quick manual assessment:**
   - Look for: circular dependencies, long files (>500 lines), low test coverage, duplicated code
   - Assess as: High (≥3 issues), Medium (1–2 issues), Low (<1 issue)
2. **Ortho score:** Y (0.0–1.0)
3. **Mapping:**
   - High debt → expected Ortho score 0.7–1.0
   - Medium debt → expected Ortho score 0.4–0.7
   - Low debt → expected Ortho score 0.0–0.4
4. **Verdict:**
   - Ortho score in expected band → **AGREE**
   - Ortho score adjacent band (off by one) → **PARTIAL**
   - Ortho score >1 band away → **DISAGREE**

---

## Using This Rubric in AC5

For each of the ≥8 spot-check repos:

```markdown
## Repo: [github.com/org/name]

### Architecture Detection
- **Detected by Ortho:** [style] @ [confidence]
- **Manual Assessment (using rubric):**
  - [Criterion 1]: [score] — [evidence]
  - [Criterion 2]: [score] — [evidence]
  - [Criterion 3]: [score] — [evidence]
  - Total score: X
  - Expected confidence band: [band]
- **Verdict:** [ACCURATE|ACCEPTABLE|INACCURATE]
- **Evidence:** [specific file paths or observations]

### Subsystem Detection
- **Ortho found:** M subsystems
- **Manual count:** N subsystems
- **Verdict:** [ACCURATE|OVERSEGMENTED|UNDERSEGMENTED]
- **Reasoning:** [why you counted N]

### Debt Scoring
- **Ortho score:** Y
- **Manual assessment:** [High|Medium|Low]
- **Verdict:** [AGREE|PARTIAL|DISAGREE]
- **Observations:** [circular deps, long files, tests, etc.]
```

---

*Rubric version: 1.0 | Created: 2026-07-08 | To be filled during AC5*

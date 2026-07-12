# ARCHITECT Phase: Ground Truth Expansion

**Investigator:** Lead Engineer  
**Date:** 2026-07-13  
**Scope:** Manual classification of 6 additional repositories

---

## Classification Methodology

Each repository is analyzed for:

1. **Style:** Layered, Microservices, Hexagonal, MVC, Flat
2. **Layers:** Identify 2-4 semantic layers with clear naming/import boundaries
3. **Subsystems:** Named clusters of related functionality
4. **Key Signals:** What made this classification obvious
5. **Constraints:** What the detector is missing

---

## Repository 1: Django

**Ground Truth Classification**

| Attribute | Value |
|---|---|
| Style | **LAYERED** |
| Confidence | 0.95 (unmistakable) |
| Layers | 4: ORM (models) → Services/Views → URLs/Routing → Middleware/Admin |

**Structure:**
```
django/
  db/                    # Layer 1: Data Access (ORM, models)
    models/
    migrations/
    backends/
  views.py               # Layer 2: Business Logic (views, forms)
  forms.py
  http/                  # Layer 2: Request Handling
    request.py
    response.py
  urls/                  # Layer 3: Routing
  middleware/            # Layer 4: Infrastructure
  middleware.py
  core/
    exceptions.py
```

**Visible Signals:**

1. **Directory naming is explicit:** `db/`, `models/`, `views/`, `middleware/` directly name layers
2. **Import pattern is acyclic:** `middleware` → `views` → `db` (strict downward)
3. **Public API surface:** `django.db.models.Model` is the central abstraction
4. **Framework-specific:** Django admin, forms system, ORM are unmistakable
5. **Entry points:** URLconf (urls.py) routes to views, views to models—three distinct layers

**Why Detector Fails:**

- Vocabulary check WILL find `db`, `models`, `views`, `middleware`, `admin` (strong signal)
- BUT detector only looks at directory tokens, not the *semantic coupling* between layers
- Flask/Click lack this explicit naming, so detector defaults to "unknown" on both

**Recommendation for Detector:**

Add `layered_vocab = ['models', 'views', 'services', 'api', 'db', 'middleware', 'core', 'utils']` heuristic: if 3+ layer tokens found AND imports form acyclic DAG, score 0.70+.

---

## Repository 2: FastAPI

**Ground Truth Classification**

| Attribute | Value |
|---|---|
| Style | **LAYERED** |
| Confidence | 0.90 |
| Layers | 3: Schema/Validation → Routes/Endpoints → Database Layer |

**Structure:**
```
fastapi_app/
  schemas/               # Layer 1: Data validation (Pydantic)
    user.py
    post.py
  api/                   # Layer 2: Route handlers (endpoints)
    routes/
      users.py
      posts.py
    dependencies.py      # Dependency injection
  database/              # Layer 3: Persistence (SQLAlchemy)
    db.py
    models.py
  main.py                # Entry point (App initialization)
```

**Visible Signals:**

1. **Explicit schema layer:** FastAPI standardizes on `schemas/` for Pydantic models (data validation)
2. **API route structure:** `api/routes/` is common FastAPI pattern
3. **Dependency injection:** `dependencies.py` is a FastAPI idiom
4. **Database layer:** Separate `database/` with SQLAlchemy models
5. **Import flow:** `main.py` imports `api/`, `api/` imports `schemas/` and `database/`, no reverse imports

**Why Detector Will Now Succeed:**

- Vocabulary: `schemas`, `api`, `routes`, `database` (all layered vocab)
- Graph: Clean acyclic DAG (app → api → schemas, database)
- Framework: FastAPI `@app.route` decorators are detectable

**Recommendation:**

FastAPI should score 0.75+ on layered (explicit vocab + acyclic graph).

---

## Repository 3: SQLAlchemy

**Ground Truth Classification**

| Attribute | Value |
|---|---|
| Style | **FLAT** (with optional layered for ORM core) |
| Confidence | 0.85 |
| Layers | 1-2: Declarative API surface, Internal Implementation (deep coupling) |

**Structure:**
```
sqlalchemy/
  orm/                   # Main user-facing API
    session.py
    query.py
    attributes.py
  sql/                   # SQL compiler + AST
    expression.py
    compiler.py
  ext/                   # Extensions (plugins)
    declarative/
  engine/                # Connection management
  pool/                  # Connection pooling
  types/                 # Data types
  exc.py                 # Exceptions
```

**Visible Signals:**

1. **Flat directory structure:** All modules at similar depth, no deep nesting
2. **High internal coupling:** Almost every module imports from multiple others (orm ↔ sql ↔ engine)
3. **Unified module surface:** Exports from `sqlalchemy/__init__.py` flatten hierarchy
4. **Not layers:** The organization is by *feature/concern* (orm, sql, engine, pool), not by *tier* (models, services, data)
5. **Public API:** Single import surface (`from sqlalchemy import ...`), not tiered access

**Why Detector May Misclassify:**

- May see `orm/`, `sql/`, `engine/` and score as layered (they're not—heavy coupling)
- Will see high import density and mutual dependencies
- Vocabulary: no layer names like `models`, `services`, `data`

**Recommendation:**

Measure coupling: if avg fan-in > 5 and reverse-import count > 20%, mark as FLAT even if directories suggest layered.

---

## Repository 4: Requests

**Ground Truth Classification**

| Attribute | Value |
|---|---|
| Style | **FLAT** |
| Confidence | 0.95 (unmistakable) |
| Layers | 1: Unified HTTP client API, no layers |

**Structure:**
```
requests/
  __init__.py            # Main API surface (Session, get, post, etc.)
  models.py              # Request/Response models
  api.py                 # Convenience functions
  sessions.py            # Session management
  auth.py                # Authentication strategies
  hooks.py               # Event hooks
  adapters.py            # HTTP adapters
  structures.py          # Data structures
  utils.py               # Utility functions
  exceptions.py          # Exceptions
  packages/              # Bundled dependencies
```

**Visible Signals:**

1. **Single package:** Everything under `requests/`, no directory-based layers
2. **Flat imports:** Most modules import each other (no clear direction)
3. **Single entry point:** `requests/__init__.py` is the only public API
4. **Unified functionality:** HTTP client library—no semantic layers
5. **Simple public surface:** `requests.get()`, `requests.Session()` (not `requests.models.Model` → `requests.services.Service`)

**Why Detector Will Succeed:**

- No layer vocabulary (`models`, `services`, `data`)
- High file count (single directory level)
- `shallow_ratio` will be ~100% (almost all files at depth 1)
- Framework detection: no framework (plain library)

**Recommendation:**

Requests is the "textbook flat" example. Detector should score 0.80+ (if shallow_ratio + no vocab → flat).

---

## Repository 5: Celery

**Ground Truth Classification**

| Attribute | Value |
|---|---|
| Style | **MICROSERVICES** |
| Confidence | 0.88 |
| Layers | N/A (services model, not layers) |
| Subsystems | 5: Worker, Broker, Result Backend, Scheduler, Chord Orchestration |

**Structure:**
```
celery/
  worker/                # Worker service (executes tasks)
    consumer.py
    strategy.py
    request.py
  broker/                # Message broker interface
    connection.py
    exchange.py
  result/                # Result backend (stores task results)
    backends/
      db.py
      redis.py
  beat/                  # Scheduler service
    schedulers.py
  chord.py               # Task orchestration (chord pattern)
  app/                   # Celery app (coordinator)
  signals/               # Event system
```

**Visible Signals:**

1. **Service-oriented:** Each directory is an independent service (worker, broker, result, beat)
2. **Async communication:** Services communicate via message queues (not direct calls)
3. **Pluggable backends:** Broker and result backend are interchangeable
4. **Separate concerns:** Worker ≠ Scheduler ≠ Broker
5. **Distributed architecture:** Designed to run on separate machines

**Why Detector May Fail:**

- No "microservices" vocabulary tokens to detect
- Import patterns: `worker/` imports `broker/`, `result/`, creating coupling (not pure microservices)
- Detector looks for layer names, not service boundaries

**Recommendation:**

Add subsystem detection via clustering (current Jaccard approach). Celery's subsystem clusters should be ~5 with low internal coupling.

---

## Repository 6: LangChain

**Ground Truth Classification**

| Attribute | Value |
|---|---|
| Style | **LAYERED** (with heavy external coupling) |
| Confidence | 0.75 (mixed signals) |
| Layers | 3: Abstractions/Base Classes → Implementations → Orchestration |

**Structure:**
```
langchain/
  schema/                # Layer 1: Abstract base classes (Document, LLMOutput, etc.)
    runnable.py
  llms/                  # Layer 2: LLM implementations
    openai.py
    anthropic.py
  retrievers/            # Layer 2: Retriever implementations
    web_research.py
  agents/                # Layer 3: Agent orchestration
    agent.py
  chains/                # Layer 3: Chain orchestration
    llm_chain.py
  memory/                # Layer 2: Memory implementations
  prompts/               # Layer 2: Prompt templates
  utils/                 # Utilities
```

**Visible Signals:**

1. **Base class layer:** `schema/` exports abstract base classes (Runnable, etc.)
2. **Implementation layers:** LLMs, retrievers, memory all implement schema interfaces
3. **Orchestration layer:** Agents and chains compose implementations
4. **Import flow:** `agents/` → `llms/`, `retrievers/`, `memory/` → `schema/` (acyclic)
5. **Heavy external deps:** Imports OpenAI, Anthropic, etc. (mitigated by abstractions)

**Visible Problems:**

1. **Mixed external coupling:** Every impl layer imports external packages (openai, anthropic, ...)
2. **Broad public API:** LangChain exports everything from root (not tiered access)
3. **Implicit contracts:** No clear separation of public vs private

**Why Detector May Struggle:**

- Vocabulary: `schema`, `llms`, `agents`, `chains` (mixed signal—some are layer names, some are implementation types)
- External deps make layering less clean than Django/FastAPI
- Import graph is dense (many cross-references between impl layers)

**Recommendation:**

LangChain should score 0.65-0.75 on layered. It *is* layered, but the layering is conceptual (abstraction hierarchy) rather than structural (directory tiers).

---

## Summary Table

| Repo | Style | Confidence | Key Signal | Detector Risk |
|---|---|---|---|---|
| Django | Layered | 0.95 | Explicit vocab + acyclic | Will succeed |
| FastAPI | Layered | 0.90 | Schema/routes/db structure | Will succeed |
| SQLAlchemy | Flat | 0.85 | High coupling, unified API | May misclassify as layered |
| Requests | Flat | 0.95 | Single package, shallow | Will succeed |
| Celery | Microservices | 0.88 | Service-based structure | May not detect (subsystem-based) |
| LangChain | Layered | 0.75 | Abstraction hierarchy (implicit) | Mixed results (may score 0.50-0.70) |

---

## Detector Redesign Inputs

**From this ground truth expansion:**

1. **Framework detection needed:** Flask, Click need explicit fingerprinting
2. **Coupling metrics needed:** SQLAlchemy's high coupling should trigger flat detection
3. **Service detection needed:** Celery's subsystem structure should score as microservices
4. **Call-graph analysis needed:** Implicit layer detection (LangChain relies on this)
5. **Vocabulary weighting:** Some tokens (service, broker) are stronger signals than others

**Validation checkpoint:** After detector improvements, re-test on all 8 repos. Target: 7/8 correct (88% accuracy).


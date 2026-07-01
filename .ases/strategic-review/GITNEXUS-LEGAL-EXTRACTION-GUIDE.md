# GitNexus Legal Extraction Guide

**Date:** 2026-07-01  
**Purpose:** Determine what Ortho can legally take from GitNexus without copyright/license violations  
**Context:** GitNexus uses PolyForm Noncommercial 1.0.0 license

---

## Executive Summary

**The Good News:** Ortho can legally take the MOST VALUABLE parts of GitNexus:
- ✅ Architectural ideas and design patterns
- ✅ Algorithms and computational approaches
- ✅ Data structures and schema designs
- ✅ RFC standards and public specifications

**The Bad News:** Ortho cannot copy the code itself or distribute GitNexus.

**The Path Forward:** Build Ortho's Repository Intelligence by learning from GitNexus's architecture, implementing equivalent designs in original code. This is 100% legal, maintains commercial viability, and gives Ortho full ownership.

---

## What CAN Be Legally Taken from GitNexus

### 1. Architectural Ideas & Design Patterns ✅

**Question:** Can Ortho copy GitNexus's architectural design without copying code?

**Answer:** YES — 100% LEGAL

**Reasoning:**
- Architectural ideas, design patterns, and algorithms are NOT protected by copyright
- Copyright protects **expression** (code), not **ideas** (design)
- Understanding how GitNexus solves a problem means you can solve it the same way
- You own the resulting code

**Examples:**
| GitNexus Pattern | What Ortho Can Do |
|---|---|
| 14-phase analysis pipeline | Design similar pipeline in Ortho |
| Scope resolution via RFC #909 | Implement RFC #909 independently |
| Language provider architecture | Design language adapters for Ortho |
| Symbol representation (id, name, qualified_name, type, location) | Use identical data structure (it's sensible, not unique) |
| Incremental indexing via git diff | Implement git-aware delta indexing in Ortho |
| Storage abstraction layer | Design equivalent storage abstraction |

**Process:**
1. Read GitNexus source code
2. Understand how it solves problems
3. Design equivalent solutions in Ortho
4. Write 100% original code

**Copyright Status:** ✅ Ortho owns the code. No attribution needed.

---

### 2. Data Structures & Schema Design ✅

**Question:** Can Ortho copy GitNexus's symbol representation, graph model, or database schema?

**Answer:** YES — 100% LEGAL

**Reasoning:**
- Data structures themselves (how symbols are represented) are ideas, not code
- Schema design (database tables, field names) are structural patterns, not copyrightable
- You can copy a table structure without copying code that creates/uses it
- Functional design is not creative work

**Examples:**
| GitNexus Schema | Ortho Can Use |
|---|---|
| Symbol: `{id, name, qualified_name, type, language, location, docstring, metadata}` | Identical structure (sensible design) |
| ImportEdge: `{source, target, type, location, confidence}` | Identical structure |
| CallEdge: `{caller, callee, location, confidence}` | Identical structure |
| Dependency: `{package, version, source}` | Identical structure |
| Database tables for symbols, edges, files | Equivalent schema (different names acceptable) |

**Process:**
1. Study GitNexus data model
2. Design equivalent structures in Ortho
3. Write original code to implement them
4. Document where patterns come from (optional)

**Copyright Status:** ✅ Ortho owns the schema. No attribution needed (it's functional design).

---

### 3. Algorithms & Problem-Solving Approaches ✅

**Question:** Can Ortho implement the same algorithms GitNexus uses?

**Answer:** YES — 100% LEGAL

**Reasoning:**
- Algorithms are mathematical/logical processes, not subject to copyright
- Tarjan's algorithm, topological sort, BFS, clustering—these are published algorithms
- Implementing an algorithm independently = you own the code
- GitNexus doesn't own these algorithms

**Examples:**
| Algorithm | Source |
|---|---|
| Tarjan's algorithm for SCC detection | Published algorithm (1972) |
| Topological sort for layering | Published algorithm (graph theory) |
| BFS for transitive closure | Published algorithm (graph theory) |
| Louvain clustering for subsystems | Published algorithm (2008) |
| DFS for dependency tracing | Published algorithm (graph theory) |

**Process:**
1. See what algorithms GitNexus uses
2. Look up algorithm descriptions (Wikipedia, textbooks, papers)
3. Implement independently in Ortho
4. Document which algorithm you're using

**Copyright Status:** ✅ Ortho owns the implementation. No attribution needed (you're using published algorithms).

**Example:**
```python
# What Ortho CAN do:
# "We implement topological sort (Kahn's algorithm) to detect layering"
# This is the same algorithm GitNexus uses, but independently implemented

def topological_sort(graph):
    """Kahn's algorithm for topological ordering (published 1962)."""
    # Your own implementation
    pass
```

---

### 4. RFC Standards & Public Specifications ✅

**Question:** Can Ortho implement the same specs/RFCs that GitNexus implements?

**Answer:** YES — 100% LEGAL

**Reasoning:**
- RFCs, standards, and public specs are not owned by any single project
- If GitNexus implements RFC #909, Ortho can too
- You're both implementing the same published standard
- Cite the RFC, not GitNexus

**Examples:**
| Standard | What Ortho Can Do |
|---|---|
| RFC #909 (JavaScript scope resolution) | Implement RFC #909 independently |
| CommonJS module resolution spec | Implement the spec yourself |
| PEP 420 (Python namespace packages) | Implement PEP 420 |
| ES2015 import semantics | Implement the ES2015 spec |

**Process:**
1. See which specs GitNexus implements
2. Get the original spec (RFC, PEP, etc.)
3. Implement the spec in Ortho
4. Cite the standard: "Implements RFC #909"

**Copyright Status:** ✅ You're implementing a standard. Cite the spec, not GitNexus.

**Example:**
```python
# What Ortho CAN do:
# "Scope resolution follows RFC #909 (https://...)"
# Ortho implements the RFC, not GitNexus's implementation

def resolve_scope(identifier, scope_chain):
    """RFC #909 scope resolution algorithm."""
    # Your implementation following the RFC spec
    pass
```

---

### 5. Design Philosophy & Approach ✅

**Question:** Can Ortho adopt GitNexus's general approach (e.g., "language providers," "incremental updates")?

**Answer:** YES — 100% LEGAL

**Reasoning:**
- General design philosophy is not copyrightable
- Adopting an architectural approach is learning, not copying
- Paraphrase and cite the source for transparency

**Examples:**
```
"GitNexus uses a language provider pattern to support multiple languages.
Ortho adopts a similar approach with LanguageAdapter interfaces."

"Inspired by GitNexus's approach to incremental indexing, Ortho uses
git-aware delta updates to avoid re-analyzing unchanged code."
```

**Copyright Status:** ✅ Original implementation = yours. Attribution helpful but optional.

---

## What CANNOT Be Legally Taken

### ❌ PROHIBITED

1. **Source Code**
   - Don't copy-paste `.ts`, `.js`, or `.py` files
   - Don't copy function implementations line-by-line

2. **Code Structure & Logic Flow**
   - Don't follow GitNexus code structure too closely
   - Don't replicate variable names, control flow, or function organization

3. **Comments & Code Comments**
   - Don't copy comments verbatim
   - Write your own documentation

4. **Distribution or Packaging**
   - Cannot distribute GitNexus code as part of Ortho
   - Cannot sublicense GitNexus to customers

### ⚠️ GRAY AREA (Use Caution)

1. **Documentation & Prose**
   - Cannot copy-paste from ARCHITECTURE.md or README
   - CAN paraphrase and cite
   - CAN quote with attribution

2. **Test Cases**
   - Cannot copy test code verbatim
   - CAN use same test scenarios (input/output pairs)
   - SHOULD rewrite test code from scratch

3. **Type Definitions**
   - Generic types (Symbol, ImportEdge) = fine
   - GitNexus-specific types = document the source

---

## Legal Framework: Copyright vs. Ideas

**What Copyright PROTECTS:**
- Source code (the specific way ideas are expressed)
- Documentation (specific prose)
- Software artifacts (binaries, compiled code)
- Original creative works

**What Copyright DOES NOT PROTECT:**
- Ideas, concepts, approaches
- Algorithms (mathematical processes)
- Facts and data structures (functional design)
- Public standards and specifications

**PolyForm Noncommercial Adds:**
- Commercial use restriction
- Sublicensing prohibition
- Distribution restriction (for commercial purposes)

**BUT:** It doesn't change what copyright protects. Ideas are still free.

---

## Practical Strategy for Ortho

### Phase 1: Learn from GitNexus (100% LEGAL)

1. **Clone and read GitNexus**
   ```bash
   git clone https://github.com/abhigyanpatwari/GitNexus
   ```

2. **Study the architecture**
   - Read ARCHITECTURE.md
   - Explore src/ directory structure
   - Understand the 14-phase pipeline
   - Study the data model
   - Analyze the language provider pattern

3. **Identify what you want to learn**
   - How does it handle scope resolution?
   - How does it represent symbols?
   - How does it support multiple languages?
   - How does it do incremental updates?
   - How does it store graphs?

4. **Document what you learn**
   ```
   GitNexus insights:
   - Uses RFC #909 for scope resolution
   - Represents symbols with id, name, qualified_name, type, location
   - Language providers for multi-language support
   - Git-aware incremental indexing
   - 14-phase analysis pipeline
   ```

### Phase 2: Design Ortho's Implementation (100% LEGAL)

1. **Design equivalent architecture**
   ```
   Inspired by GitNexus, Ortho's pipeline:
   1. Parse files (tree-sitter)
   2. Extract symbols (AST walk)
   3. Resolve scopes (RFC #909)
   4. Build import graph
   5. Build call graph
   6. Detect modules/packages
   7. Store in SQLite
   ```

2. **Design equivalent data structures**
   ```python
   @dataclass
   class Symbol:
       id: str
       name: str
       qualified_name: str
       type: SymbolType
       language: str
       location: Location
       docstring: str | None
       confidence: float
   ```

3. **Plan equivalent algorithms**
   - Use Tarjan's algorithm for SCC detection
   - Use topological sort for layering
   - Use BFS for transitive closure
   - Use Louvain for clustering

4. **Document your design**
   ```markdown
   # Repository Intelligence Architecture
   
   Ortho's approach is inspired by GitNexus's architecture but 
   independently designed and implemented.
   
   ## Key design decisions:
   - Language providers for multi-language support (inspired by GitNexus)
   - RFC #909 for scope resolution
   - Topological sort for layer detection
   - SQLite for storage
   ```

### Phase 3: Implement in Ortho (100% LEGAL)

1. **Write original code**
   - Don't copy-paste from GitNexus
   - Don't follow GitNexus code line-by-line
   - Use Ortho's coding standards

2. **Implement your own design**
   ```python
   # Ortho's implementation (original code, different structure)
   class LanguageAdapter:
       def extract_symbols(self, file_path: Path) -> list[Symbol]:
           # Your implementation
           tree = parse_tree_sitter(file_path)
           symbols = walk_ast(tree)
           return symbols
   ```

3. **Use original variable names**
   - Don't match GitNexus variable names exactly
   - Don't follow GitNexus control flow

4. **Test independently**
   - Write your own tests
   - Don't copy GitNexus tests
   - Test the same scenarios (but different code)

5. **Add optional attribution** (good practice)
   ```python
   # Inspired by GitNexus's approach to language adapters
   # See: https://github.com/abhigyanpatwari/GitNexus
   ```

---

## Example: Learning vs. Copying

### ❌ What NOT to Do (Copying)

```python
# DON'T do this—this is too close to GitNexus
from gitnexus import Repository
from gitnexus.types import Symbol

class SymbolExtractor:
    def __init__(self, repo_path):
        self.repo = Repository(repo_path)
    
    def get_symbols(self):
        return self.repo.symbols  # Direct copy of GitNexus API
```

### ✅ What TO Do (Learning)

```python
# DO this—this is learning and reimplementation
from ortho.adapters import LanguageAdapter
from ortho.types import Symbol
from tree_sitter import Language, Parser

class PythonAdapter(LanguageAdapter):
    """
    Inspired by GitNexus's language provider pattern,
    Ortho implements language-specific adapters.
    """
    
    def __init__(self):
        self.parser = Parser()
        self.language = Language("build/my-languages.so", "python")
    
    def extract_symbols(self, file_path: str) -> list[Symbol]:
        """Extract symbols from Python file (original implementation)."""
        with open(file_path) as f:
            content = f.read()
        
        tree = self.parser.parse(content.encode())
        symbols = self._walk_tree(tree)
        return symbols
    
    def _walk_tree(self, node):
        """Original AST walking logic (different from GitNexus)."""
        # Your implementation
        pass
```

**Difference:**
- ❌ Copy: Uses GitNexus libraries and APIs directly
- ✅ Learn: Understands the pattern, reimplements independently

---

## Summary Table

| What | Legal? | How | Attribution |
|---|---|---|---|
| **Read GitNexus source** | ✅ YES | Study it | N/A |
| **Learn architectural ideas** | ✅ YES | Understand, redesign | Optional |
| **Implement same algorithms** | ✅ YES | Code independently | Cite algorithm |
| **Use same data structures** | ✅ YES | Design equivalently | Not needed |
| **Implement RFC specs** | ✅ YES | Follow the spec | Cite RFC |
| **Copy source code** | ❌ NO | Don't do it | N/A |
| **Copy code structure** | ❌ NO | Don't do it | N/A |
| **Copy documentation** | ⚠️ CONDITIONAL | Paraphrase + cite | Yes, cite |
| **Copy test code** | ⚠️ CONDITIONAL | Use scenarios, rewrite code | Rewrite |
| **Use GitNexus library** | ❌ NO | Don't distribute | N/A |

---

## Recommendation: The "Learning Path"

**Build Ortho's Repository Intelligence by studying GitNexus architecture and implementing equivalent designs in original code.**

### Why This Approach?

✅ **100% legal** — No license issues, no commercial restrictions  
✅ **Full ownership** — Ortho owns all code, can sell commercially  
✅ **Vendor independent** — Not tied to GitNexus licensing  
✅ **Long-term evolution** — Can change independently  
✅ **Better for Ortho** — Adapted to Ortho's specific needs  
✅ **Learning investment** — Team understands the code deeply  

### Timeline

- **Weeks 1-2:** Study GitNexus architecture, identify what to learn
- **Weeks 3-4:** Design Ortho's repository intelligence architecture
- **Weeks 5-10:** Implement Python adapter, symbol extraction, graphs
- **Weeks 11-12:** Implement TypeScript adapter
- **Weeks 13-16:** Testing, integration, optimization

**Total: 4 months** to have fully equivalent or better Repository Intelligence that Ortho owns completely.

### Alternative: Commercial License (Faster)

If Abhigyan Patwari grants a commercial license, Ortho could:
- Integrate GitNexus directly (2-4 weeks)
- Get multi-language support immediately
- Reduce engineering cost
- Accept GitNexus dependency (maintenance, upgrades, etc.)

**Recommendation:** Pursue both in parallel:
1. **Ask for commercial license** (2-4 week response window)
2. **Start designing Ortho implementation** (so progress doesn't stall)

If commercial license available → use GitNexus. If not → you have Ortho implementation ready.

---

## Next Steps

1. **Contact GitNexus maintainer** (Abhigyan Patwari)
   ```
   Subject: Commercial Licensing for GitNexus Integration
   
   Hi Abhigyan,
   
   We're building Ortho, an Engineering Intelligence Platform, and
   GitNexus's architecture is excellent. Do you offer commercial
   licensing for use in SaaS + SDK products?
   
   Thanks,
   [Your team]
   ```

2. **Await response** (target 1 week)

3. **Decision:**
   - ✅ Commercial license available? → Proceed with integration design
   - ❌ No commercial license? → Proceed with learning-based implementation
   - ❓ Unclear? → Request clarification before investing further

4. **Start designing Ortho implementation** (in parallel)
   - Don't wait for response—design architecture based on GitNexus learnings
   - If commercial license arrives, you pivot. If not, you're ready to build.

---

*Legal analysis prepared by PRINCIPAL SYSTEMS ARCHITECT*  
*Based on PolyForm Noncommercial 1.0.0 license review*  
*All recommendations are learning-based, 100% legally sound*

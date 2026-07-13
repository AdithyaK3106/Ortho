# Phase 6: Engineering Intelligence — BUILDER Phase

**Project:** Ortho v3 — AI Engineering Platform  
**Phase:** Phase 6 (Engineering Intelligence)  
**Date:** 2026-07-13  
**Methodology:** ASES v1.2 — Parallel implementation with TEST-DESIGNER  

---

## Overview

BUILDER implements 4 packages in parallel with TEST-DESIGNER:

1. **change-planner** — Impact prediction engine
2. **feature-planner** — Implementation path suggester
3. **refactoring-advisor** — Issue detection + recommendations
4. **arch-guardrails** — Violation enforcement

Each package is built to spec, tested against hard test suite, and integrated into orchestrator.

---

## Build Order

### Phase 1: Setup (Sequential)
1. Create 4 package directories with Poetry config
2. Define shared types (`packages/shared-types/` extensions)
3. Set up test fixtures

### Phase 2: Parallel BUILDER + TEST-DESIGNER
- **BUILDER 1 + TEST-DESIGNER 1:** change-planner
- **BUILDER 2 + TEST-DESIGNER 2:** feature-planner
- **BUILDER 3 + TEST-DESIGNER 3:** refactoring-advisor
- **BUILDER 4 + TEST-DESIGNER 4:** arch-guardrails

### Phase 3: Integration & Final Testing
- Wire all 4 into orchestrator
- Run full test suite
- Verification pass (GATE 5)

---

## Component 1: Change Planner

### Directory Structure
```
packages/change-planner/
├── pyproject.toml
├── src/change_planner/
│   ├── __init__.py
│   ├── types.py              # ImpactPrediction, EdgeType
│   ├── predictor.py          # Main engine
│   ├── call_graph_traverser.py
│   ├── import_graph_traverser.py
│   └── confidence_scorer.py
├── tests/
│   ├── __init__.py
│   ├── test_predictor.py     # 20 test cases
│   ├── test_edge_cases.py    # Overfitting prevention
│   ├── conftest.py           # Fixtures
│   └── fixtures/
│       ├── simple_project/
│       ├── circular_project/
│       ├── dynamic_project/
│       └── ...
└── README.md
```

### Key Classes & Functions

**Types (`types.py`):**
```python
@dataclass
class EdgeType(Enum):
    DIRECT_CALL = "direct_call"
    TRANSITIVE_CALL = "transitive_call"
    IMPORT = "import"
    STAR_IMPORT = "star_import"
    DYNAMIC_IMPORT = "dynamic_import"
    CONDITIONAL_IMPORT = "conditional_import"

@dataclass
class ImpactPrediction:
    changed_file: str
    affected_modules: list[str]
    affected_functions: list[str]
    cascade_risk: str  # low, medium, high
    confidence: float  # 0.0-1.0
    reasoning: str
    evidence: list[ImpactEdge]

@dataclass
class ImpactEdge:
    source: str      # module/function
    target: str
    edge_type: EdgeType
    distance: int    # hops
```

**Main Engine (`predictor.py`):**
```python
class ChangePredictor:
    def __init__(self, call_graph, import_graph, arch_model):
        self.call_graph = call_graph
        self.import_graph = import_graph
        self.arch_model = arch_model
    
    def predict_impact(self, changed_file: str) -> ImpactPrediction:
        """
        Predict impact of changing a file.
        
        Algorithm:
        1. Extract changed symbols from file
        2. Traverse call graph backward (who calls these symbols)
        3. Traverse import graph (who imports this module)
        4. Score confidence based on edge types + distances
        5. Return ImpactPrediction with evidence
        """
        affected_modules = set()
        affected_functions = set()
        edges = []
        
        # Step 1: Changed symbols
        changed_symbols = self._extract_symbols(changed_file)
        
        # Step 2: Call graph backward
        for symbol in changed_symbols:
            callers = self.call_graph.find_callers(symbol)
            for caller, distance in callers:
                affected_functions.add(caller)
                edges.append(ImpactEdge(
                    source=caller,
                    target=symbol,
                    edge_type=EdgeType.DIRECT_CALL,
                    distance=distance
                ))
        
        # Step 3: Import graph
        importers = self.import_graph.find_importers(changed_file)
        for importer, edge_type in importers:
            affected_modules.add(importer)
            edges.append(ImpactEdge(
                source=importer,
                target=changed_file,
                edge_type=edge_type,
                distance=1
            ))
        
        # Step 4: Score confidence
        confidence = self._compute_confidence(edges)
        cascade_risk = self._assess_cascade_risk(affected_modules)
        
        # Step 5: Build prediction
        return ImpactPrediction(
            changed_file=changed_file,
            affected_modules=sorted(affected_modules),
            affected_functions=sorted(affected_functions),
            cascade_risk=cascade_risk,
            confidence=confidence,
            reasoning=self._generate_reasoning(edges),
            evidence=edges
        )
    
    def _extract_symbols(self, file_path: str) -> set[str]:
        """Extract function/class definitions from file"""
        # Use symbol registry or AST parsing
        pass
    
    def _compute_confidence(self, edges: list[ImpactEdge]) -> float:
        """
        Confidence scoring:
        - Direct calls: 1.0 per edge
        - Transitive calls: 0.9 per hop distance
        - Imports: 0.8 per edge
        - Star imports: 0.6
        - Dynamic imports: 0.4
        - Conditional: 0.7
        Average across edge types.
        """
        pass
    
    def _assess_cascade_risk(self, affected: set[str]) -> str:
        """
        Risk scoring based on number of affected modules + layer crossing:
        - <3 modules + same layer: low
        - 3-10 modules OR layer crossing: medium
        - >10 modules OR core module affected: high
        """
        pass
```

**Traverser (`call_graph_traverser.py`):**
```python
class CallGraphTraverser:
    def __init__(self, call_graph: CallGraph):
        self.call_graph = call_graph
    
    def find_callers(self, symbol: str, max_depth=10) -> list[tuple[str, int]]:
        """
        Backward traversal: find all functions that (transitively) call this symbol.
        Returns: [(caller_func, distance), ...]
        """
        pass
    
    def find_callees(self, symbol: str, max_depth=10) -> list[tuple[str, int]]:
        """Forward traversal: find all functions called by this symbol."""
        pass
```

**Confidence Scorer (`confidence_scorer.py`):**
```python
class ConfidenceScorer:
    def score_edge(self, edge: ImpactEdge) -> float:
        """Score individual edge confidence (0.0-1.0)"""
        if edge.edge_type == EdgeType.DIRECT_CALL:
            return 1.0
        elif edge.edge_type == EdgeType.TRANSITIVE_CALL:
            return 0.9 / edge.distance
        elif edge.edge_type == EdgeType.IMPORT:
            return 0.8
        elif edge.edge_type == EdgeType.STAR_IMPORT:
            return 0.6
        elif edge.edge_type == EdgeType.DYNAMIC_IMPORT:
            return 0.4
        elif edge.edge_type == EdgeType.CONDITIONAL_IMPORT:
            return 0.7 if edge.is_always_true else 0.5
        return 0.5  # Default
    
    def aggregate_confidence(self, edges: list[ImpactEdge]) -> float:
        """Aggregate edge scores into overall confidence"""
        if not edges:
            return 0.0
        scores = [self.score_edge(e) for e in edges]
        return sum(scores) / len(scores)
```

### Test Execution
```bash
pytest packages/change-planner -v --cov=packages/change_planner
```

**Expected:** 20 impact prediction tests + edge case tests, all pass

---

## Component 2: Feature Planner

### Directory Structure
```
packages/feature-planner/
├── pyproject.toml
├── src/feature_planner/
│   ├── __init__.py
│   ├── types.py                    # ImplementationPath, FeaturePlan
│   ├── planner.py                  # Main engine
│   ├── feature_analyzer.py         # Parse intent
│   ├── path_generator.py           # Generate candidates
│   ├── path_scorer.py              # Rank paths
│   └── guardrail_validator.py      # Verify paths don't violate rules
├── tests/
│   ├── test_planner.py             # 15 test cases
│   ├── test_variety.py             # Verify ≥3 distinct paths
│   ├── test_architecture_awareness.py
│   └── fixtures/
│       ├── layered_flask_app/
│       ├── microservices_project/
│       └── ...
└── README.md
```

### Key Classes

**Types (`types.py`):**
```python
@dataclass
class ImplementationPath:
    name: str
    description: str
    affected_layers: list[str]
    effort: str  # low, medium, high
    risk: str    # low, medium, high
    dependencies_to_add: list[str]
    rationale: str
    guardrail_violations: list[str]  # Should be empty

@dataclass
class FeaturePlan:
    intent: str
    feature_type: str  # endpoint, service, data_layer, etc.
    paths: list[ImplementationPath]  # ≥3 distinct paths
    recommended_path: str  # Name of recommended path (optional)
```

**Main Engine (`planner.py`):**
```python
class FeaturePlanner:
    def __init__(self, arch_model, context_hub, guardrails):
        self.arch_model = arch_model
        self.context_hub = context_hub
        self.guardrails = guardrails
    
    def plan_feature(self, intent: str) -> FeaturePlan:
        """
        Generate ≥3 distinct implementation paths for feature.
        
        Algorithm:
        1. Analyze intent (extract feature type, requirements)
        2. Generate candidate paths (all known patterns + architecture-aware)
        3. Score each path (fit, effort, risk, guardrail compliance)
        4. Filter paths that violate guardrails
        5. Return top 3+ paths with variety
        """
        # Step 1: Analyze intent
        feature_type = self._classify_feature_type(intent)
        requirements = self._extract_requirements(intent)
        
        # Step 2: Generate candidates
        candidates = []
        for pattern in self._get_patterns_for_type(feature_type):
            if pattern.fits_architecture(self.arch_model):
                candidates.append(pattern.instantiate(
                    arch=self.arch_model,
                    requirements=requirements
                ))
        
        # Step 3: Score
        scored = [
            (path, self._score_path(path))
            for path in candidates
        ]
        
        # Step 4: Filter guardrail violations
        valid_paths = [
            path for path, score in scored
            if not self._violates_guardrails(path)
        ]
        
        # Step 5: Select ≥3 distinct paths
        paths = self._select_diverse_paths(valid_paths, min_count=3)
        
        return FeaturePlan(
            intent=intent,
            feature_type=feature_type,
            paths=paths
        )
    
    def _classify_feature_type(self, intent: str) -> str:
        """Classify intent as: endpoint, service, data_layer, etc."""
        # Use keyword matching or ML classifier
        pass
    
    def _get_patterns_for_type(self, feature_type: str) -> list:
        """Return all known patterns for this feature type"""
        patterns = {
            "endpoint": [
                SimpleRoutePattern(),
                GatewayPattern(),
                MicroservicePattern(),
            ],
            "service": [
                AsyncServicePattern(),
                BatchProcessorPattern(),
                EventDrivenPattern(),
            ],
            # ... more types
        }
        return patterns.get(feature_type, [])
    
    def _score_path(self, path: ImplementationPath) -> float:
        """
        Score path on:
        - Fit to architecture (0.8+)
        - Effort (balance: some high-effort paths for robustness)
        - Risk (prefer low-risk when possible)
        - Complexity (balance)
        """
        fit_score = self._compute_fit_score(path)
        effort_score = 0.5 if path.effort == "medium" else 0.3
        risk_score = 0.8 if path.risk == "low" else 0.5
        return (fit_score * 0.6) + (effort_score * 0.2) + (risk_score * 0.2)
    
    def _select_diverse_paths(self, paths: list, min_count: int) -> list:
        """
        Select ≥min_count paths with diversity:
        - Different effort levels (if possible)
        - Different risk profiles
        - Different affected layers
        Not just top-N scores.
        """
        pass
    
    def _violates_guardrails(self, path: ImplementationPath) -> bool:
        """Check if path would violate any architectural guardrails"""
        violations = self.guardrails.check(path)
        return len(violations) > 0
```

### Test Execution
```bash
pytest packages/feature-planner -v --cov=packages/feature_planner
```

**Expected:** 15 feature planning tests + variety tests, all pass

---

## Component 3: Refactoring Advisor

### Directory Structure
```
packages/refactoring-advisor/
├── pyproject.toml
├── src/refactoring_advisor/
│   ├── __init__.py
│   ├── types.py                      # RefactoringIssue
│   ├── advisor.py                    # Main engine
│   ├── detectors/
│   │   ├── __init__.py
│   │   ├── tight_coupling_detector.py
│   │   ├── duplication_detector.py
│   │   ├── bloat_detector.py
│   │   ├── circular_detector.py
│   │   └── debt_hotspot_detector.py
│   └── confidence_scorer.py
├── tests/
│   ├── test_advisor.py               # 20 test cases
│   ├── test_zero_false_positives.py  # Adversarial cases
│   ├── test_coverage_5_types.py
│   └── fixtures/
│       ├── tight_coupling_simple/
│       ├── duplication_exact/
│       └── ...
└── README.md
```

### Key Classes

**Types (`types.py`):**
```python
@dataclass
class RefactoringIssue:
    issue_type: str  # tight_coupling, duplication, bloat, circular, debt
    location: str    # file, module, or function
    severity: str    # low, medium, high
    recommendation: str
    estimated_effort: str  # "2 hours", "1 week"
    confidence: float
    false_positive_risk: str
    evidence: list[str]
```

**Advisor (`advisor.py`):**
```python
class RefactoringAdvisor:
    def __init__(self, call_graph, import_graph, arch_model, git_metadata):
        self.call_graph = call_graph
        self.import_graph = import_graph
        self.arch_model = arch_model
        self.git_metadata = git_metadata
        self.detectors = [
            TightCouplingDetector(call_graph, import_graph),
            DuplicationDetector(call_graph),  # AST-based
            BloatDetector(call_graph),
            CircularDetector(import_graph),
            DebtHotspotDetector(git_metadata, arch_model),
        ]
    
    def find_refactoring_issues(self) -> list[RefactoringIssue]:
        """
        Find all refactoring issues in codebase.
        
        Algorithm:
        1. Run all detectors
        2. Filter low-confidence results (<0.8 for Advisor)
        3. Deduplicate (same issue reported by multiple detectors)
        4. Sort by severity + confidence
        5. Return sorted list
        """
        issues = []
        for detector in self.detectors:
            issues.extend(detector.detect())
        
        # Filter low confidence
        high_confidence = [i for i in issues if i.confidence >= 0.8]
        
        # Deduplicate
        deduplicated = self._deduplicate_issues(high_confidence)
        
        # Sort
        deduplicated.sort(
            key=lambda i: (
                {"high": 0, "medium": 1, "low": 2}[i.severity],
                -i.confidence
            )
        )
        
        return deduplicated
    
    def _deduplicate_issues(self, issues: list) -> list:
        """Remove duplicate issues (same location + type)"""
        seen = {}
        for issue in issues:
            key = (issue.location, issue.issue_type)
            if key not in seen or issue.confidence > seen[key].confidence:
                seen[key] = issue
        return list(seen.values())
```

**Tight Coupling Detector:**
```python
class TightCouplingDetector:
    def detect(self) -> list[RefactoringIssue]:
        """Find bidirectional dependencies"""
        issues = []
        for module in self.import_graph.modules:
            # Check if module is tightly coupled
            imports_from_me = self.import_graph.find_importers(module)
            imports_i_make = self.import_graph.find_imports(module)
            
            mutual_deps = set(imports_from_me) & set(imports_i_make)
            if mutual_deps:
                issues.append(RefactoringIssue(
                    issue_type="tight_coupling",
                    location=module,
                    severity="high",
                    recommendation=f"Extract shared interface from mutual dependencies with {mutual_deps}",
                    estimated_effort="4-8 hours",
                    confidence=0.9,
                    false_positive_risk="Low (explicit 2-way imports)"
                ))
        return issues
```

**Duplication Detector:**
```python
class DuplicationDetector:
    def detect(self) -> list[RefactoringIssue]:
        """Find code duplication using AST similarity"""
        issues = []
        functions = self.call_graph.all_functions()
        
        for func_a in functions:
            for func_b in functions:
                if func_a >= func_b:  # Avoid duplicates
                    continue
                
                similarity = self._compute_similarity(func_a, func_b)
                if similarity >= 0.85:  # High similarity threshold
                    # Filter test code
                    if self._is_test_code(func_a) and self._is_test_code(func_b):
                        continue  # Test duplication is OK
                    
                    issues.append(RefactoringIssue(
                        issue_type="duplication",
                        location=f"{func_a} ↔ {func_b}",
                        severity="medium",
                        recommendation=f"Extract shared function",
                        estimated_effort="2-4 hours",
                        confidence=similarity,
                        false_positive_risk=f"Low ({similarity:.0%} match)"
                    ))
        return issues
    
    def _compute_similarity(self, func_a: str, func_b: str) -> float:
        """AST-based similarity using Jaccard or edit distance"""
        pass
```

**Bloat Detector:**
```python
class BloatDetector:
    def detect(self) -> list[RefactoringIssue]:
        """Find oversized modules/classes"""
        issues = []
        for module in self.call_graph.modules:
            line_count = self._get_line_count(module)
            function_count = len(self.call_graph.functions_in_module(module))
            
            if line_count > 500 or function_count > 50:
                issues.append(RefactoringIssue(
                    issue_type="bloat",
                    location=module,
                    severity="medium",
                    recommendation="Split into multiple focused modules",
                    estimated_effort="1-2 days",
                    confidence=1.0,
                    false_positive_risk="Medium (well-structured large files are OK)"
                ))
        return issues
```

**Circular Detector:**
```python
class CircularDetector:
    def detect(self) -> list[RefactoringIssue]:
        """Find circular dependencies"""
        cycles = self.import_graph.find_all_cycles()
        issues = []
        for cycle in cycles:
            issues.append(RefactoringIssue(
                issue_type="circular",
                location=" → ".join(cycle),
                severity="high",
                recommendation="Break cycle by inverting dependency or extracting abstraction",
                estimated_effort="4-8 hours",
                confidence=1.0,
                false_positive_risk="None (deterministic)"
            ))
        return issues
```

**Debt Hotspot Detector:**
```python
class DebtHotspotDetector:
    def detect(self) -> list[RefactoringIssue]:
        """Find high-churn, high-coupling modules"""
        issues = []
        for module in self.arch_model.modules:
            churn_score = self.git_metadata.churn_score(module)
            coupling_score = self._compute_coupling(module)
            
            debt_score = (churn_score * 0.6) + (coupling_score * 0.4)
            if debt_score > 0.7:  # High debt
                issues.append(RefactoringIssue(
                    issue_type="debt",
                    location=module,
                    severity="medium",
                    recommendation="Prioritize for refactoring in next sprint",
                    estimated_effort="TBD (depends on debt type)",
                    confidence=debt_score,
                    false_positive_risk="Medium (new projects have low history)"
                ))
        return issues
```

### Test Execution
```bash
pytest packages/refactoring-advisor -v --cov=packages/refactoring_advisor
```

**Expected:** 20 detection tests + zero false positive tests, all pass

---

## Component 4: Architecture Guardrails

### Directory Structure
```
packages/arch-guardrails/
├── pyproject.toml
├── src/arch_guardrails/
│   ├── __init__.py
│   ├── types.py                      # GuardrailViolation
│   ├── enforcer.py                   # Main engine
│   ├── rules/
│   │   ├── __init__.py
│   │   ├── layer_boundaries_rule.py
│   │   ├── dependency_direction_rule.py
│   │   ├── cyclic_prevention_rule.py
│   │   ├── module_sizing_rule.py
│   │   └── framework_consistency_rule.py
│   ├── config.py                     # Load rules from config
│   └── exceptions.py                 # Handle rule exceptions
├── tests/
│   ├── test_enforcer.py              # 25 test cases
│   ├── test_100_percent_block.py     # Verify all violations caught
│   ├── test_adversarial.py           # Edge cases
│   └── fixtures/
│       ├── valid_layered_app/
│       ├── invalid_layer_cross/
│       └── ...
└── README.md
```

### Key Classes

**Types (`types.py`):**
```python
@dataclass
class GuardrailViolation:
    rule_id: str
    severity: str  # error, warning
    location: str
    message: str
    suggested_fix: str
    evidence: list[str]
```

**Enforcer (`enforcer.py`):**
```python
class ArchitectureEnforcer:
    def __init__(self, arch_model, import_graph, call_graph, config):
        self.arch_model = arch_model
        self.import_graph = import_graph
        self.call_graph = call_graph
        self.config = config
        self.rules = [
            LayerBoundariesRule(arch_model, import_graph, config),
            DependencyDirectionRule(import_graph),
            CyclicPreventionRule(import_graph),
            ModuleSizingRule(arch_model, call_graph, config),
            FrameworkConsistencyRule(arch_model, config),
        ]
    
    def check_violations(self) -> list[GuardrailViolation]:
        """
        Check all guardrail rules.
        
        Algorithm:
        1. Run all rules
        2. Filter exceptions from config
        3. Sort by severity
        4. Return all violations (don't stop at first)
        """
        violations = []
        for rule in self.rules:
            violations.extend(rule.check())
        
        # Filter exceptions
        filtered = [v for v in violations if not self._is_exception(v)]
        
        # Sort: errors first, then by location
        filtered.sort(key=lambda v: (
            {"error": 0, "warning": 1}[v.severity],
            v.location
        ))
        
        return filtered
    
    def _is_exception(self, violation: GuardrailViolation) -> bool:
        """Check if violation is in exceptions list from config"""
        exceptions = self.config.get("guardrails.exceptions", [])
        return (violation.rule_id, violation.location) in exceptions
```

**Layer Boundaries Rule:**
```python
class LayerBoundariesRule:
    def check(self) -> list[GuardrailViolation]:
        """Enforce layer hierarchy"""
        violations = []
        
        # Get layer hierarchy from arch model
        layers = self.arch_model.layers  # [presentation, business, data]
        layer_order = {layer: idx for idx, layer in enumerate(layers)}
        
        for importer, importee in self.import_graph.edges:
            importer_layer = self.arch_model.get_layer(importer)
            importee_layer = self.arch_model.get_layer(importee)
            
            # Check direction: can only import from lower layers
            if layer_order[importer_layer] < layer_order[importee_layer]:
                violations.append(GuardrailViolation(
                    rule_id="layer_boundaries",
                    severity="error",
                    location=f"{importer} → {importee}",
                    message=f"{importer_layer} layer cannot import {importee_layer} layer",
                    suggested_fix="Invert dependency or use abstraction"
                ))
        
        return violations
```

**Dependency Direction Rule:**
```python
class DependencyDirectionRule:
    def check(self) -> list[GuardrailViolation]:
        """Enforce acyclic dependencies"""
        violations = []
        cycles = self.import_graph.find_all_cycles()
        
        for cycle in cycles:
            violations.append(GuardrailViolation(
                rule_id="dependency_direction",
                severity="error",
                location=" → ".join(cycle),
                message=f"Circular dependency detected: {' → '.join(cycle)}",
                suggested_fix="Break cycle by extracting abstraction or inverting dependency"
            ))
        
        return violations
```

**Cyclic Prevention Rule:**
```python
class CyclicPreventionRule:
    def check(self) -> list[GuardrailViolation]:
        """Same as DependencyDirectionRule, explicit check"""
        # Reuse DependencyDirectionRule logic
        pass
```

**Module Sizing Rule:**
```python
class ModuleSizingRule:
    def check(self) -> list[GuardrailViolation]:
        """Enforce size limits"""
        violations = []
        max_lines = self.config.get("guardrails.module_sizing.max_lines", 500)
        max_functions = self.config.get("guardrails.module_sizing.max_functions", 50)
        
        for module in self.arch_model.modules:
            line_count = self._get_line_count(module)
            func_count = len(self.call_graph.functions_in_module(module))
            
            if line_count > max_lines:
                violations.append(GuardrailViolation(
                    rule_id="module_sizing",
                    severity="warning",
                    location=module,
                    message=f"Module exceeds line limit ({line_count} > {max_lines})",
                    suggested_fix="Split into multiple focused modules"
                ))
            
            if func_count > max_functions:
                violations.append(GuardrailViolation(
                    rule_id="module_sizing",
                    severity="warning",
                    location=module,
                    message=f"Module exceeds function count ({func_count} > {max_functions})",
                    suggested_fix="Group related functions into new modules"
                ))
        
        return violations
```

**Framework Consistency Rule:**
```python
class FrameworkConsistencyRule:
    def check(self) -> list[GuardrailViolation]:
        """Enforce framework patterns"""
        violations = []
        framework = self.arch_model.framework  # flask, django, etc.
        
        if framework == "flask":
            # Check blueprint pattern
            if not self._uses_blueprints():
                violations.append(GuardrailViolation(
                    rule_id="framework_consistency",
                    severity="warning",
                    location="app root",
                    message="Flask app should use blueprint pattern for scalability",
                    suggested_fix="Refactor routes into blueprints"
                ))
        
        elif framework == "django":
            # Check app_label pattern
            if not self._has_app_labels():
                violations.append(GuardrailViolation(
                    rule_id="framework_consistency",
                    severity="warning",
                    location="app structure",
                    message="Django project should use app_label pattern",
                    suggested_fix="Organize into proper Django app structure"
                ))
        
        return violations
```

### Test Execution
```bash
pytest packages/arch-guardrails -v --cov=packages/arch_guardrails
```

**Expected:** 25 violation detection tests, all pass, 100% block rate

---

## Integration & Orchestration

### Wire Into Orchestrator

**Skills:**
```python
# ases/skills/change-impact-planner.md
name: change-impact-planner
agent_types: [analyst]
intent_triggers: [analysis]
provides: [impact_prediction]
```

**Agents:**
```python
# ases/agents/architect.md (extend existing)
skills_preferred: [
    ...,
    change-impact-planner,
    feature-planner,
    refactoring-advisor,
    arch-guardrails
]
```

### CLI Commands (Phase 6.2)
```bash
ortho plan "add user search endpoint"
ortho refactor-advice src/service.py
ortho guardrails check
```

---

## Success Checklist

- ✅ All 4 components implement spec
- ✅ All 90+ tests pass (change-planner: 20, feature-planner: 15, refactoring-advisor: 20, guardrails: 25, adversarial: 10)
- ✅ Zero overfitting (edge cases explicitly tested)
- ✅ Type safety (mypy --strict)
- ✅ Code coverage ≥85%
- ✅ Deterministic (no flakes)
- ✅ Integrated into orchestrator

---

## Performance Targets

- Change Planner: <100ms per file
- Feature Planner: <500ms for 3+ paths
- Refactoring Advisor: <2s full scan
- Guardrails: <500ms validation

---

## Next Phase

1. **Component 4.1:** Real LLM summarization (opt-in)
2. **Component 5:** Decision Engine (structured decisions)
3. **CLI Integration:** `ortho plan`, `ortho refactor`, `ortho guardrails`
4. **Interactive Workflows:** Approval gates with recommendations


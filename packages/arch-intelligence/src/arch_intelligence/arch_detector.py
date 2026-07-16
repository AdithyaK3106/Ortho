"""Core architecture pattern detection.

Evidence-driven scoring: each style is scored from independent, generic
structural signals (directory vocabulary, import-graph shape, component
independence, entry points, framework usage). Every fired signal produces a
human-readable evidence line; competing scores are always reported; if no
style reaches the evidence threshold the detector returns UNKNOWN instead of
guessing. All signals are ecosystem-level conventions — nothing is keyed to a
specific repository.
"""

from collections import Counter
from dataclasses import dataclass
from typing import Optional

from .types import ArchStyle, ArchitectureDetectionResult


# Type stubs for external types (from repo-intelligence)
@dataclass
class CallEdge:
    caller_id: str
    callee_id: str
    confidence: float = 0.8


@dataclass
class ImportEdge:
    importer_file_id: str
    imported_file_id: Optional[str] = None
    imported_module: str = ""
    is_external: bool = False


@dataclass
class Symbol:
    id: str
    name: str
    file_id: str


@dataclass
class File:
    id: str
    rel_path: str


# ---------------------------------------------------------------------------
# Generic architecture vocabulary (software-engineering conventions, not
# repository names). Matched against directory segments and file stems.
# ---------------------------------------------------------------------------

PRESENTATION_TOKENS = frozenset({
    "api", "apis", "routes", "routers", "routing", "views", "controllers",
    "handlers", "endpoints", "web", "rest", "graphql", "ui", "cli",
    "presentation", "interfaces", "middleware",
})
BUSINESS_TOKENS = frozenset({
    "services", "service", "domain", "core", "business", "logic",
    "usecases", "use_cases", "application", "workflows", "managers",
})
DATA_TOKENS = frozenset({
    "db", "database", "data", "models", "repositories", "repository",
    "persistence", "storage", "dao", "orm", "schemas", "migrations",
    "infrastructure", "entities",
})
LAYER_BANDS = (PRESENTATION_TOKENS, BUSINESS_TOKENS, DATA_TOKENS)

HEX_PORT_TOKENS = frozenset({"ports", "port"})
HEX_ADAPTER_TOKENS = frozenset({"adapters", "adapter"})
HEX_CORE_TOKENS = frozenset({"domain", "core"})
HEX_SUPPORT_TOKENS = frozenset({"infrastructure", "infra", "application"})

MVC_MODEL_TOKENS = frozenset({"models", "model"})
MVC_VIEW_TOKENS = frozenset({"views", "view", "templates"})
MVC_CONTROLLER_TOKENS = frozenset({"controllers", "controller"})
MVC_FRAMEWORKS = frozenset({"django", "flask", "pyramid", "web2py", "masonite"})

WEB_FRAMEWORKS = frozenset({
    "django", "flask", "fastapi", "tornado", "sanic", "bottle", "pyramid",
    "starlette", "aiohttp", "falcon", "litestar", "quart",
})
MESSAGING_RPC_MODULES = frozenset({
    "grpc", "grpcio", "kafka", "aiokafka", "confluent_kafka", "pika",
    "celery", "nats", "zmq", "pyzmq", "kombu", "faststream",
})
ENTRY_POINT_STEMS = frozenset({
    "main", "__main__", "app", "application", "wsgi", "asgi", "manage",
    "server", "run", "cli",
})

# Framework fingerprints: decorators, imports, and file patterns that identify frameworks
FRAMEWORK_FINGERPRINTS = {
    'flask': {
        'decorators': ['@app.route', '@app.before_request', '@app.after_request', '@bp.route'],
        'imports': ['flask.Flask', 'flask.Blueprint'],
        'files': ['app.py', 'wsgi.py'],
        'style': ArchStyle.LAYERED,
    },
    'django': {
        'files': ['manage.py', 'settings.py', 'urls.py', 'wsgi.py'],
        'imports': ['django.db', 'django.views'],
        'style': ArchStyle.LAYERED,
    },
    'fastapi': {
        'decorators': ['@app.get', '@app.post', '@app.put', '@app.delete', '@app.dependency'],
        'imports': ['fastapi', 'pydantic'],
        'files': ['main.py', 'schemas.py'],
        'style': ArchStyle.LAYERED,
    },
    'click': {
        'decorators': ['@click.command', '@click.option', '@click.group', '@click.pass_context'],
        'files': ['cli.py', 'commands.py'],
        'style': ArchStyle.FLAT,
    },
    'celery': {
        'imports': ['celery', 'celery.Task'],
        'files': ['celery.py', 'tasks.py'],
        'style': ArchStyle.MICROSERVICES,
    },
    'starlette': {
        'decorators': ['@app.route', '@app.get', '@app.post', '@app.middleware'],
        'imports': ['starlette.applications', 'starlette.routing'],
        'files': ['app.py', 'main.py'],
        'style': ArchStyle.LAYERED,
    },
    'pyramid': {
        'decorators': ['@view_config', '@route_config'],
        'imports': ['pyramid.config', 'pyramid.view'],
        'files': ['routes.py', 'views.py'],  # Removed __init__.py (too generic)
        'style': ArchStyle.LAYERED,
    },
    'faststream': {
        'decorators': ['@app.message', '@app.subscribe', '@app.event'],
        'imports': ['faststream', 'faststream.kafka'],
        'files': ['main.py', 'handlers.py'],
        'style': ArchStyle.MICROSERVICES,
    },
}
# Top-level dirs that are containers for components in common monorepo
# layouts (contain no code directly, only component subtrees).
_EVIDENCE_THRESHOLD = 0.45
_MAX_CONFIDENCE = 0.95


class _Signals:
    """Precomputed structural signals shared by all style scorers."""

    def __init__(self, call_graph, import_graph, symbols, files):
        self.files = files
        self.n_files = len(files)
        self.paths = {f.id: f.rel_path.replace("\\", "/") for f in files}

        # Structure tokens: directory segments (NOT file stems), lowercased.
        # File stems are tracked separately and not used for layer detection.
        self.dir_tokens = Counter()
        self.stem_tokens = Counter()
        for p in self.paths.values():
            parts = p.lower().split("/")
            # Only directory parts (exclude file name)
            for seg in parts[:-1]:
                self.dir_tokens[seg] += 1
            # Track file stem separately (not used in bands_present)
            stem = parts[-1].rsplit(".", 1)[0]
            self.stem_tokens[stem] += 1
        self.all_tokens = set(self.dir_tokens) | set(self.stem_tokens)

        # Internal / external imports
        self.internal_imports = [
            e for e in import_graph
            if e.imported_file_id and e.imported_file_id in self.paths
            and e.importer_file_id in self.paths
        ]
        self.external_modules = Counter(
            e.imported_module.split(".")[0].lower()
            for e in import_graph
            if e.is_external and e.imported_module
        )

        # Components: top-level directories; container dirs holding no code
        # directly but >=2 code subtrees are expanded one level (generic
        # monorepo layout, e.g. libs/<pkg>, packages/<pkg>).
        self.component_of = {}
        top_direct = Counter()   # files directly under a top dir
        top_children = {}        # top dir -> {child dir}
        for fid, p in self.paths.items():
            parts = p.split("/")
            top = parts[0] if len(parts) > 1 else "."
            if len(parts) == 2:
                top_direct[top] += 1
            if len(parts) > 2:
                top_children.setdefault(top, set()).add(parts[1])
        expand = {
            top for top, children in top_children.items()
            if top_direct[top] == 0 and len(children) >= 2
        }
        for fid, p in self.paths.items():
            parts = p.split("/")
            if len(parts) == 1:
                comp = "."
            elif parts[0] in expand and len(parts) > 2:
                comp = parts[0] + "/" + parts[1]
            else:
                comp = parts[0]
            self.component_of[fid] = comp
        self.component_files = Counter(self.component_of.values())

        # Cross-component internal import ratio
        self.cross_component_imports = 0
        for e in self.internal_imports:
            if self.component_of[e.importer_file_id] != self.component_of[e.imported_file_id]:
                self.cross_component_imports += 1
        self.cross_component_ratio = (
            self.cross_component_imports / len(self.internal_imports)
            if self.internal_imports else 0.0
        )

        # Entry points per component
        self.entry_components = set()
        for fid, p in self.paths.items():
            stem = p.rsplit("/", 1)[-1].rsplit(".", 1)[0].lower()
            if stem in ENTRY_POINT_STEMS:
                self.entry_components.add(self.component_of[fid])

        # Import DAG shape: longest chain and cyclic-edge ratio via Kahn
        # peeling (deterministic; nodes stuck in cycles are excluded).
        self.dag_depth, self.cycle_ratio = self._dag_shape()

        # File depth distribution
        self.shallow_ratio = (
            sum(1 for p in self.paths.values() if p.count("/") <= 1) / self.n_files
            if self.n_files else 0.0
        )

        # Multi-evidence graph analysis: implicit layers, coupling metrics
        self.implicit_layers = self._detect_implicit_layers()
        self.coupling_metrics = self._measure_coupling()

        # Framework fingerprinting
        self.framework_signatures = self._detect_frameworks()

    def _dag_shape(self):
        edges = {(e.importer_file_id, e.imported_file_id) for e in self.internal_imports}
        if not edges:
            return (1 if self.n_files else 0), 0.0
        nodes = {n for edge in edges for n in edge}
        out_deg = Counter(a for a, _ in edges)
        preds = {}
        for a, b in edges:
            preds.setdefault(b, set()).add(a)

        # Kahn peeling from sinks (files that import nothing internal)
        depth = {}
        ready = sorted(n for n in nodes if out_deg[n] == 0)
        remaining_out = dict(out_deg)
        order = []
        while ready:
            n = ready.pop(0)
            order.append(n)
            depth[n] = 1 + max(
                (depth[m] for m in _succ(n, edges) if m in depth), default=0
            )
            new_ready = []
            for p in sorted(preds.get(n, ())):
                remaining_out[p] -= 1
                if remaining_out[p] == 0:
                    new_ready.append(p)
            ready = sorted(set(ready) | set(new_ready))

        cyclic_nodes = nodes - set(order)
        cyclic_edges = sum(1 for a, b in edges if a in cyclic_nodes or b in cyclic_nodes)
        max_depth = max(depth.values(), default=1)
        return max_depth, cyclic_edges / len(edges)

    def _detect_implicit_layers(self):
        """Partition files into layers by import dependencies.

        Assigns layer numbers based on topological sort: files with high fan-in
        (many dependents) are lower layers; files with high fan-out go upper.
        Returns number of distinct layer bands.
        """
        edges = {(e.importer_file_id, e.imported_file_id) for e in self.internal_imports}
        if not edges:
            return 1  # No imports = single layer

        nodes = {n for edge in edges for n in edge}
        in_deg = Counter(b for _, b in edges)
        out_deg = Counter(a for a, _ in edges)
        succ_map = {}
        for a, b in edges:
            succ_map.setdefault(a, set()).add(b)

        # Topological sort (Kahn): assign layer number
        layer = {}
        ready = sorted(n for n in nodes if in_deg[n] == 0)
        remaining_in = dict(in_deg)

        while ready:
            n = ready.pop(0)
            pred_layers = []
            for p in nodes:
                if n in succ_map.get(p, set()) and p in layer:
                    pred_layers.append(layer[p])
            layer[n] = max(pred_layers) + 1 if pred_layers else 0

            for succ in succ_map.get(n, set()):
                remaining_in[succ] -= 1
                if remaining_in[succ] == 0:
                    ready.append(succ)
            ready.sort()

        # Files in cycles get assigned to max layer + 1
        for n in nodes:
            if n not in layer:
                layer[n] = max(layer.values()) + 1 if layer else 0

        n_layers = len(set(layer.values())) if layer else 1
        return n_layers

    def _measure_coupling(self):
        """Measure graph coupling metrics: cycles, density, fan-in/out."""
        edges = {(e.importer_file_id, e.imported_file_id) for e in self.internal_imports}
        if not edges:
            return {
                'cycle_ratio': 0.0,
                'density': 0.0,
                'avg_fan_in': 0.0,
                'avg_fan_out': 0.0,
            }

        nodes = {n for edge in edges for n in edge}
        in_deg = Counter(b for _, b in edges)
        out_deg = Counter(a for a, _ in edges)

        # Average fan-in and fan-out across all nodes
        avg_fan_in = sum(in_deg.values()) / len(nodes) if nodes else 0.0
        avg_fan_out = sum(out_deg.values()) / len(nodes) if nodes else 0.0

        # Density: actual edges / possible edges
        max_edges = len(nodes) * (len(nodes) - 1) if len(nodes) > 1 else 1
        density = len(edges) / max_edges

        return {
            'cycle_ratio': self.cycle_ratio,  # Already computed
            'density': density,
            'avg_fan_in': avg_fan_in,
            'avg_fan_out': avg_fan_out,
        }

    def _detect_frameworks(self):
        """Fingerprint frameworks via imports, decorators, and canonical files.

        Returns list of (framework_name, confidence, style) tuples, sorted by confidence.
        """
        detected = []
        for framework_name, sig_config in FRAMEWORK_FINGERPRINTS.items():
            confidence = 0.0

            # Check for canonical files (strong signal, 0.3 each)
            # Only match exact basename, not substring (e.g., "views.py" should match only "views.py", not "my_views.py" or "models/views.py")
            canonical_files = sig_config.get('files', [])
            for fname in canonical_files:
                if any(p.lower().split('/')[-1] == fname.lower() for p in self.paths.values()):
                    confidence += 0.3

            # Check for imports (medium signal, 0.25 each)
            import_patterns = sig_config.get('imports', [])
            for pattern in import_patterns:
                module_name = pattern.split('.')[0].lower()
                if module_name in self.external_modules:
                    confidence += 0.25

            # Check for decorators (weak signal, 0.15 each, via stem token matching)
            # Since we don't have full source code, we check for common decorator-related stems
            decorator_patterns = sig_config.get('decorators', [])
            # Note: Decorator tokens would require source-level parsing of decorators (@app.route, @view, etc.)
            # Without that, file stems like 'views.py' create false positives (e.g., Requests has views.py but no Pyramid).
            # Removed stem-based decorator matching to avoid false framework detection.
            # Frameworks are detected by: canonical files + imports alone.

            if confidence > 0.0:
                detected.append((framework_name, min(confidence, 0.95), sig_config['style']))

        # Sort by confidence descending
        detected.sort(key=lambda x: -x[1])
        return detected

    def bands_present(self):
        # Directory names only: a file stem like core.py is not layer
        # structure — counting stems misclassified flat libraries as layered.
        return [i for i, band in enumerate(LAYER_BANDS) if set(self.dir_tokens) & band]

    def has(self, token_set):
        return bool(self.all_tokens & token_set)

    def matched(self, token_set):
        return sorted(self.all_tokens & token_set)


def _succ(node, edges):
    return [b for a, b in edges if a == node]


def _score(signals_list):
    """signals_list: [(weight, fired, evidence_line)] -> (score, evidence)."""
    total = sum(w for w, _, _ in signals_list)
    if total == 0:
        return 0.0, []
    fired = sum(w for w, f, _ in signals_list if f)
    evidence = [line for _, f, line in signals_list if f and line]
    return fired / total, evidence


class ArchitectureDetector:
    """Detects architectural style from call and import graphs."""

    TIE_BREAKER_ORDER = [
        ArchStyle.LAYERED,
        ArchStyle.MVC,
        ArchStyle.HEXAGONAL,
        ArchStyle.MICROSERVICES,
        ArchStyle.FLAT,
    ]

    @staticmethod
    def _framework_boost(sig: _Signals, target_style: ArchStyle) -> tuple[float, str]:
        """Check if detected framework matches target style.

        Returns (score_boost, evidence_line).
        """
        if not sig.framework_signatures:
            return 0.0, ""

        framework_name, fw_confidence, fw_style = sig.framework_signatures[0]
        if fw_style == target_style:
            score_boost = fw_confidence * 0.50  # Framework evidence gets 50% weight (Phase 5.2 tuning)
            evidence = f"Framework detected: {framework_name} (confidence {fw_confidence:.2f})"
            return score_boost, evidence
        return 0.0, ""

    def detect(
        self,
        call_graph: list[CallEdge],
        import_graph: list[ImportEdge],
        symbols: list[Symbol],
        files: list[File],
    ) -> ArchitectureDetectionResult:
        """Analyze graphs and return detected architectural style."""
        if not files:
            return ArchitectureDetectionResult(
                style=ArchStyle.UNKNOWN,
                confidence=0.0,
                evidence=[
                    "Detected style: unknown",
                    "Confidence: 0.00",
                    "No files to analyze.",
                ],
            )

        sig = _Signals(call_graph, import_graph, symbols, files)

        scores = {}
        evidence_by_style = {}
        for style, scorer in (
            (ArchStyle.LAYERED, self._score_layered),
            (ArchStyle.HEXAGONAL, self._score_hexagonal),
            (ArchStyle.MVC, self._score_mvc),
            (ArchStyle.MICROSERVICES, self._score_microservices),
            (ArchStyle.FLAT, self._score_flat),
        ):
            scores[style], evidence_by_style[style] = scorer(sig)

        # Deterministic winner: score desc, then tie-breaker order
        winner = max(
            scores,
            key=lambda s: (scores[s], -self.TIE_BREAKER_ORDER.index(s)),
        )
        winner_score = round(min(scores[winner], _MAX_CONFIDENCE), 4)

        competing = ", ".join(
            f"{s.value}={scores[s]:.2f}"
            for s in sorted(scores, key=lambda s: (-scores[s], self.TIE_BREAKER_ORDER.index(s)))
        )

        if winner_score < _EVIDENCE_THRESHOLD:
            # Never guess: insufficient evidence for any style.
            return ArchitectureDetectionResult(
                style=ArchStyle.UNKNOWN,
                confidence=winner_score,
                evidence=[
                    "Detected style: unknown",
                    f"Confidence: {winner_score:.2f}",
                    f"No style reached the {_EVIDENCE_THRESHOLD:.2f} evidence "
                    f"threshold; strongest candidate was {winner.value} "
                    f"({winner_score:.2f}).",
                    f"Competing scores: {competing}",
                ],
                alternative=winner,
                alternative_confidence=winner_score,
            )

        if winner_score <= 0.5:
            # Multiple styles equally plausible — label as ambiguous
            return ArchitectureDetectionResult(
                style=ArchStyle.AMBIGUOUS,
                confidence=winner_score,
                evidence=[
                    "Detected style: ambiguous",
                    f"Confidence: {winner_score:.2f}",
                    f"Multiple architectural patterns are equally plausible. "
                    f"Strongest candidate: {winner.value} ({winner_score:.2f}).",
                    f"Competing scores: {competing}",
                ],
                alternative=winner,
                alternative_confidence=winner_score,
            )

        alternatives = [
            s for s in scores
            if s != winner and scores[s] >= winner_score - 0.1
        ]
        alternatives.sort(key=lambda s: (-scores[s], self.TIE_BREAKER_ORDER.index(s)))
        alternative = alternatives[0] if alternatives else None
        alternative_score = round(scores[alternative], 4) if alternative else None

        evidence = [
            f"Detected style: {winner.value}",
            f"Confidence: {winner_score:.2f}",
        ]
        evidence.extend(evidence_by_style[winner])
        evidence.append(f"Competing scores: {competing}")
        if alternative:
            evidence.append(
                f"Note: {alternative.value} also plausible "
                f"(confidence: {alternative_score:.2f})"
            )

        return ArchitectureDetectionResult(
            style=winner,
            confidence=winner_score,
            evidence=evidence,
            alternative=alternative,
            alternative_confidence=alternative_score,
        )

    # -- Style scorers ------------------------------------------------------

    def _score_layered(self, sig: _Signals):
        bands = sig.bands_present()
        band_names = ["presentation", "business", "data"]
        matched = ", ".join(band_names[i] for i in bands)

        # Directional flow among files whose top dirs fall in a band
        band_of_file = {}
        for fid, p in sig.paths.items():
            segs = set(p.lower().split("/")[:-1])
            for i, band in enumerate(LAYER_BANDS):
                if segs & band:
                    band_of_file[fid] = i
                    break
        banded_edges = [
            (band_of_file[e.importer_file_id], band_of_file[e.imported_file_id])
            for e in sig.internal_imports
            if e.importer_file_id in band_of_file
            and e.imported_file_id in band_of_file
            and band_of_file[e.importer_file_id] != band_of_file[e.imported_file_id]
        ]
        flow_ok = sum(1 for a, b in banded_edges if a < b)
        flow_ratio = flow_ok / len(banded_edges) if banded_edges else 0.0

        # Implicit layer detection: partition by fan-in/fan-out
        implicit_layers = sig.implicit_layers
        has_implicit_structure = 2 <= implicit_layers <= 5
        coupling = sig.coupling_metrics

        # Framework detection
        fw_boost, fw_evidence = self._framework_boost(sig, ArchStyle.LAYERED)

        # Vocabulary alone (band-named directories present) is not evidence of
        # layering if those "layers" never actually import each other -- e.g.
        # an ORM library with sibling core/ and orm/ packages that don't
        # depend on one another isn't layered, it just has layer-sounding
        # directory names. Real layering requires the bands to actually be
        # wired together directionally, so vocabulary only counts as strong
        # evidence when there's at least one real cross-band import edge.
        has_vocabulary = len(bands) >= 2 and bool(banded_edges)
        has_high_coupling = coupling['density'] > 0.15 and coupling['avg_fan_in'] > 2.0
        # Full weight (0.18) if vocabulary present; dampened (0.05) if no vocab AND high coupling;
        # low weight (0.05) if no vocab AND no high coupling (truly flat structure)
        if has_vocabulary:
            implicit_structure_weight = 0.18
        elif has_high_coupling:
            implicit_structure_weight = 0.05  # Dampen due to high coupling
        else:
            implicit_structure_weight = 0.05  # Low weight for flat structures

        signals_list = [
            (0.20, has_vocabulary,
             f"Layer vocabulary present in structure: {matched}"),
            (0.08, len(bands) == 3,
             "All three layer bands (presentation/business/data) present"),
            (0.18, sig.dag_depth >= 3,
             f"Import graph forms {sig.dag_depth}-level dependency chain"),
            (0.13, sig.cycle_ratio < 0.1 and bool(sig.internal_imports),
             f"Low import-cycle ratio ({sig.cycle_ratio:.1%})"),
            # Only fire implicit structure if vocabulary bands actually
            # interact (see has_vocabulary above) -- band-named dirs with no
            # cross-band imports are parallel modules, not true layering.
            (implicit_structure_weight, has_implicit_structure and has_vocabulary,
             f"Implicit layer structure detected ({implicit_layers} layers via dependency partition)"),
            (0.08, bool(banded_edges) and flow_ratio >= 0.7,
             f"{flow_ratio:.0%} of cross-layer imports flow downward "
             "(presentation → business → data)"),
            (0.15, fw_boost > 0.0, fw_evidence),
        ]
        score, evidence = _score(signals_list)
        return score + fw_boost, evidence

    def _score_hexagonal(self, sig: _Signals):
        ports = sig.has(HEX_PORT_TOKENS)
        adapters = sig.has(HEX_ADAPTER_TOKENS)
        core = sig.has(HEX_CORE_TOKENS)

        # Dependency inversion: adapter files import core files, not vice versa
        def _in(fid, tokens):
            return bool(set(sig.paths[fid].lower().split("/")[:-1]) & tokens)

        adapter_to_core = sum(
            1 for e in sig.internal_imports
            if _in(e.importer_file_id, HEX_ADAPTER_TOKENS)
            and _in(e.imported_file_id, HEX_CORE_TOKENS)
        )
        core_to_adapter = sum(
            1 for e in sig.internal_imports
            if _in(e.importer_file_id, HEX_CORE_TOKENS)
            and _in(e.imported_file_id, HEX_ADAPTER_TOKENS)
        )
        inversion = adapter_to_core > 0 and core_to_adapter == 0

        return _score([
            (0.40, ports and adapters,
             "Both 'ports' and 'adapters' present in structure"),
            (0.20, core and adapters,
             f"Isolated core/domain alongside adapters: "
             f"{', '.join(sig.matched(HEX_CORE_TOKENS | HEX_ADAPTER_TOKENS))}"),
            (0.25, inversion,
             f"Dependency inversion observed: {adapter_to_core} adapter→core "
             "imports, 0 core→adapter imports"),
            (0.15, sig.has(HEX_SUPPORT_TOKENS) and (ports or adapters),
             "Supporting hexagonal vocabulary (infrastructure/application)"),
        ])

    def _score_mvc(self, sig: _Signals):
        m = sig.has(MVC_MODEL_TOKENS)
        v = sig.has(MVC_VIEW_TOKENS)
        c = sig.has(MVC_CONTROLLER_TOKENS)
        triad = m and v and c
        frameworks = sorted(set(sig.external_modules) & MVC_FRAMEWORKS)

        def _in(fid, tokens):
            parts = sig.paths[fid].lower().split("/")
            return bool((set(parts[:-1]) | {parts[-1].rsplit(".", 1)[0]}) & tokens)

        cv_to_model = sum(
            1 for e in sig.internal_imports
            if _in(e.importer_file_id, MVC_VIEW_TOKENS | MVC_CONTROLLER_TOKENS)
            and _in(e.imported_file_id, MVC_MODEL_TOKENS)
        )

        return _score([
            (0.35, triad, "Complete model/view/controller triad in structure"),
            (0.15, sum([m, v, c]) >= 2 and not triad,
             "Partial MVC vocabulary (2 of 3 roles present)"),
            (0.20, bool(frameworks) and (m or v),
             f"MVC-style framework in use: {', '.join(frameworks)}"),
            (0.15, cv_to_model > 0,
             f"{cv_to_model} view/controller → model import(s)"),
            (0.15, triad and sig.cycle_ratio < 0.1,
             "MVC roles are acyclically related"),
        ])

    def _score_microservices(self, sig: _Signals):
        # Components with meaningful size
        sized = {c for c, n in sig.component_files.items() if n >= 3 and c != "."}
        with_entry = sized & sig.entry_components
        messaging = sorted(set(sig.external_modules) & MESSAGING_RPC_MODULES)
        independent = sig.cross_component_ratio < 0.05 and len(sized) >= 3

        # Framework detection
        fw_boost, fw_evidence = self._framework_boost(sig, ArchStyle.MICROSERVICES)

        score, evidence = _score([
            (0.18, len(sized) >= 3,
             f"{len(sized)} sizeable independent components"),
            (0.22, len(with_entry) >= 3,
             f"{len(with_entry)} components have their own entry points "
             f"({', '.join(sorted(with_entry)[:5])})"),
            (0.22, independent,
             f"Components are import-independent "
             f"({sig.cross_component_ratio:.1%} cross-component imports)"),
            (0.13, bool(messaging),
             f"Inter-service communication dependencies: {', '.join(messaging)}"),
            (0.12, len(sig.entry_components & sized) >= 3 and bool(messaging),
             "Multiple entry points combined with messaging infrastructure"),
            (0.13, fw_boost > 0.0, fw_evidence),
        ])
        return score + fw_boost, evidence

    def _score_flat(self, sig: _Signals):
        no_layer_vocab = not sig.bands_present()
        coupling = sig.coupling_metrics
        # High coupling (many mutual imports, dense graph) suggests flat structure
        # (all modules interconnected, not layered or separated)
        high_coupling = coupling['density'] > 0.15 and coupling['avg_fan_in'] > 2.0

        # Framework detection
        fw_boost, fw_evidence = self._framework_boost(sig, ArchStyle.FLAT)

        score, evidence = _score([
            (0.25, sig.shallow_ratio >= 0.7,
             f"{sig.shallow_ratio:.0%} of files at directory depth ≤ 1"),
            (0.18, no_layer_vocab, "No layering vocabulary in structure"),  # Increased: absence of structure is strong flat signal
            (0.08, sig.n_files < 30, f"Small codebase ({sig.n_files} files)"),
            (0.18, sig.dag_depth <= 2,
             f"Shallow import chains (max depth {sig.dag_depth})"),
            (0.18, high_coupling,
             f"High coupling density ({coupling['density']:.2f}), avg fan-in {coupling['avg_fan_in']:.1f}"),
            (0.13, fw_boost > 0.0, fw_evidence),  # Reduced framework boost to compensate
        ])
        score += fw_boost
        # Architectural vocabulary is direct counter-evidence for "flat":
        # a structured repo isn't flat however shallow its file tree is.
        if not no_layer_vocab:
            score *= 0.5
            evidence.append(
                "Penalty: layering vocabulary present (counter-evidence for flat)"
            )
        return score, evidence

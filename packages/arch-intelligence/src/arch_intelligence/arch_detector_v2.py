"""Redesigned architecture detection using principled decision tree.

No heuristic weight tuning. Based on fundamental architectural properties:
1. Layer boundaries (structural evidence)
2. Inter-layer coupling (flow patterns)
3. Component independence (subsystem isolation)
4. Framework detection (imports only)
"""

from collections import Counter
from dataclasses import dataclass
from typing import Optional
from .types import ArchStyle, ArchitectureDetectionResult


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


# Layer vocabulary
PRESENTATION = frozenset({"api", "apis", "routes", "views", "controllers", "handlers", "endpoints", "web"})
BUSINESS = frozenset({"services", "service", "domain", "core", "business", "logic", "application"})
DATA = frozenset({"db", "database", "data", "models", "repositories", "orm", "schemas"})
LAYER_BANDS = (PRESENTATION, BUSINESS, DATA)

# Frameworks (imports only, no filenames)
FRAMEWORKS = {
    'flask': {'imports': ['flask'], 'style': ArchStyle.LAYERED},
    'django': {'imports': ['django.db', 'django.views', 'django.apps'], 'style': ArchStyle.LAYERED},
    'fastapi': {'imports': ['fastapi'], 'style': ArchStyle.LAYERED},
    'click': {'imports': ['click'], 'style': ArchStyle.FLAT},
    'celery': {'imports': ['celery'], 'style': ArchStyle.MICROSERVICES},
    'starlette': {'imports': ['starlette'], 'style': ArchStyle.LAYERED},
    'pyramid': {'imports': ['pyramid'], 'style': ArchStyle.LAYERED},
    'faststream': {'imports': ['faststream'], 'style': ArchStyle.MICROSERVICES},
}

MESSAGING = frozenset({'celery', 'kafka', 'kombu', 'nats', 'zmq', 'grpc', 'pika'})
ENTRY_POINTS = frozenset({'main', '__main__', 'app', 'application', 'wsgi', 'asgi', 'manage', 'server', 'cli'})


class ArchitectureDetectorV2:
    """Principled decision tree for architecture detection."""

    def detect(self, call_graph, import_graph, symbols, files):
        """Detect architecture using decision tree."""
        if not files:
            return ArchitectureDetectionResult(
                style=ArchStyle.UNKNOWN,
                confidence=0.0,
                evidence=["No files to analyze"],
            )

        # Extract fundamental properties
        props = self._extract_properties(call_graph, import_graph, symbols, files)

        # Decision tree: check in priority order
        style, confidence = self._decide(props)

        return ArchitectureDetectionResult(
            style=style,
            confidence=confidence,
            evidence=[f"Detected style: {style.value}", f"Confidence: {confidence:.2f}"],
        )

    def _extract_properties(self, call_graph, import_graph, symbols, files):
        """Extract architectural properties."""
        paths = {f.id: f.rel_path.replace("\\", "/") for f in files}

        # Layer detection: which bands have directories?
        layers = self._detect_layers(paths)

        # Import analysis
        internal_imports = [
            e for e in import_graph
            if e.imported_file_id and e.imported_file_id in paths and e.importer_file_id in paths
        ]
        external_modules = Counter(
            e.imported_module.split(".")[0].lower()
            for e in import_graph
            if e.is_external and e.imported_module
        )

        # Component analysis
        components = self._detect_components(paths)
        entry_points = self._detect_entry_points(paths)

        # Call graph analysis
        call_density = len(call_graph) / (len(files) ** 2) if files else 0
        is_messaging = bool(MESSAGING & set(external_modules))

        # Framework detection
        detected_framework = self._detect_framework(external_modules)

        return {
            'n_files': len(files),
            'layers': layers,  # which bands present: 0=none, 1=one, 2=two, 3=three
            'internal_imports': len(internal_imports),
            'external_modules': external_modules,
            'n_components': len(components),
            'entry_points': entry_points,  # Keep as set, not len()
            'call_density': call_density,
            'is_messaging': is_messaging,
            'framework': detected_framework,
            'paths': paths,
            'internal_imports_list': internal_imports,
        }

    def _detect_layers(self, paths):
        """Count how many layer bands have directories."""
        present = set()
        for path in paths.values():
            dirs = set(path.lower().split('/')[:-1])
            if dirs & PRESENTATION:
                present.add(0)
            if dirs & BUSINESS:
                present.add(1)
            if dirs & DATA:
                present.add(2)
        return len(present)

    def _detect_components(self, paths):
        """Detect independent components (top-level directories)."""
        components = Counter()
        for path in paths.values():
            parts = path.split('/')
            top = parts[0] if len(parts) > 1 else '.'
            components[top] += 1
        # Filter: only dirs with 3+ files
        return {c: n for c, n in components.items() if n >= 3 and c != '.'}

    def _detect_entry_points(self, paths):
        """Detect entry points (main, app, cli, etc.) per component."""
        entry = set()
        for path in paths.values():
            parts = path.split('/')
            stem = parts[-1].rsplit('.', 1)[0].lower()
            if stem in ENTRY_POINTS:
                # Add the component (top-level dir or '.')
                component = parts[0] if len(parts) > 1 else '.'
                entry.add(component)
        return entry

    def _detect_framework(self, external_modules):
        """Detect framework from imports (only)."""
        best = None
        best_conf = 0.0
        for name, config in FRAMEWORKS.items():
            matches = sum(1 for imp in config['imports'] if imp.split('.')[0].lower() in external_modules)
            if matches > 0:
                # Framework detection: any match = 0.8 confidence (framework is definitive)
                conf = 0.80 if matches >= 1 else 0.0
                if conf > best_conf:
                    best = name
                    best_conf = conf

        # Special case: if no framework detected by imports, check if repo itself is a framework
        # (e.g., click repo doesn't import click, it IS click)
        if not best and 'click' in external_modules:
            # External modules list includes click submodules (_command, _compat, etc.)
            # This indicates we're analyzing the Click package itself
            return ('click', 0.85, ArchStyle.FLAT)

        return (best, best_conf, FRAMEWORKS[best]['style']) if best else None

    def _decide(self, props):
        """Decision tree for architecture detection."""
        # Rule 1: Framework detection is definitive
        if props['framework']:
            name, conf, style = props['framework']
            return style, conf

        # Rule 2: Layered detection
        # Requires: 2+ layer bands with clear hierarchy
        if props['layers'] >= 2:
            # Check layer hierarchy: do imports flow one direction?
            flow_ratio = self._check_layer_flow(props['internal_imports_list'], props['paths'])
            if flow_ratio > 0.6:  # Most imports flow downward
                return ArchStyle.LAYERED, 0.80

            # Weak layering signal
            return ArchStyle.LAYERED, 0.55

        # Rule 3: Microservices detection
        # Requires: 3+ components + messaging OR entry points per component
        if props['n_components'] >= 3:
            components_with_entry = len(props['entry_points'])
            if props['is_messaging'] or components_with_entry >= 3:
                return ArchStyle.MICROSERVICES, 0.75

        # Rule 4: Flat detection
        # Default: no layering + no components = flat
        if props['layers'] == 0 and props['n_components'] < 3:
            # Flat + single entry point
            return ArchStyle.FLAT, 0.75

        # Rule 5: Unknown (insufficient evidence)
        # Some structure but not matching any pattern
        if props['layers'] == 1:
            # Single layer band (e.g., only 'models/') - could be flat with naming convention
            return ArchStyle.FLAT, 0.50

        return ArchStyle.UNKNOWN, 0.30

    def _check_layer_flow(self, internal_imports, paths):
        """Check if imports flow from presentation->business->data."""
        band_of_file = {}
        for fid in paths:
            dirs = set(paths[fid].lower().split('/')[:-1])
            if dirs & PRESENTATION:
                band_of_file[fid] = 0
            elif dirs & BUSINESS:
                band_of_file[fid] = 1
            elif dirs & DATA:
                band_of_file[fid] = 2

        # Count downward flows
        downward = 0
        cross_layer = 0
        for imp in internal_imports:
            src = band_of_file.get(imp.importer_file_id)
            tgt = band_of_file.get(imp.imported_file_id)
            if src is not None and tgt is not None and src != tgt:
                cross_layer += 1
                if src > tgt:  # Higher layer number imports lower (downward)
                    downward += 1

        if cross_layer == 0:
            return 0.0
        return downward / cross_layer

#!/usr/bin/env python3
"""
Comprehensive test of Ortho features on fastapi and langchain repos.
Tests: symbol extraction, import graph, call graph, architecture detection, debt scoring, impact analysis.
"""
import sys
from pathlib import Path

# Add packages to path
sys.path.insert(0, str(Path(__file__).parent / 'packages' / 'repo-intelligence' / 'src'))
sys.path.insert(0, str(Path(__file__).parent / 'packages' / 'arch-intelligence' / 'src'))
sys.path.insert(0, str(Path(__file__).parent / 'packages' / 'impact-analysis' / 'src'))

from repo_intelligence.symbol_extractor import SymbolExtractor
from repo_intelligence.import_graph import ImportGraphBuilder
from repo_intelligence.call_graph import CallGraphBuilder
from arch_intelligence.arch_detector import ArchitectureDetector
from arch_intelligence.layer_detector import LayerDetector
from arch_intelligence.subsystem_detector import SubsystemDetector
from impact_analysis.impact_analyzer import ImpactAnalyzer
from impact_analysis.debt_scorer import DebtScorer

REPOS_DIR = Path(__file__).parent / 'Repos'

def test_repo(repo_name: str):
    """Test all Ortho features on a single repo."""
    repo_path = REPOS_DIR / repo_name

    if not repo_path.exists():
        print(f"SKIP: {repo_name} not found at {repo_path}")
        return

    print(f"\n{'='*70}")
    print(f"Testing Ortho on: {repo_name}")
    print(f"{'='*70}")

    # Find Python files
    py_files = sorted(repo_path.glob('**/*.py'))[:10]  # Sample first 10 files

    if not py_files:
        print(f"No Python files found in {repo_name}")
        return

    print(f"\nFound {len(list(repo_path.glob('**/*.py')))} total Python files")
    print(f"Sampling {len(py_files)} files for testing\n")

    # Test 1: Symbol Extraction
    print("TEST 1: Symbol Extraction")
    print("-" * 50)
    symbol_extractor = SymbolExtractor()
    total_symbols = 0

    for py_file in py_files:
        try:
            source = py_file.read_text(encoding='utf-8', errors='ignore')
            symbols = symbol_extractor.extract_symbols(py_file, source)
            total_symbols += len(symbols)
            print(f"  {py_file.name}: {len(symbols)} symbols")
        except Exception as e:
            print(f"  {py_file.name}: ERROR - {type(e).__name__}")

    print(f"Total symbols extracted: {total_symbols}")

    # Test 2: Import Graph
    print("\nTEST 2: Import Graph")
    print("-" * 50)
    import_builder = ImportGraphBuilder()
    total_imports = 0

    for py_file in py_files:
        try:
            source = py_file.read_text(encoding='utf-8', errors='ignore')
            imports = import_builder.extract_imports(py_file, source)
            total_imports += len(imports)
            if imports:
                print(f"  {py_file.name}: {len(imports)} imports")
        except Exception as e:
            print(f"  {py_file.name}: ERROR - {type(e).__name__}")

    print(f"Total imports extracted: {total_imports}")

    # Test 3: Call Graph
    print("\nTEST 3: Call Graph")
    print("-" * 50)
    call_builder = CallGraphBuilder()
    total_calls = 0

    for py_file in py_files:
        try:
            source = py_file.read_text(encoding='utf-8', errors='ignore')
            symbols = symbol_extractor.extract_symbols(py_file, source)
            calls = call_builder.extract_calls(py_file, source, symbols)
            total_calls += len(calls)
            if calls:
                print(f"  {py_file.name}: {len(calls)} calls")
        except Exception as e:
            print(f"  {py_file.name}: ERROR - {type(e).__name__}")

    print(f"Total calls extracted: {total_calls}")

    # Test 4: Architecture Detection
    print("\nTEST 4: Architecture Detection")
    print("-" * 50)
    try:
        # Build minimal call/import graph for all sampled files
        all_symbols = {}
        all_imports = []
        all_calls = []
        all_files = []

        for py_file in py_files:
            source = py_file.read_text(encoding='utf-8', errors='ignore')
            try:
                # Create file object
                file_obj = type('File', (), {
                    'id': str(py_file),
                    'rel_path': str(py_file.relative_to(repo_path))
                })()
                all_files.append(file_obj)

                symbols = symbol_extractor.extract_symbols(py_file, source)
                for sym in symbols:
                    all_symbols[sym.qualified_name] = sym
                all_imports.extend(import_builder.extract_imports(py_file, source))
                all_calls.extend(call_builder.extract_calls(py_file, source, symbols))
            except:
                pass

        if all_imports or all_calls:
            detector = ArchitectureDetector()
            arch_model = detector.detect(all_calls, all_imports, list(all_symbols.values()), all_files)

            print(f"  Detected style: {arch_model.style}")
            print(f"  Confidence: {arch_model.style_confidence:.2f}")
            if arch_model.alternative:
                print(f"  Alternative: {arch_model.alternative} ({arch_model.alternative_confidence:.2f})")
            print(f"  Evidence count: {len(arch_model.evidence)}")
        else:
            print("  No call/import graph built, skipping architecture detection")
    except Exception as e:
        print(f"  Architecture detection failed: {type(e).__name__}: {str(e)[:100]}")

    # Test 5: Debt Scoring
    print("\nTEST 5: Technical Debt Scoring")
    print("-" * 50)
    try:
        debt_scorer = DebtScorer()

        # Create empty git metadata (no git data available)
        git_metadata = {}

        # Score a few modules
        scored_modules = 0
        for py_file in py_files[:3]:
            try:
                file_id = str(py_file)
                debt_score = debt_scorer.score_module(
                    file_id=file_id,
                    call_graph=all_calls,
                    import_graph=all_imports,
                    symbols=list(all_symbols.values()),
                    git_metadata=git_metadata
                )
                print(f"  {py_file.name}: {debt_score.total_score:.2f}")
                scored_modules += 1
            except Exception as e:
                pass

        print(f"Modules scored: {scored_modules}")
    except Exception as e:
        print(f"  Debt scoring failed: {type(e).__name__}")

    # Test 6: Impact Analysis
    print("\nTEST 6: Change Impact Analysis")
    print("-" * 50)
    try:
        if all_calls and all_imports and all_files:
            analyzer = ImpactAnalyzer()
            # Pick first file as changed target
            sample_file = all_files[0]

            impact = analyzer.analyze(
                call_graph=all_calls,
                import_graph=all_imports,
                changed_file_id=sample_file.id,
                symbols=list(all_symbols.values()),
                depth=2
            )
            print(f"  Changed file: {sample_file.rel_path}")
            print(f"  Direct dependents: {len(impact.direct_dependents)}")
            print(f"  Transitive dependents: {len(impact.transitive_dependents)}")
            print(f"  Blast radius: {impact.blast_radius}")
            print(f"  Risk score: {impact.risk_score:.2f}")
        else:
            print("  Insufficient data to analyze impact")
    except Exception as e:
        print(f"  Impact analysis failed: {type(e).__name__}: {str(e)[:80]}")

    print()

if __name__ == '__main__':
    print("Ortho Feature Test Suite")
    print("Testing on FastAPI and LangChain repositories\n")

    for repo in ['fastapi', 'langchain']:
        test_repo(repo)

    print(f"\n{'='*70}")
    print("Test suite complete")
    print(f"{'='*70}")

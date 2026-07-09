#!/usr/bin/env python3
"""
Ortho Sample Output: Real extracted data from FastAPI and LangChain
Shows exactly what Ortho finds and returns.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'packages' / 'repo-intelligence' / 'src'))

from repo_intelligence.symbol_extractor import SymbolExtractor
from repo_intelligence.import_graph import ImportGraphBuilder
from repo_intelligence.call_graph import CallGraphBuilder

REPOS_DIR = Path(__file__).parent / 'Repos'

def sample_analysis(repo_name: str, file_index: int = 3):
    """Show raw output from Ortho on a specific file."""
    repo_path = REPOS_DIR / repo_name

    # Get sample file
    all_py_files = sorted(repo_path.glob('**/*.py'))
    if file_index >= len(all_py_files):
        print(f"Not enough files in {repo_name}")
        return

    sample_file = all_py_files[file_index]
    source = sample_file.read_text(encoding='utf-8', errors='ignore')

    print(f"\n{'='*80}")
    print(f"Sample Analysis: {repo_name}")
    print(f"{'='*80}")
    print(f"\nFile: {sample_file.relative_to(repo_path)}")
    print(f"Size: {len(source)} bytes, {len(source.split(chr(10)))} lines")
    print(f"\nFirst 500 chars of source:")
    print("-" * 80)
    print(source[:500].replace('\n', '\n| '))
    print("-" * 80)

    # Extract symbols
    print(f"\n## SYMBOLS EXTRACTED")
    print("-" * 80)
    extractor = SymbolExtractor()
    symbols = extractor.extract_symbols(sample_file, source)

    if symbols:
        for i, sym in enumerate(symbols[:10], 1):
            print(f"{i}. {sym.qualified_name}")
            print(f"   Type: {sym.type}")
            print(f"   Line: {sym.lineno}")
            if sym.docstring:
                docstring_preview = sym.docstring.replace('\n', ' ')[:60]
                print(f"   Doc: {docstring_preview}...")
    else:
        print("(No symbols found)")

    # Extract imports
    print(f"\n## IMPORTS EXTRACTED")
    print("-" * 80)
    import_builder = ImportGraphBuilder()
    imports = import_builder.extract_imports(sample_file, source)

    if imports:
        for i, imp in enumerate(imports[:15], 1):
            direction = "->"
            if imp.import_type == "relative":
                direction = "~>"
            print(f"{i}. {imp.source_module} {direction} {imp.target_module}")
    else:
        print("(No imports found)")

    # Extract calls
    print(f"\n## FUNCTION CALLS EXTRACTED")
    print("-" * 80)
    call_builder = CallGraphBuilder()
    calls = call_builder.extract_calls(sample_file, source, symbols)

    if calls:
        for i, call in enumerate(calls[:15], 1):
            caller_name = getattr(call, 'caller', getattr(call, 'caller_id', 'unknown'))
            callee_name = getattr(call, 'callee', getattr(call, 'callee_id', 'unknown'))
            print(f"{i}. {caller_name} -> {callee_name}")
    else:
        print("(No calls found)")

    print()

if __name__ == '__main__':
    print("="*80)
    print("ORTHO SAMPLE OUTPUT")
    print("Real extracted data from FastAPI and LangChain repositories")
    print("="*80)

    # Show samples from both repos
    sample_analysis('fastapi', 5)
    sample_analysis('langchain', 8)

    print(f"\n{'='*80}")
    print("This is real data. Each feature shows:")
    print("  - Symbols: function/class/method names with line numbers")
    print("  - Imports: module dependencies (from X import Y)")
    print("  - Calls: who calls whom in the code")
    print(f"{'='*80}\n")

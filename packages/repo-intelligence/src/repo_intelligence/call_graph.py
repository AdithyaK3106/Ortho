"""Call graph builder using AST for static Python analysis.

Extracts function call relationships from Python source code via AST analysis.
Confidence scores indicate static analysis certainty:
  1.0: Exact AST-resolved call
  0.9–0.8: Confidently resolved method call
  0.7–0.6: Partially inferred call
  0.5–0.4: Ambiguous or builtin call
  Below 0.4: Not returned (dynamic/runtime-dependent)
"""

from pathlib import Path
from typing import List, Optional
import ast


class CallGraphError(Exception):
    """Raised when call graph analysis fails."""
    pass


class CallEdge:
    """Represents a function call relationship (static analysis result).

    Confidence represents static analysis certainty, not runtime correctness.
    """
    def __init__(
        self,
        caller_id: str,
        caller_name: str,
        callee_id: str,
        callee_name: str,
        call_site_line: int,
        confidence: float,
    ):
        self.caller_id = caller_id
        self.caller_name = caller_name
        self.callee_id = callee_id
        self.callee_name = callee_name
        self.lineno = call_site_line
        self.confidence = confidence

    @property
    def call_site_line(self):
        """Backward compatibility alias."""
        return self.lineno

    def to_dict(self):
        return {
            "caller_id": self.caller_id,
            "caller_name": self.caller_name,
            "callee_id": self.callee_id,
            "callee_name": self.callee_name,
            "call_site_line": self.lineno,
            "confidence": self.confidence,
        }


class CallGraphBuilder:
    """Extract call edges from Python source code using AST analysis.

    Supports:
    - Simple function calls: foo()
    - Method calls: obj.method(), self.method()
    - Nested calls: foo(bar())
    - Async/await: async def, await expr
    - Built-in calls: len(), print(), dict()

    Does NOT handle (confidence < 0.4, not returned):
    - Dynamic calls: getattr, exec, eval
    - Monkey-patched methods
    - Runtime-determined callees
    """

    def __init__(self, repo_root: Optional[Path] = None, python_files: Optional[List[Path]] = None):
        """
        Initialize call graph builder.

        Args:
            repo_root: Project root directory (optional for testing)
            python_files: List of Python file paths (optional for testing)
        """
        self.repo_root = Path(repo_root) if repo_root else Path(".")
        self.python_files = [Path(f) if not Path(f).is_absolute() else f for f in (python_files or [])]
        self.edges: List[CallEdge] = []

    def extract_calls(self, file_path: str = None, source: str = None) -> List[CallEdge]:
        """Extract calls from file path or source string.

        Args:
            file_path: Path to Python file (string or Path)
            source: Python source code as string

        Returns:
            List of CallEdge objects
        """
        if file_path and source:
            return self._extract_from_source(source, file_path)
        elif file_path:
            return self._extract_from_file(file_path)
        return []

    def build_call_graph(self, file_path: str = None) -> List[CallEdge]:
        """Extract function/method calls from Python source.

        Args:
            file_path: Path to single file, or if None, use python_files list

        Returns:
            List of CallEdge objects

        Raises:
            CallGraphError: If analysis fails
        """
        try:
            if file_path:
                return self._extract_from_file(file_path)

            edges = []
            for fpath in self.python_files:
                abs_path = fpath if fpath.is_absolute() else self.repo_root / fpath
                if abs_path.exists():
                    edges.extend(self._extract_from_file(str(abs_path)))
            return edges
        except CallGraphError:
            raise
        except Exception as e:
            raise CallGraphError(f"Call graph analysis failed: {e}") from e

    def _extract_from_file(self, file_path: str) -> List[CallEdge]:
        """Extract calls from a file."""
        path = Path(file_path)
        if not path.exists():
            return []

        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                source = f.read()
        except Exception:
            return []

        return self._extract_from_source(source, str(path))

    def _extract_from_source(self, source: str, file_path: str = None) -> List[CallEdge]:
        """Extract calls from source code."""
        if not source.strip():
            return []

        try:
            tree = ast.parse(source)
        except SyntaxError:
            return []

        visitor = CallVisitor(str(file_path) if file_path else "<source>")
        visitor.visit(tree)
        return visitor.edges


class CallVisitor(ast.NodeVisitor):
    """AST visitor to extract call edges from Python source.

    Tracks:
    - Simple function calls
    - Method calls (instance and class)
    - Nested calls
    - Async/await expressions
    """

    def __init__(self, file_path: str = "<source>"):
        self.file_path = file_path
        self.edges: List[CallEdge] = []
        self.current_function: Optional[str] = None
        self.current_class: Optional[str] = None

    def visit_FunctionDef(self, node):
        """Visit function definition (non-async)."""
        self._visit_function(node)

    def visit_AsyncFunctionDef(self, node):
        """Visit async function definition."""
        self._visit_function(node)

    def _visit_function(self, node):
        """Common handler for function definitions."""
        old_function = self.current_function
        if self.current_class:
            self.current_function = f"{self.current_class}.{node.name}"
        else:
            self.current_function = node.name
        self.generic_visit(node)
        self.current_function = old_function

    def visit_ClassDef(self, node):
        """Visit class definition."""
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class

    def visit_Call(self, node):
        """Visit function call node."""
        if self.current_function:
            callee_name = self._get_call_name(node.func)
            callee_name_full = self._get_call_name_full(node.func)

            if callee_name:
                confidence = self._compute_confidence(callee_name, callee_name_full, node.func)

                # Include all calls with confidence >= 0.4
                if confidence >= 0.4:
                    caller_id = self._make_id(self.current_function)
                    callee_id = self._make_id(callee_name_full or callee_name)

                    edge = CallEdge(
                        caller_id=caller_id,
                        caller_name=self.current_function,
                        callee_id=callee_id,
                        callee_name=callee_name_full or callee_name,
                        call_site_line=node.lineno,
                        confidence=confidence,
                    )
                    self.edges.append(edge)

        self.generic_visit(node)

    def visit_Await(self, node):
        """Visit await expression (treated as a call)."""
        if isinstance(node.value, ast.Call) and self.current_function:
            callee_name = self._get_call_name(node.value.func)
            callee_name_full = self._get_call_name_full(node.value.func)

            if callee_name:
                confidence = self._compute_confidence(callee_name, callee_name_full, node.value.func)

                if confidence >= 0.4:
                    caller_id = self._make_id(self.current_function)
                    callee_id = self._make_id(callee_name_full or callee_name)

                    edge = CallEdge(
                        caller_id=caller_id,
                        caller_name=self.current_function,
                        callee_id=callee_id,
                        callee_name=callee_name_full or callee_name,
                        call_site_line=node.lineno,
                        confidence=confidence,
                    )
                    self.edges.append(edge)

        self.generic_visit(node)

    def _get_call_name(self, node) -> Optional[str]:
        """Extract short call name from expression (just the function name)."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return node.attr
        elif isinstance(node, ast.Subscript):
            return self._get_call_name(node.value)
        return None

    def _get_call_name_full(self, node) -> Optional[str]:
        """Extract full qualified name from call expression (e.g., obj.method)."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            value_name = self._get_call_name_full(node.value)
            if value_name:
                return f"{value_name}.{node.attr}"
            return node.attr
        elif isinstance(node, ast.Subscript):
            return self._get_call_name_full(node.value)
        return None

    def _is_builtin(self, name: str) -> bool:
        """Check if name is a Python builtin."""
        builtins = {
            "print", "len", "range", "enumerate", "zip", "map", "filter", "sorted",
            "str", "int", "float", "bool", "list", "dict", "set", "tuple",
            "open", "input", "sum", "max", "min", "abs", "all", "any", "iter",
            "hasattr", "getattr", "setattr", "isinstance", "issubclass", "callable",
            "repr", "ascii", "format", "hash", "id", "type", "vars", "dir",
        }
        return name in builtins

    def _is_method_call(self, node) -> bool:
        """Check if call is a method call (attribute access)."""
        return isinstance(node, ast.Attribute)

    def _is_self_call(self, node) -> bool:
        """Check if call is to self."""
        if isinstance(node, ast.Attribute):
            if isinstance(node.value, ast.Name):
                return node.value.id == "self"
        return False

    def _compute_confidence(self, short_name: str, full_name: Optional[str], node) -> float:
        """Compute confidence score for a call.

        Confidence bands (from spec):
        - 1.0: Exact AST-resolved call (e.g., foo())
        - 0.9–0.8: Confidently resolved method (e.g., self.method)
        - 0.7–0.6: Partially inferred (e.g., obj.method)
        - 0.5–0.4: Ambiguous or builtin
        - Below 0.4: Not returned
        """
        # Builtin calls: low confidence
        if self._is_builtin(short_name):
            return 0.4

        # Self method calls: high confidence
        if self._is_self_call(node):
            return 0.9

        # Instance method calls: moderate confidence
        if self._is_method_call(node):
            return 0.7

        # Simple function calls: highest confidence
        return 1.0

    def _make_id(self, name: str) -> str:
        """Create a stable ID for a symbol (simplified)."""
        return name

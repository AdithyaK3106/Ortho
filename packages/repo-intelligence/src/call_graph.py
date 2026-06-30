"""Call graph builder using pyan3 for static Python analysis."""

from pathlib import Path
from typing import List
import ast
import pyan3.analyzer as pyan_analyzer
from .symbol_extractor import Symbol


class CallGraphError(Exception):
    """Raised when call graph analysis fails."""
    pass


class CallEdge:
    """Represents a function call relationship."""
    def __init__(
        self,
        caller_id: str,
        callee_id: str,
        call_site_line: int,
        confidence: float,
    ):
        self.caller_id = caller_id
        self.callee_id = callee_id
        self.call_site_line = call_site_line
        self.confidence = confidence

    def to_dict(self):
        return {
            "caller_id": self.caller_id,
            "callee_id": self.callee_id,
            "call_site_line": self.call_site_line,
            "confidence": self.confidence,
        }


class CallGraphBuilder:
    """Extract call edges from Python source code using AST analysis."""

    def __init__(self, repo_root: Path, python_files: List[Path]):
        """
        Initialize call graph builder.

        Args:
            repo_root: Project root directory
            python_files: List of Python file paths (absolute or relative to repo_root)
        """
        self.repo_root = Path(repo_root)
        self.python_files = [Path(f) if not Path(f).is_absolute() else f for f in python_files]
        self.edges = []
        self._recursive_calls = set()
        self._call_stack = []

    def build_call_graph(self) -> List[CallEdge]:
        """
        Extract function/method calls from Python AST.

        Returns:
            List of CallEdge objects with caller_id, callee_id, line, confidence

        Raises:
            CallGraphError: If analysis fails
        """
        try:
            for file_path in self.python_files:
                abs_path = file_path if file_path.is_absolute() else self.repo_root / file_path
                if not abs_path.exists():
                    continue
                self._analyze_file(abs_path)
            return self.edges
        except Exception as e:
            raise CallGraphError(f"Call graph analysis failed: {e}") from e

    def _analyze_file(self, file_path: Path):
        """Analyze a single Python file for call relationships."""
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            source = f.read()

        try:
            tree = ast.parse(source)
        except SyntaxError:
            return

        visitor = CallVisitor(file_path, self.repo_root)
        visitor.visit(tree)
        self.edges.extend(visitor.edges)


class CallVisitor(ast.NodeVisitor):
    """AST visitor to extract call edges from Python source."""

    def __init__(self, file_path: Path, repo_root: Path):
        self.file_path = file_path
        self.repo_root = Path(repo_root)
        self.edges = []
        self.current_function = None
        self.current_class = None

    def visit_FunctionDef(self, node):
        """Visit function definition."""
        old_function = self.current_function
        self.current_function = (self.current_class, node.name) if self.current_class else node.name
        self.generic_visit(node)
        self.current_function = old_function

    def visit_AsyncFunctionDef(self, node):
        """Visit async function definition."""
        old_function = self.current_function
        self.current_function = (self.current_class, node.name) if self.current_class else node.name
        self.generic_visit(node)
        self.current_function = old_function

    def visit_ClassDef(self, node):
        """Visit class definition."""
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class

    def visit_Call(self, node):
        """Visit function call."""
        if self.current_function:
            callee_name = self._get_call_name(node.func)
            if callee_name and not self._is_builtin(callee_name):
                confidence = 1.0
                if callee_name == self.current_function or (
                    isinstance(self.current_function, tuple) and callee_name == self.current_function[1]
                ):
                    confidence = 0.8

                self.edges.append(
                    {
                        "caller": str(self.current_function),
                        "callee": callee_name,
                        "line": node.lineno,
                        "confidence": confidence,
                    }
                )
        self.generic_visit(node)

    def visit_Await(self, node):
        """Visit await expression."""
        if isinstance(node.value, ast.Call) and self.current_function:
            callee_name = self._get_call_name(node.value.func)
            if callee_name and not self._is_builtin(callee_name):
                self.edges.append(
                    {
                        "caller": str(self.current_function),
                        "callee": callee_name,
                        "line": node.lineno,
                        "confidence": 1.0,
                    }
                )
        self.generic_visit(node)

    def _get_call_name(self, node) -> str:
        """Extract function name from call expression."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return node.attr
        elif isinstance(node, ast.Subscript):
            return self._get_call_name(node.value)
        return ""

    def _is_builtin(self, name: str) -> bool:
        """Check if name is a Python builtin."""
        builtins = {
            "print", "len", "range", "enumerate", "zip", "map", "filter", "sorted",
            "str", "int", "float", "bool", "list", "dict", "set", "tuple",
            "open", "input", "sum", "max", "min", "abs", "all", "any", "iter",
        }
        return name in builtins

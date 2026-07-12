"""Token optimizer: Context assembly and token budget management."""

from .budget import TokenBudget, BudgetExceededError
from .types import ContextChunk, ContextPackage
from .assembler import assemble_context
from .prompt import assemble_prompt
from .deduplicator import detect_and_remove_duplicates, DeduplicationResult
from .reranker import rerank_by_intent, RerankerConfig
from .graph_expander import expand_by_call_graph, CallGraphInterface

__all__ = [
    "TokenBudget",
    "BudgetExceededError",
    "ContextChunk",
    "ContextPackage",
    "assemble_context",
    "assemble_prompt",
    "detect_and_remove_duplicates",
    "DeduplicationResult",
    "rerank_by_intent",
    "RerankerConfig",
    "expand_by_call_graph",
    "CallGraphInterface",
]

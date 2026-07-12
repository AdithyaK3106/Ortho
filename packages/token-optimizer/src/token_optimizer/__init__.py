"""Token optimizer: Context assembly and token budget management."""

from .budget import TokenBudget, BudgetExceededError
from .types import ContextChunk, ContextPackage
from .assembler import assemble_context
from .prompt import assemble_prompt
from .deduplicator import detect_and_remove_duplicates, DeduplicationResult
from .reranker import rerank_by_intent, RerankerConfig
from .graph_expander import expand_by_call_graph, CallGraphInterface
from .compressor import compress_over_budget, CompressionError
from .arch_retrieval import boost_by_architecture
from .model_adapter import adapt_prompt_for_model

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
    "compress_over_budget",
    "CompressionError",
    "boost_by_architecture",
    "adapt_prompt_for_model",
]

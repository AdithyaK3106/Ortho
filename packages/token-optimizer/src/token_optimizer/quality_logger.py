"""Context quality logging for offline analysis and tuning."""

import csv
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from .types import ContextPackage


class ContextQualityLogger:
    """Log context assembly decisions to CSV."""

    def __init__(self, log_dir: Optional[Path] = None):
        """Initialize logger with directory for CSV files."""
        if log_dir is None:
            log_dir = Path(".ortho/logs")
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def log_assembly(
        self,
        context_package: ContextPackage,
        query: str,
        intent_class: str,
        dedup_ratio: float = 1.0,
        rerank_factor: float = 1.0,
        compression_applied: bool = False,
        architecture_boost_applied: bool = False,
        model: str = "claude-opus-4-8",
        llm_input_tokens: int = 0,
        llm_output_tokens: int = 0,
        llm_stop_reason: str = "complete",
    ) -> None:
        """
        Log a context assembly decision to CSV.

        Args:
            context_package: Assembled context package
            query: User query/intent text
            intent_class: Intent classification result
            dedup_ratio: Deduplication reduction ratio
            rerank_factor: Average rerank boost factor
            compression_applied: Whether compression was used
            architecture_boost_applied: Whether arch boosting was used
            model: LLM model used
            llm_input_tokens: Tokens sent to LLM
            llm_output_tokens: Tokens received from LLM
            llm_stop_reason: LLM stop reason (complete, max_tokens, etc.)
        """
        timestamp = datetime.utcnow().isoformat()
        log_file = self.log_dir / f"context-quality-{datetime.utcnow().strftime('%Y%m%d')}.csv"

        # Compute metrics
        chunks_retrieved = len(context_package.chunks)
        chunks_included = sum(1 for c in context_package.chunks if c.included)
        tokens_used = context_package.budget.used
        tokens_available = context_package.budget.total

        # Prepare row
        row = {
            "timestamp": timestamp,
            "workflow_run_id": context_package.workflow_run_id,
            "step_id": context_package.step_id,
            "query": query[:100],  # Truncate for CSV
            "intent_class": intent_class,
            "chunks_retrieved": chunks_retrieved,
            "chunks_included": chunks_included,
            "tokens_used": tokens_used,
            "tokens_available": tokens_available,
            "dedup_ratio": round(dedup_ratio, 3),
            "rerank_factor": round(rerank_factor, 3),
            "compression_applied": int(compression_applied),
            "architecture_boost_applied": int(architecture_boost_applied),
            "model": model,
            "llm_input_tokens": llm_input_tokens,
            "llm_output_tokens": llm_output_tokens,
            "llm_stop_reason": llm_stop_reason,
        }

        # Write to CSV
        file_exists = log_file.exists()
        with open(log_file, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=row.keys())
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)

    def read_logs(self, date: Optional[str] = None) -> list[Dict[str, Any]]:
        """
        Read all quality logs or logs for specific date.

        Args:
            date: Optional date string (YYYYMMDD) to filter

        Returns:
            List of log entries as dicts
        """
        entries = []
        pattern = f"context-quality-{date}*.csv" if date else "context-quality-*.csv"

        for log_file in self.log_dir.glob(pattern):
            with open(log_file, "r") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Convert numeric fields
                    row["chunks_retrieved"] = int(row["chunks_retrieved"])
                    row["chunks_included"] = int(row["chunks_included"])
                    row["tokens_used"] = int(row["tokens_used"])
                    row["tokens_available"] = int(row["tokens_available"])
                    row["dedup_ratio"] = float(row["dedup_ratio"])
                    row["rerank_factor"] = float(row["rerank_factor"])
                    row["compression_applied"] = bool(int(row["compression_applied"]))
                    row["architecture_boost_applied"] = bool(int(row["architecture_boost_applied"]))
                    row["llm_input_tokens"] = int(row["llm_input_tokens"])
                    row["llm_output_tokens"] = int(row["llm_output_tokens"])
                    entries.append(row)

        return entries

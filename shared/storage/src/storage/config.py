import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass
class OrthoConfig:
    """Configuration for Ortho project."""

    project_name: str
    project_root: str
    primary_language: str
    languages: list[str]
    exclude_patterns: list[str]
    embedding_model: str
    embedding_provider: str
    default_model: str
    fallback_model: str
    max_tokens: int
    human_approval: bool
    approval_timeout_seconds: int
    default_budget: int
    compression_threshold: float

    @classmethod
    def load(cls, config_path: Path) -> "OrthoConfig":
        """Load config from TOML file."""
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(config_path, "rb") as f:
            data = tomllib.load(f)

        return cls(
            project_name=data.get("project", {}).get("name", "ortho"),
            project_root=data.get("project", {}).get("root", "."),
            primary_language=data.get("project", {}).get("primary_language", "python"),
            languages=data.get("indexing", {}).get("languages", ["python"]),
            exclude_patterns=data.get("indexing", {}).get("exclude_patterns", []),
            embedding_model=data.get("context_hub", {}).get("embedding_model", "text-embedding-3-small"),
            embedding_provider=data.get("context_hub", {}).get("embedding_provider", "openai"),
            default_model=data.get("llm", {}).get("default_model", "claude-sonnet-4-6"),
            fallback_model=data.get("llm", {}).get("fallback_model", "claude-haiku-4-5-20251001"),
            max_tokens=data.get("llm", {}).get("max_tokens", 8192),
            human_approval=data.get("orchestration", {}).get("human_approval", True),
            approval_timeout_seconds=data.get("orchestration", {}).get("approval_timeout_seconds", 300),
            default_budget=data.get("token_optimizer", {}).get("default_budget", 16000),
            compression_threshold=data.get("token_optimizer", {}).get("compression_threshold", 0.6),
        )

    def validate(self) -> None:
        """Validate config values."""
        if not self.project_name:
            raise ValueError("project_name is required")
        if not self.primary_language:
            raise ValueError("primary_language is required")
        if self.default_budget <= 0:
            raise ValueError("default_budget must be positive")
        if not (0 <= self.compression_threshold <= 1):
            raise ValueError("compression_threshold must be between 0 and 1")

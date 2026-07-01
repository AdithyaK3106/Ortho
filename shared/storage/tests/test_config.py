"""Tests for OrthoConfig - Configuration loading and validation."""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from storage.config import OrthoConfig


class TestOrthoConfigLoad:
    """Test configuration loading from TOML."""

    @pytest.fixture
    def config_file(self):
        """Create a test config file."""
        with TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.toml"
            config_content = """
[project]
name = "test-project"
root = "/test/root"
primary_language = "python"

[indexing]
languages = ["python", "typescript"]
exclude_patterns = ["**/node_modules", "**/__pycache__"]

[context_hub]
embedding_model = "text-embedding-3-large"
embedding_provider = "openai"

[llm]
default_model = "claude-opus-4-8"
fallback_model = "claude-haiku-4-5"
max_tokens = 16384

[orchestration]
human_approval = false
approval_timeout_seconds = 600

[token_optimizer]
default_budget = 32000
compression_threshold = 0.75
"""
            config_path.write_text(config_content)
            yield config_path

    def test_load_config_from_file(self, config_file):
        """Should load config from TOML file."""
        config = OrthoConfig.load(config_file)

        assert config.project_name == "test-project"
        assert config.project_root == "/test/root"
        assert config.primary_language == "python"

    def test_load_languages_list(self, config_file):
        """Should load language list."""
        config = OrthoConfig.load(config_file)

        assert "python" in config.languages
        assert "typescript" in config.languages
        assert len(config.languages) == 2

    def test_load_exclude_patterns(self, config_file):
        """Should load exclude patterns."""
        config = OrthoConfig.load(config_file)

        assert "**/node_modules" in config.exclude_patterns
        assert "**/__pycache__" in config.exclude_patterns

    def test_load_embedding_config(self, config_file):
        """Should load embedding model config."""
        config = OrthoConfig.load(config_file)

        assert config.embedding_model == "text-embedding-3-large"
        assert config.embedding_provider == "openai"

    def test_load_llm_config(self, config_file):
        """Should load LLM model config."""
        config = OrthoConfig.load(config_file)

        assert config.default_model == "claude-opus-4-8"
        assert config.fallback_model == "claude-haiku-4-5"
        assert config.max_tokens == 16384

    def test_load_orchestration_config(self, config_file):
        """Should load orchestration settings."""
        config = OrthoConfig.load(config_file)

        assert config.human_approval is False
        assert config.approval_timeout_seconds == 600

    def test_load_token_optimizer_config(self, config_file):
        """Should load token optimizer settings."""
        config = OrthoConfig.load(config_file)

        assert config.default_budget == 32000
        assert config.compression_threshold == 0.75

    def test_file_not_found(self):
        """Should raise FileNotFoundError for missing config."""
        with pytest.raises(FileNotFoundError):
            OrthoConfig.load(Path("/nonexistent/config.toml"))

    def test_load_minimal_config(self):
        """Should load config with minimal required fields."""
        with TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.toml"
            config_path.write_text("")

            config = OrthoConfig.load(config_path)

            # Should use defaults
            assert config.project_name == "ortho"
            assert config.primary_language == "python"


class TestOrthoConfigDefaults:
    """Test default values when config is missing sections."""

    def test_default_project_name(self):
        """Should default project name to 'ortho'."""
        with TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.toml"
            config_path.write_text("")

            config = OrthoConfig.load(config_path)
            assert config.project_name == "ortho"

    def test_default_primary_language(self):
        """Should default primary language to 'python'."""
        with TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.toml"
            config_path.write_text("")

            config = OrthoConfig.load(config_path)
            assert config.primary_language == "python"

    def test_default_languages_list(self):
        """Should default languages to ['python']."""
        with TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.toml"
            config_path.write_text("")

            config = OrthoConfig.load(config_path)
            assert config.languages == ["python"]

    def test_default_embedding_model(self):
        """Should default to OpenAI's text-embedding-3-small."""
        with TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.toml"
            config_path.write_text("")

            config = OrthoConfig.load(config_path)
            assert config.embedding_model == "text-embedding-3-small"
            assert config.embedding_provider == "openai"

    def test_default_llm_models(self):
        """Should default to Claude models."""
        with TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.toml"
            config_path.write_text("")

            config = OrthoConfig.load(config_path)
            assert config.default_model == "claude-sonnet-4-6"
            assert config.fallback_model == "claude-haiku-4-5-20251001"

    def test_default_max_tokens(self):
        """Should default max_tokens to 8192."""
        with TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.toml"
            config_path.write_text("")

            config = OrthoConfig.load(config_path)
            assert config.max_tokens == 8192

    def test_default_token_optimizer_budget(self):
        """Should default token budget to 16000."""
        with TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.toml"
            config_path.write_text("")

            config = OrthoConfig.load(config_path)
            assert config.default_budget == 16000

    def test_default_compression_threshold(self):
        """Should default compression threshold to 0.6."""
        with TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.toml"
            config_path.write_text("")

            config = OrthoConfig.load(config_path)
            assert config.compression_threshold == 0.6


class TestOrthoConfigValidation:
    """Test configuration validation."""

    def test_validate_requires_project_name(self):
        """Should require non-empty project name."""
        config = OrthoConfig(
            project_name="",
            project_root=".",
            primary_language="python",
            languages=["python"],
            exclude_patterns=[],
            embedding_model="text-embedding-3-small",
            embedding_provider="openai",
            default_model="claude-sonnet-4-6",
            fallback_model="claude-haiku-4-5-20251001",
            max_tokens=8192,
            human_approval=True,
            approval_timeout_seconds=300,
            default_budget=16000,
            compression_threshold=0.6,
        )

        with pytest.raises(ValueError, match="project_name is required"):
            config.validate()

    def test_validate_requires_primary_language(self):
        """Should require non-empty primary language."""
        config = OrthoConfig(
            project_name="test",
            project_root=".",
            primary_language="",
            languages=["python"],
            exclude_patterns=[],
            embedding_model="text-embedding-3-small",
            embedding_provider="openai",
            default_model="claude-sonnet-4-6",
            fallback_model="claude-haiku-4-5-20251001",
            max_tokens=8192,
            human_approval=True,
            approval_timeout_seconds=300,
            default_budget=16000,
            compression_threshold=0.6,
        )

        with pytest.raises(ValueError, match="primary_language is required"):
            config.validate()

    def test_validate_requires_positive_budget(self):
        """Should require positive default budget."""
        config = OrthoConfig(
            project_name="test",
            project_root=".",
            primary_language="python",
            languages=["python"],
            exclude_patterns=[],
            embedding_model="text-embedding-3-small",
            embedding_provider="openai",
            default_model="claude-sonnet-4-6",
            fallback_model="claude-haiku-4-5-20251001",
            max_tokens=8192,
            human_approval=True,
            approval_timeout_seconds=300,
            default_budget=0,
            compression_threshold=0.6,
        )

        with pytest.raises(ValueError, match="default_budget must be positive"):
            config.validate()

    def test_validate_compression_threshold_bounds(self):
        """Should require compression threshold between 0 and 1."""
        config = OrthoConfig(
            project_name="test",
            project_root=".",
            primary_language="python",
            languages=["python"],
            exclude_patterns=[],
            embedding_model="text-embedding-3-small",
            embedding_provider="openai",
            default_model="claude-sonnet-4-6",
            fallback_model="claude-haiku-4-5-20251001",
            max_tokens=8192,
            human_approval=True,
            approval_timeout_seconds=300,
            default_budget=16000,
            compression_threshold=1.5,
        )

        with pytest.raises(ValueError, match="compression_threshold must be between 0 and 1"):
            config.validate()

    def test_valid_config_passes_validation(self):
        """Valid config should pass validation."""
        config = OrthoConfig(
            project_name="test",
            project_root=".",
            primary_language="python",
            languages=["python"],
            exclude_patterns=[],
            embedding_model="text-embedding-3-small",
            embedding_provider="openai",
            default_model="claude-sonnet-4-6",
            fallback_model="claude-haiku-4-5-20251001",
            max_tokens=8192,
            human_approval=True,
            approval_timeout_seconds=300,
            default_budget=16000,
            compression_threshold=0.6,
        )

        # Should not raise
        config.validate()

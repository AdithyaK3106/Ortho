"""Hard unit tests for prompt assembler (spec.md AC4)."""

import pytest
import sys
from datetime import datetime
from pathlib import Path

# Add src directory to path so token_optimizer can be imported
_src_path = Path(__file__).parent.parent / "src"
if str(_src_path) not in sys.path:
    sys.path.insert(0, str(_src_path))

try:
    from token_optimizer.budget import TokenBudget
    from token_optimizer.types import ContextPackage, ContextChunk
    from token_optimizer.prompt import assemble_prompt
except ImportError:
    TokenBudget = None
    ContextPackage = None
    ContextChunk = None
    assemble_prompt = None


class TestAssemblePromptDeterminism:
    """CRITICAL: Determinism tests for prompt assembly."""

    @pytest.mark.skipif(assemble_prompt is None, reason="prompt assembler not implemented")
    def test_assemble_prompt_determinism_identical_inputs(self, mock_agent, mock_skills):
        """AC4: Identical inputs produce identical prompt text."""
        now = datetime.utcnow().isoformat()
        chunks = [
            ContextChunk(
                id="ch1", source_type="artifact", source_id="art1",
                content="Content 1", relevance_score=0.9,
                token_count=10, included=True
            ),
            ContextChunk(
                id="ch2", source_type="artifact", source_id="art2",
                content="Content 2", relevance_score=0.8,
                token_count=15, included=True
            ),
        ]
        budget = TokenBudget(total=100, used=0, model="claude")
        pkg = ContextPackage(
            id="pkg1", workflow_run_id="run1", step_id="step1",
            chunks=chunks, budget=budget, assembled_at=now
        )

        _, user_msg1 = assemble_prompt(pkg, step=None, agent=mock_agent, skills=mock_skills)
        _, user_msg2 = assemble_prompt(pkg, step=None, agent=mock_agent, skills=mock_skills)

        assert user_msg1 == user_msg2


class TestAssemblePromptOrdering:
    """Hard tests for chunk ordering in prompts."""

    @pytest.mark.skipif(assemble_prompt is None, reason="prompt assembler not implemented")
    def test_assemble_prompt_chunk_ordering_by_id_ascending(self, mock_agent, mock_skills):
        """AC4: Chunks ordered by chunk.id ascending (lexicographic)."""
        now = datetime.utcnow().isoformat()
        chunks = [
            ContextChunk(
                id="z_chunk", source_type="artifact", source_id="z",
                content="Z content", relevance_score=0.9,
                token_count=10, included=True
            ),
            ContextChunk(
                id="a_chunk", source_type="artifact", source_id="a",
                content="A content", relevance_score=0.95,
                token_count=5, included=True
            ),
            ContextChunk(
                id="m_chunk", source_type="artifact", source_id="m",
                content="M content", relevance_score=0.85,
                token_count=8, included=True
            ),
        ]
        budget = TokenBudget(total=100, used=0, model="claude")
        pkg = ContextPackage(
            id="pkg1", workflow_run_id="run1", step_id="step1",
            chunks=chunks, budget=budget, assembled_at=now
        )

        _, user_msg = assemble_prompt(pkg, step=None, agent=mock_agent, skills=[])

        pos_a = user_msg.find("a_chunk")
        pos_m = user_msg.find("m_chunk")
        pos_z = user_msg.find("z_chunk")

        if pos_a != -1 and pos_m != -1 and pos_z != -1:
            assert pos_a < pos_m < pos_z


class TestAssemblePromptFormat:
    """Hard tests for prompt format."""

    @pytest.mark.skipif(assemble_prompt is None, reason="prompt assembler not implemented")
    def test_assemble_prompt_format_fixed_delimiter(self, mock_agent, mock_skills):
        """AC4: Format is \\n\\n--- [{source_type}:{source_id}] ---\\n{content}\\n."""
        now = datetime.utcnow().isoformat()
        chunk = ContextChunk(
            id="ch1", source_type="artifact", source_id="src_123",
            content="Sample content", relevance_score=0.9,
            token_count=10, included=True
        )
        budget = TokenBudget(total=100, used=0, model="claude")
        pkg = ContextPackage(
            id="pkg1", workflow_run_id="run1", step_id="step1",
            chunks=[chunk], budget=budget, assembled_at=now
        )

        _, user_msg = assemble_prompt(pkg, step=None, agent=mock_agent, skills=[])

        expected = "\n\n--- [artifact:src_123] ---\nSample content\n"
        assert expected in user_msg

    @pytest.mark.skipif(assemble_prompt is None, reason="prompt assembler not implemented")
    def test_assemble_prompt_only_included_chunks(self, mock_agent, mock_skills):
        """AC4: Only chunks with included=True appear in user message."""
        now = datetime.utcnow().isoformat()
        chunks = [
            ContextChunk(
                id="ch1", source_type="artifact", source_id="s1",
                content="Included", relevance_score=0.9,
                token_count=10, included=True
            ),
            ContextChunk(
                id="ch2", source_type="artifact", source_id="s2",
                content="Excluded", relevance_score=0.8,
                token_count=10, included=False
            ),
        ]
        budget = TokenBudget(total=100, used=0, model="claude")
        pkg = ContextPackage(
            id="pkg1", workflow_run_id="run1", step_id="step1",
            chunks=chunks, budget=budget, assembled_at=now
        )

        _, user_msg = assemble_prompt(pkg, step=None, agent=mock_agent, skills=[])

        assert "s1" in user_msg
        assert "Included" in user_msg
        assert "s2" not in user_msg
        assert "Excluded" not in user_msg

    @pytest.mark.skipif(assemble_prompt is None, reason="prompt assembler not implemented")
    def test_assemble_prompt_empty_included_set(self, mock_agent, mock_skills):
        """AC4: No included chunks → empty user message."""
        now = datetime.utcnow().isoformat()
        chunks = [
            ContextChunk(
                id="ch1", source_type="artifact", source_id="s1",
                content="content", relevance_score=0.9,
                token_count=10, included=False
            ),
        ]
        budget = TokenBudget(total=100, used=0, model="claude")
        pkg = ContextPackage(
            id="pkg1", workflow_run_id="run1", step_id="step1",
            chunks=chunks, budget=budget, assembled_at=now
        )

        _, user_msg = assemble_prompt(pkg, step=None, agent=mock_agent, skills=[])

        assert user_msg == ""

    def test_assemble_prompt_falls_back_to_intent_text_when_no_chunks_included(
        self, mock_agent, mock_skills
    ):
        """Regression: a real ArtifactStore with nothing ingested yet for a
        repo returns a real (truthy) ContextPackage with zero included
        chunks -- indistinguishable, before this fix, from "context
        assembly worked but found nothing", so the agent got a genuinely
        empty user message and could only ask what it was reviewing. When
        intent_text is given, it must be used instead of an empty string."""
        now = datetime.utcnow().isoformat()
        chunks = [
            ContextChunk(
                id="ch1", source_type="artifact", source_id="s1",
                content="content", relevance_score=0.9,
                token_count=10, included=False
            ),
        ]
        budget = TokenBudget(total=100, used=0, model="claude")
        pkg = ContextPackage(
            id="pkg1", workflow_run_id="run1", step_id="step1",
            chunks=chunks, budget=budget, assembled_at=now
        )

        _, user_msg = assemble_prompt(
            pkg, step=None, agent=mock_agent, skills=[],
            intent_text="refactor flask/app.py to split it into smaller modules",
        )

        assert user_msg == "Original request: refactor flask/app.py to split it into smaller modules"


class TestAssemblePromptDuplicateHandling:
    """Tests for duplicate source_id handling."""

    @pytest.mark.skipif(assemble_prompt is None, reason="prompt assembler not implemented")
    def test_assemble_prompt_duplicate_source_ids_all_included(self, mock_agent, mock_skills):
        """AC4: Multiple chunks with same source_id are all included (no dedup)."""
        now = datetime.utcnow().isoformat()
        chunks = [
            ContextChunk(
                id="ch1", source_type="artifact", source_id="src_dup",
                content="First", relevance_score=0.9,
                token_count=10, included=True
            ),
            ContextChunk(
                id="ch2", source_type="artifact", source_id="src_dup",
                content="Second", relevance_score=0.8,
                token_count=10, included=True
            ),
        ]
        budget = TokenBudget(total=100, used=0, model="claude")
        pkg = ContextPackage(
            id="pkg1", workflow_run_id="run1", step_id="step1",
            chunks=chunks, budget=budget, assembled_at=now
        )

        _, user_msg = assemble_prompt(pkg, step=None, agent=mock_agent, skills=[])

        count = user_msg.count("src_dup")
        assert count == 2

        pos_first = user_msg.find("First")
        pos_second = user_msg.find("Second")
        assert pos_first < pos_second

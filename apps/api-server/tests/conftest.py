"""Pytest configuration for api-server tests."""

import sys
from pathlib import Path

# Add root and src to path so imports work
project_root = Path(__file__).parent.parent.parent.parent  # ../../..
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "apps" / "api-server" / "src"))

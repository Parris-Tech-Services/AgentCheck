"""Test-environment guards for AgentCheck.

A handful of hardened-backend tests require infrastructure that is deliberately
outside this repository: the LLMAccountability ``agy_service`` integration and
a real AGYRunner Windows account/ACL. Generic CI must report those checks as
unavailable (skipped), rather than misreporting an absent environment as a
product regression.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


_LLM_ACCOUNTABILITY_PATH = Path("C:/dev/AI-Verification/LLMAccountability")
_EXTERNAL_SCHEMA_TESTS = {
    "test_integration_pushed_real_schema",
    "test_integration_test_counts_real_schema",
    "test_integration_inconsistent_tests",
    "test_integration_stale_hardened_evidence",
}
_AGYRUNNER_ACL_TEST = "test_agyrunner_cannot_write_agentwitness_dir"


def _agy_service_available() -> bool:
    """Return whether the external hardened-service module can be imported."""
    if sys.platform == "win32" and _LLM_ACCOUNTABILITY_PATH.exists():
        external_path = str(_LLM_ACCOUNTABILITY_PATH)
        if external_path not in sys.path:
            sys.path.insert(0, external_path)

    try:
        return importlib.util.find_spec("agy_service") is not None
    except (ImportError, ValueError):
        return False


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Mark tests whose required external environment is not present."""
    external_schema_available = _agy_service_available()

    for item in items:
        if item.name in _EXTERNAL_SCHEMA_TESTS and not external_schema_available:
            item.add_marker(
                pytest.mark.skip(
                    reason=(
                        "requires external LLMAccountability agy_service; "
                        "generic AgentCheck CI does not provide that integration environment"
                    )
                )
            )

        if item.name == _AGYRUNNER_ACL_TEST and sys.platform != "win32":
            item.add_marker(
                pytest.mark.skip(
                    reason="requires a real Windows AGYRunner account and ACL environment"
                )
            )

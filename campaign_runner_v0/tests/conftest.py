"""Shared pytest helpers for campaign_runner_v0."""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
AURORA_WORKSPACE = REPO_ROOT / "aurora_audit"
POLICY = REPO_ROOT / "campaign_runner_v0" / "policies" / "aurora_default.json"


@pytest.fixture
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture
def aurora_workspace() -> Path:
    assert AURORA_WORKSPACE.is_dir()
    return AURORA_WORKSPACE


@pytest.fixture
def policy_path() -> Path:
    assert POLICY.is_file()
    return POLICY

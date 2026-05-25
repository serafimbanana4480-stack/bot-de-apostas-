"""Tests for correlation ID propagation."""
from __future__ import annotations

from src.monitoring.correlation_context import (
    correlation_ctx,
    generate_correlation_id,
    get_correlation_id,
    set_correlation_id,
)


def test_generate_correlation_id():
    cid = generate_correlation_id()
    assert cid.startswith("vbq-")
    assert len(cid) > 4

    cid2 = generate_correlation_id(prefix="test")
    assert cid2.startswith("test-")


def test_get_set_correlation_id():
    assert get_correlation_id() is None
    set_correlation_id("abc-123")
    assert get_correlation_id() == "abc-123"
    set_correlation_id(None)
    assert get_correlation_id() is None


def test_correlation_ctx():
    assert get_correlation_id() is None
    with correlation_ctx("my-id"):
        assert get_correlation_id() == "my-id"
    assert get_correlation_id() is None


def test_correlation_ctx_auto_generates():
    with correlation_ctx():
        cid = get_correlation_id()
        assert cid is not None
        assert cid.startswith("vbq-")


def test_nested_correlation_ctx():
    with correlation_ctx("outer"):
        assert get_correlation_id() == "outer"
        with correlation_ctx("inner"):
            assert get_correlation_id() == "inner"
        assert get_correlation_id() == "outer"

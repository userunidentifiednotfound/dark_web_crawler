"""Unit tests for proxy manager and circuit breaker behavior."""

import pytest
from dwi_crawler.crawling.proxy import CircuitBreakerOpenException, ProxyManager


def test_circuit_breaker_trip_and_reset():
    pm = ProxyManager()
    pm.max_failures = 3
    pm.failure_count = 0
    pm.is_circuit_open = False

    # Initially closed circuit
    pm.check_circuit()

    # Record 2 failures (below threshold)
    pm.record_failure("timeout 1")
    pm.record_failure("timeout 2")
    assert not pm.is_circuit_open
    pm.check_circuit()

    # 3rd failure trips the circuit
    pm.record_failure("connection refused")
    assert pm.is_circuit_open

    # Check circuit should now raise CircuitBreakerOpenException
    with pytest.raises(CircuitBreakerOpenException):
        pm.check_circuit()

    # Success should reset the circuit
    pm.record_success()
    assert not pm.is_circuit_open
    assert pm.failure_count == 0
    pm.check_circuit()  # Should not raise

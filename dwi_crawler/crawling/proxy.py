"""Centralized Tor and proxy session manager with circuit breaker and health monitoring."""

import asyncio
import logging
import socket
import time
from dwi_crawler.config.settings import get_settings

logger = logging.getLogger("dwi_crawler.crawling.proxy")


class CircuitBreakerOpenException(Exception):
    pass


class ProxyManager:
    """Manages Tor and authorized proxy sessions, health checks, and circuit breaking."""

    def __init__(self):
        self.settings = get_settings()
        self.failure_count = 0
        self.max_failures = 5
        self.reset_timeout = 60.0
        self.last_failure_time: float = 0.0
        self.is_circuit_open = False

    def get_proxy_url(self) -> str:
        """Returns the centralized proxy URL."""
        return self.settings.get_proxy_url()

    def is_proxy_enabled_for_url(self, is_onion: bool) -> bool:
        """Determines whether a given request should be routed through the proxy."""
        if is_onion:
            return self.settings.use_proxy_for_onion
        return self.settings.use_proxy_for_surface

    def check_circuit(self) -> None:
        """Checks if the proxy circuit breaker is currently open."""
        if self.is_circuit_open:
            if time.time() - self.last_failure_time > self.reset_timeout:
                logger.info("Proxy circuit breaker half-open: attempting recovery.")
                self.is_circuit_open = False
                self.failure_count = 0
            else:
                raise CircuitBreakerOpenException("Proxy circuit breaker is open due to repeated failures.")

    def record_success(self) -> None:
        """Records a successful proxy connection."""
        self.failure_count = 0
        self.is_circuit_open = False

    def record_failure(self, error: Exception | str) -> None:
        """Records a proxy connection failure and triggers circuit breaking if threshold exceeded."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        logger.warning(f"Proxy failure #{self.failure_count}: {error}")
        if self.failure_count >= self.max_failures:
            self.is_circuit_open = True
            logger.error(f"Proxy circuit breaker OPENED after {self.failure_count} consecutive failures.")

    async def check_health(self) -> dict[str, any]:
        """Tests connectivity to the configured Tor proxy host and port."""
        host = self.settings.tor_proxy_host
        port = self.settings.tor_proxy_port
        start_time = time.time()
        try:
            # Non-blocking socket connect check
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._sync_socket_check, host, port, 3.0)
            latency = round((time.time() - start_time) * 1000, 2)
            self.record_success()
            return {
                "status": "healthy",
                "host": host,
                "port": port,
                "type": self.settings.tor_proxy_type,
                "latency_ms": latency,
                "circuit_open": self.is_circuit_open,
            }
        except Exception as ex:
            return {
                "status": "unreachable",
                "host": host,
                "port": port,
                "type": self.settings.tor_proxy_type,
                "error": str(ex),
                "circuit_open": self.is_circuit_open,
            }

    @staticmethod
    def _sync_socket_check(host: str, port: int, timeout: float) -> None:
        with socket.create_connection((host, port), timeout=timeout):
            pass


_proxy_manager_instance: ProxyManager | None = None


def get_proxy_manager() -> ProxyManager:
    global _proxy_manager_instance
    if _proxy_manager_instance is None:
        _proxy_manager_instance = ProxyManager()
    return _proxy_manager_instance

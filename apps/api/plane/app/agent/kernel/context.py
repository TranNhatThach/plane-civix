# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

import logging
from typing import Dict, Any, Optional, Callable, List

logger = logging.getLogger(__name__)


class ServiceRegistration:
    """Represents an active service binding with an optional disposer effect."""
    def __init__(self, key: str, instance: Any, disposer: Optional[Callable[[], None]] = None):
        self.key = key
        self.instance = instance
        self.disposer = disposer

    def dispose(self):
        if self.disposer and callable(self.disposer):
            try:
                self.disposer()
            except Exception as e:
                logger.error(f"Error executing disposer for service '{self.key}': {e}")


class KernelContext:
    """
    Microkernel Service Container (IoC Container).
    Provides pluggable dependency injection, reversible effect registrations,
    and hierarchical sub-contexts for Agent Runtime.
    """

    def __init__(self, parent: Optional["KernelContext"] = None):
        self.parent = parent
        self._services: Dict[str, ServiceRegistration] = {}
        self._disposers: List[Callable[[], None]] = []

    def provide(self, key: str, instance: Any, disposer: Optional[Callable[[], None]] = None) -> Callable[[], None]:
        """
        Registers a service or capability instance in the context.
        Returns a disposer function that unregisters the service cleanly.
        """
        if key in self._services:
            logger.debug(f"Overriding existing service '{key}' in KernelContext")
            self._services[key].dispose()

        reg = ServiceRegistration(key, instance, disposer)
        self._services[key] = reg

        def unbind():
            if key in self._services and self._services[key] == reg:
                reg.dispose()
                del self._services[key]

        return unbind

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieves a registered service, resolving hierarchically up to parent context."""
        if key in self._services:
            return self._services[key].instance
        if self.parent:
            return self.parent.get(key, default)
        return default

    def has(self, key: str) -> bool:
        """Checks if a service key exists in current context or parent contexts."""
        if key in self._services:
            return True
        if self.parent:
            return self.parent.has(key)
        return False

    def create_subcontext(self) -> "KernelContext":
        """Spawns an isolated child context inheriting parent services with separate local overrides."""
        return KernelContext(parent=self)

    def dispose(self):
        """Disposes all registered services and listeners cleanly."""
        for key in list(self._services.keys()):
            reg = self._services.pop(key, None)
            if reg:
                reg.dispose()
        for disp in self._disposers:
            try:
                disp()
            except Exception as e:
                logger.error(f"Error in context disposer: {e}")
        self._disposers.clear()

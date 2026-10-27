# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

import logging
from typing import Dict, List, Any, Callable, Optional, Tuple

logger = logging.getLogger(__name__)

# Waterfall handler type: (payload: Any, next_fn: Callable[[Any], Any]) -> Any
WaterfallHandler = Callable[[Any, Callable[[Any], Any]], Any]


class KernelEvents:
    """
    Event Emitter & Waterfall Interceptor Chain Engine.
    Powers lifecycle hooks (agent/pre-step, tools/pre-execute, etc.)
    with short-circuiting and payload mutation capabilities.
    """

    def __init__(self):
        self._listeners: Dict[str, List[Callable[..., Any]]] = {}
        self._waterfalls: Dict[str, List[WaterfallHandler]] = {}

    def on(self, event_name: str, handler: Callable[..., Any]) -> Callable[[], None]:
        """Registers a standard observer event listener. Returns a disposer."""
        if event_name not in self._listeners:
            self._listeners[event_name] = []
        self._listeners[event_name].append(handler)

        def disposer():
            if event_name in self._listeners and handler in self._listeners[event_name]:
                self._listeners[event_name].remove(handler)

        return disposer

    def emit(self, event_name: str, *args, **kwargs) -> List[Any]:
        """Emits an event to all registered observers."""
        results = []
        handlers = list(self._listeners.get(event_name, []))
        for handler in handlers:
            try:
                results.append(handler(*args, **kwargs))
            except Exception as e:
                logger.error(f"Error executing listener for event '{event_name}': {e}")
        return results

    def use_waterfall(self, event_name: str, handler: WaterfallHandler) -> Callable[[], None]:
        """
        Registers a waterfall interceptor into the execution pipeline.
        Handler signature: (payload, next_fn) -> result
        Returns a disposer function.
        """
        if event_name not in self._waterfalls:
            self._waterfalls[event_name] = []
        self._waterfalls[event_name].append(handler)

        def disposer():
            if event_name in self._waterfalls and handler in self._waterfalls[event_name]:
                self._waterfalls[event_name].remove(handler)

        return disposer

    def execute_waterfall(self, event_name: str, initial_payload: Any) -> Any:
        """
        Executes registered waterfall interceptors sequentially like an onion middleware.
        If any handler doesn't call next_fn or raises an exception, the pipeline halts.
        """
        handlers = list(self._waterfalls.get(event_name, []))
        if not handlers:
            return initial_payload

        def build_chain(index: int) -> Callable[[Any], Any]:
            if index >= len(handlers):
                return lambda p: p

            current_handler = handlers[index]
            next_step = build_chain(index + 1)

            def runner(payload: Any) -> Any:
                return current_handler(payload, next_step)

            return runner

        pipeline = build_chain(0)
        return pipeline(initial_payload)

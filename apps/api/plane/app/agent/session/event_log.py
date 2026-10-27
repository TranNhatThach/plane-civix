# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

import json
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

from plane.app.agent.session.events import SessionEvent

logger = logging.getLogger(__name__)


class BaseEventLog(ABC):
    """Abstract interface for Append-Only Event Log."""

    @abstractmethod
    def append(self, event: SessionEvent) -> None:
        """Appends an event to the persistent event stream."""
        pass

    @abstractmethod
    def get_events(self, session_id: Optional[str] = None) -> List[SessionEvent]:
        """Returns the chronological list of events."""
        pass

    @abstractmethod
    def fork(self, up_to_index: int, new_session_id: str) -> "BaseEventLog":
        """Forks event stream up to specific event index into a new session."""
        pass


class InMemoryEventLog(BaseEventLog):
    """
    In-Memory Append-Only Event Stream.
    Supports deterministic replay, branch forking, and JSONL persistence.
    """

    def __init__(self, session_id: str = ""):
        self.session_id = session_id
        self._events: List[SessionEvent] = []

    def append(self, event: SessionEvent) -> None:
        if not event.session_id:
            event.session_id = self.session_id
        self._events.append(event)

    def get_events(self, session_id: Optional[str] = None) -> List[SessionEvent]:
        if session_id:
            return [e for e in self._events if e.session_id == session_id]
        return list(self._events)

    def fork(self, up_to_index: int, new_session_id: str) -> "InMemoryEventLog":
        forked = InMemoryEventLog(session_id=new_session_id)
        sliced = self._events[:up_to_index]
        for e in sliced:
            data = e.to_dict()
            data["session_id"] = new_session_id
            forked.append(SessionEvent.from_dict(data))
        return forked

    def to_jsonl(self) -> str:
        lines = [json.dumps(e.to_dict(), ensure_ascii=False) for e in self._events]
        return "\n".join(lines)

    @classmethod
    def from_jsonl(cls, jsonl_content: str, session_id: str = "") -> "InMemoryEventLog":
        log = cls(session_id=session_id)
        for line in jsonl_content.strip().splitlines():
            line = line.strip()
            if line:
                data = json.loads(line)
                log.append(SessionEvent.from_dict(data))
        return log

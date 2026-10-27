# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, List


class EventTypes:
    # Turn lifecycle
    TURN_START = "turn/start"
    TURN_END = "turn/end"

    # Step lifecycle
    STEP_START = "step/start"
    STEP_END = "step/end"

    # Message payloads
    USER_MESSAGE = "user/message"
    ASSISTANT_CHUNK = "assistant/chunk"
    ASSISTANT_MESSAGE = "assistant/message"

    # Tool invocation
    TOOL_CALL = "tool/call"
    TOOL_RESULT = "tool/result"

    # Run state
    RUN_ERROR = "run/error"
    RUN_COMPLETED = "run/completed"


@dataclass
class SessionEvent:
    """
    Immutable Session Event record for Append-Only Event Stream.
    Guarantees Model-Visible <=> Logged deterministic execution.
    """
    type: str
    payload: Dict[str, Any]
    session_id: str = ""
    turn_id: str = ""
    step: int = 1
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionEvent":
        return cls(**data)

# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

# Microkernel & Event Sourcing
from plane.app.agent.kernel.context import KernelContext
from plane.app.agent.kernel.events import KernelEvents, WaterfallHandler
from plane.app.agent.session.events import SessionEvent, EventTypes
from plane.app.agent.session.event_log import BaseEventLog, InMemoryEventLog
from plane.app.agent.session.projection import derive_messages
from plane.app.agent.session.spilling import SpillingEngine
from plane.app.agent.session.memory import SessionMemory

# Seams & Loop
from plane.app.agent.seams.llm.base import BaseLLMProvider
from plane.app.agent.seams.llm.openai_provider import OpenAILLMProvider
from plane.app.agent.seams.storage.base import BaseStorageProvider
from plane.app.agent.seams.approval.base import BaseApprovalProvider
from plane.app.agent.seams.approval.policy import StandardApprovalProvider, ApprovalPolicy, DESTRUCTIVE_TOOLS
from plane.app.agent.loop.driver import AgentLoopDriver
from plane.app.agent.loop.event_stream import EventStream
from plane.app.agent.loop.quota_guard import QuotaGuard
from plane.app.agent.loop.fast_path import FastPathMatcher


# Lazy / Safe resolution for Django-dependent modules
def __getattr__(name: str):
    if name in ("PlaneAgentEngine", "check_user_project_permission", "PLANE_AGENT_SYSTEM_PROMPT"):
        from plane.app.agent.core import PlaneAgentEngine, check_user_project_permission, PLANE_AGENT_SYSTEM_PROMPT
        return locals()[name]
    if name in ("ToolRegistry", "agent_tool"):
        from plane.app.agent.registry import ToolRegistry, agent_tool
        return locals()[name]
    if name == "PlaneORMStorageProvider":
        from plane.app.agent.seams.storage.plane_provider import PlaneORMStorageProvider
        return PlaneORMStorageProvider
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


__all__ = [
    # Legacy Core Facade (Lazy-loaded)
    "PlaneAgentEngine",
    "check_user_project_permission",
    "PLANE_AGENT_SYSTEM_PROMPT",
    "ToolRegistry",
    "agent_tool",
    # Microkernel & Event Sourcing
    "KernelContext",
    "KernelEvents",
    "WaterfallHandler",
    "SessionEvent",
    "EventTypes",
    "BaseEventLog",
    "InMemoryEventLog",
    "derive_messages",
    "SpillingEngine",
    "SessionMemory",
    # Capability Seams
    "BaseLLMProvider",
    "OpenAILLMProvider",
    "BaseStorageProvider",
    "PlaneORMStorageProvider",
    "BaseApprovalProvider",
    "StandardApprovalProvider",
    "ApprovalPolicy",
    "DESTRUCTIVE_TOOLS",
    # Autonomous Loop
    "AgentLoopDriver",
    "EventStream",
    "QuotaGuard",
    "FastPathMatcher",
]

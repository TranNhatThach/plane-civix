# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

from plane.app.agent.seams.llm import BaseLLMProvider, OpenAILLMProvider
from plane.app.agent.seams.storage import BaseStorageProvider
from plane.app.agent.seams.approval import (
    BaseApprovalProvider,
    ApprovalPolicy,
    StandardApprovalProvider,
    DESTRUCTIVE_TOOLS,
)


def __getattr__(name: str):
    if name == "PlaneORMStorageProvider":
        from plane.app.agent.seams.storage.plane_provider import PlaneORMStorageProvider
        return PlaneORMStorageProvider
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


__all__ = [
    "BaseLLMProvider",
    "OpenAILLMProvider",
    "BaseStorageProvider",
    "PlaneORMStorageProvider",
    "BaseApprovalProvider",
    "ApprovalPolicy",
    "StandardApprovalProvider",
    "DESTRUCTIVE_TOOLS",
]

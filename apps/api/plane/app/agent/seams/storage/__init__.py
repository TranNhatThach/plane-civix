# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

from plane.app.agent.seams.storage.base import BaseStorageProvider


def __getattr__(name: str):
    if name == "PlaneORMStorageProvider":
        from plane.app.agent.seams.storage.plane_provider import PlaneORMStorageProvider
        return PlaneORMStorageProvider
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


__all__ = ["BaseStorageProvider", "PlaneORMStorageProvider"]

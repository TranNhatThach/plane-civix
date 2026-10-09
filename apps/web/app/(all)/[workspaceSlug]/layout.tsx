/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { useEffect } from "react";
import { Outlet, useNavigate, useLocation } from "react-router";
import { AuthenticationWrapper } from "@/lib/wrappers/authentication-wrapper";
import { WorkspaceContentWrapper } from "@/components/workspace/content-wrapper";
import { AppRailVisibilityProvider } from "@/lib/app-rail";
import { GlobalModals } from "@/components/common/modal/global";
import { MustChangePasswordBanner } from "@/components/workspace/must-change-password-banner";
import { WorkspaceAuthWrapper } from "@/layouts/auth-layout/workspace-wrapper";
import type { Route } from "./+types/layout";

export default function WorkspaceLayout(props: Route.ComponentProps) {
  const { workspaceSlug } = props.params;
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    if (workspaceSlug && (workspaceSlug.includes(" ") || workspaceSlug.includes("%20"))) {
      const cleanSlug = workspaceSlug.replace(/%20/g, "-").replace(/\s+/g, "-");
      const cleanPath = location.pathname.replace(workspaceSlug, cleanSlug);
      navigate(cleanPath, { replace: true });
    }
  }, [workspaceSlug, location.pathname, navigate]);

  return (
    <AuthenticationWrapper>
      <WorkspaceAuthWrapper>
        <AppRailVisibilityProvider>
          <WorkspaceContentWrapper>
            <GlobalModals workspaceSlug={workspaceSlug} />
            <MustChangePasswordBanner />
            <Outlet />
          </WorkspaceContentWrapper>
        </AppRailVisibilityProvider>
      </WorkspaceAuthWrapper>
    </AuthenticationWrapper>
  );
}

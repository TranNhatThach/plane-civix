/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { observer } from "mobx-react";
import useSWR from "swr";
// components
import { EUserPermissions, EUserPermissionsLevel } from "@plane/constants";
import { NotAuthorizedView } from "@/components/auth-screens/not-authorized-view";
import { PageHead } from "@/components/core/page-title";
import { SingleIntegrationCard } from "@/components/integration/single-integration-card";
import { IntegrationAndImportExportBanner } from "@/components/ui/integration-and-import-export-banner";
import { IntegrationsSettingsLoader } from "@/components/ui/loader/settings/integration";
// constants
import { APP_INTEGRATIONS } from "@plane/constants";
// hooks
import { useWorkspace } from "@/hooks/store/use-workspace";
import { useUserPermissions } from "@/hooks/store/user";
// services
import { IntegrationService } from "@/services/integrations";

import { TelegramIntegrationForm } from "@/components/integration/telegram/telegram-form";
import { SlackIntegrationForm } from "@/components/integration/slack/slack-form";

import type { Route } from "./+types/page";
import { SettingsContentWrapper } from "@/components/settings/content-wrapper";

const integrationService = new IntegrationService();

function WorkspaceIntegrationsPage({ params }: Route.ComponentProps) {
  const { workspaceSlug } = params;
  // store hooks
  const { currentWorkspace } = useWorkspace();
  const { workspaceUserInfo, allowPermissions } = useUserPermissions();

  // derived values
  const canPerformWorkspaceAdminActions = allowPermissions(
    [EUserPermissions.ADMIN, EUserPermissions.MEMBER],
    EUserPermissionsLevel.WORKSPACE,
    workspaceSlug
  );
  const pageTitle = currentWorkspace?.name ? `${currentWorkspace.name} - Integrations` : undefined;

  const { data: appIntegrations } = useSWR(
    canPerformWorkspaceAdminActions ? APP_INTEGRATIONS : null,
    () => (canPerformWorkspaceAdminActions ? integrationService.getAppIntegrationsList() : null),
    {
      revalidateOnFocus: false,
      shouldRetryOnError: false,
    }
  );

  if (workspaceUserInfo && !canPerformWorkspaceAdminActions) {
    return <NotAuthorizedView section="settings" className="h-auto" />;
  }

  return (
    <SettingsContentWrapper>
      <PageHead title={pageTitle} />
      <section className="w-full space-y-6 overflow-y-auto">
        <IntegrationAndImportExportBanner bannerName="Integrations" />
        {workspaceSlug && (
          <div className="px-6 space-y-6">
            <SlackIntegrationForm workspaceSlug={workspaceSlug} projectId="global" />
            <TelegramIntegrationForm workspaceSlug={workspaceSlug} projectId="global" />
          </div>
        )}
        <div>
          {appIntegrations ? (
            appIntegrations
              .filter((integration) => integration.provider !== "slack")
              .map((integration) => (
                <SingleIntegrationCard key={integration.id} integration={integration} />
              ))
          ) : (
            <IntegrationsSettingsLoader />
          )}
        </div>
      </section>
    </SettingsContentWrapper>
  );
}

export default observer(WorkspaceIntegrationsPage);

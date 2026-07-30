/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { observer } from "mobx-react";
import useSWR from "swr";
// components
import { PageWrapper } from "@/components/common/page-wrapper";
// hooks
import { useInstance } from "@/hooks/store";
// types
import type { Route } from "./+types/page";
// local
import { InstanceAIForm } from "./form";

const InstanceAIPage = observer(function InstanceAIPage(_props: Route.ComponentProps) {
  // store
  const { fetchInstanceConfigurations, formattedConfig } = useInstance();

  useSWR("INSTANCE_CONFIGURATIONS", () => fetchInstanceConfigurations());

  return (
    <PageWrapper
      header={{
        title: "AI features for all your workspaces",
        description: "Configure your AI API credentials so Plane AI features are turned on for all your workspaces.",
      }}
    >
      <InstanceAIForm config={formattedConfig ?? {}} />
    </PageWrapper>
  );
});

export const meta: Route.MetaFunction = () => [{ title: "Artificial Intelligence Settings - God Mode" }];

export default InstanceAIPage;

import React from "react";
import { observer } from "mobx-react";
import { CivixChangelogTimeline } from "@/components/changelog";

export const ProductUpdatesChangelog = observer(function ProductUpdatesChangelog() {
  return (
    <div className="vertical-scrollbar relative mx-0.5 flex scrollbar-xs h-[550px] flex-col overflow-hidden overflow-y-scroll px-6 py-4">
      <CivixChangelogTimeline />
    </div>
  );
});

/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import React from "react";
import { cn } from "@plane/utils";

interface AudioWaveformProps {
  active?: boolean;
  className?: string;
}

export const AudioWaveform: React.FC<AudioWaveformProps> = ({ active = true, className }) => {
  return (
    <div className={cn("flex items-center gap-1 h-4", className)}>
      {[0.4, 0.9, 0.6, 1.0, 0.5, 0.8].map((scale, i) => (
        <span
          key={i}
          className={cn(
            "w-1 bg-gradient-to-t from-indigo-500 via-purple-500 to-pink-500 rounded-full transition-all duration-300",
            active ? "animate-pulse" : "h-1 opacity-50"
          )}
          style={{
            height: active ? `${Math.max(4, scale * 16)}px` : "4px",
            animationDelay: `${i * 120}ms`,
          }}
        />
      ))}
    </div>
  );
};

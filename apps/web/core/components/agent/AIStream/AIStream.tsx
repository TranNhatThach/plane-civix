/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@plane/utils";
import { useAIStream } from "./useAIStream";
import { AIStreamButton } from "./AIStreamButton";
import { AIStreamPanel } from "./AIStreamPanel";

export const AIStream: React.FC = () => {
  const {
    state,
    input,
    setInput,
    messages,
    containerRef,
    inputRef,
    isListening,
    toggleListening,
    expand,
    collapse,
    submitPrompt,
    suggestions,
  } = useAIStream();

  const isCollapsed = state === "collapsed";

  return (
    <div ref={containerRef} className="pointer-events-auto fixed right-6 bottom-6 z-[100] max-w-[calc(100vw-24px)]">
      <motion.div
        layout
        transition={{
          type: "spring",
          stiffness: 380,
          damping: 28,
        }}
        className={cn(
          "overflow-hidden backdrop-blur-2xl transition-shadow duration-300",
          "bg-neutral-950/95 border border-white/15 shadow-[0_20px_60px_rgba(0,0,0,0.7)]",
          isCollapsed
            ? "h-[48px] w-[200px] rounded-full hover:border-white/30"
            : "h-auto w-[460px] max-w-[calc(100vw-48px)] rounded-3xl"
        )}
      >
        <AnimatePresence mode="wait" initial={false}>
          {isCollapsed ? (
            <motion.div
              key="collapsed-pill"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              transition={{ duration: 0.15 }}
              className="h-full w-full"
            >
              <AIStreamButton state={state} onClick={expand} />
            </motion.div>
          ) : (
            <motion.div
              key="expanded-panel"
              initial={{ opacity: 0, scale: 0.96 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.96 }}
              transition={{ duration: 0.2 }}
              className="h-full w-full"
            >
              <AIStreamPanel
                state={state}
                input={input}
                setInput={setInput}
                messages={messages}
                suggestions={suggestions}
                onClose={collapse}
                onSubmit={submitPrompt}
                isListening={isListening}
                onToggleListening={toggleListening}
                inputRef={inputRef as React.Ref<HTMLTextAreaElement>}
              />
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </div>
  );
};

export default AIStream;

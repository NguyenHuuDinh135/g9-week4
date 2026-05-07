"use client";

import { AssistantRuntimeProvider } from "@assistant-ui/react";
import { useChatRuntime } from "@/lib/chat-runtime";
import { TraceToolUI } from "@/components/assistant-ui/trace-tool-ui";

export function ChatProvider({ children }: { children: React.ReactNode }) {
  const runtime = useChatRuntime();
  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <TraceToolUI />
      {children}
    </AssistantRuntimeProvider>
  );
}

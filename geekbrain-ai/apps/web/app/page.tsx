"use client";

import { ChatProvider } from "./providers";
import { Thread } from "@/components/assistant-ui/thread";

export default function Page() {
  return (
    <ChatProvider>
      <div className="h-svh">
        <Thread />
      </div>
    </ChatProvider>
  );
}

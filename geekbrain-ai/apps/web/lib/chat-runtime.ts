"use client";

import type { ChatModelAdapter } from "@assistant-ui/react";
import { useLocalRuntime } from "@assistant-ui/react";

const chatModelAdapter: ChatModelAdapter = {
  async *run({ messages, abortSignal }) {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        messages: messages.map((m) => ({
          role: m.role,
          content:
            m.content
              .filter((p): p is { type: "text"; text: string } => p.type === "text")
              .map((p) => p.text)
              .join("") || "",
        })),
      }),
      signal: abortSignal,
    });

    if (!response.ok) {
      throw new Error(`Chat failed: ${response.status}`);
    }

    const reader = response.body?.getReader();
    if (!reader) throw new Error("No response body");

    const decoder = new TextDecoder();
    let fullText = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value, { stream: true });
      const lines = chunk.split("\n");

      for (const line of lines) {
        if (line.startsWith("data:")) {
          try {
            const data = JSON.parse(line.slice(5).trim());
            if (data.type === "text") {
              fullText = data.content;
              yield { content: [{ type: "text" as const, text: fullText }] };
            }
          } catch {
            // skip malformed SSE lines
          }
        }
      }
    }
  },
};

export function useChatRuntime() {
  return useLocalRuntime(chatModelAdapter);
}

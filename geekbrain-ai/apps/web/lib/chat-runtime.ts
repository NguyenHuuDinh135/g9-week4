"use client";

import type { ChatModelAdapter } from "@assistant-ui/react";
import { useLocalRuntime } from "@assistant-ui/react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

const THREAD_ID = typeof crypto !== "undefined"
  ? crypto.randomUUID()
  : Math.random().toString(36).slice(2);

const chatModelAdapter: ChatModelAdapter = {
  async *run({ messages, abortSignal }) {
    const response = await fetch(`${API_BASE}/api/chat`, {
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
        thread_id: THREAD_ID,
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
    let traceText = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value, { stream: true });
      const lines = chunk.split("\n");

      for (const line of lines) {
        if (line.startsWith("data:")) {
          try {
            const data = JSON.parse(line.slice(5).trim());
            if (data.type === "trace") {
              const step = data.step === "kb_retrieval"
                ? `📚 KB Retrieval: ${data.data.results_count} docs found (${data.data.sources?.map((s: { source: string; score: number }) => s.source.split("/").pop()).join(", ") || "none"})`
                : `🔧 Tool: ${data.data.tool}(${JSON.stringify(data.data.input).slice(0, 80)})`;
              traceText += step + "\n";
              yield {
                content: [
                  { type: "reasoning" as const, text: traceText },
                  { type: "text" as const, text: "⏳ Processing..." },
                ],
              };
            } else if (data.type === "text") {
              fullText = data.content;
              if (traceText) {
                yield {
                  content: [
                    { type: "reasoning" as const, text: traceText },
                    { type: "text" as const, text: fullText },
                  ],
                };
              } else {
                yield { content: [{ type: "text" as const, text: fullText }] };
              }
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
  return useLocalRuntime(chatModelAdapter, {
    adapters: {
      suggestion: {
        generate: async () => [
          { prompt: "[L1] What is the current API rate limit for PaymentGW?" },
          { prompt: "[L1] Who leads Team Platform and what services do they own?" },
          { prompt: "[L1] What was the root cause of the March 5, 2026 PaymentGW outage?" },
          { prompt: "[L2] What is PaymentGW's API rate limit?" },
          { prompt: "[L2] If Team Commerce discovers a P1 bug in OrderSvc at 21:00 on a Friday, can they deploy a fix?" },
          { prompt: "[L2] Which services would be directly affected if AuthSvc goes completely down?" },
          { prompt: "[L3] What is PaymentGW's current p99 latency?" },
          { prompt: "[L3] What was GeekBrain's total infrastructure cost across all services in Q1 2026?" },
          { prompt: "[L3] Is NotificationSvc currently meeting its SLA targets?" },
          { prompt: "[L3] Which service currently handles the most requests per minute?" },
          { prompt: "[L4] Which service had the highest cost in March 2026?" },
          { prompt: "[L5] Assess whether PaymentGW is reliable and recommend improvements." },
          { prompt: "[L5] Which service is most at risk of SLA breach right now? What should be done?" },
        ],
      },
    },
  });
}

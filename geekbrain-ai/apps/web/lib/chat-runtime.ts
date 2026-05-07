"use client";

import type { ChatModelAdapter } from "@assistant-ui/react";
import { useLocalRuntime } from "@assistant-ui/react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

const THREAD_ID =
  typeof crypto !== "undefined"
    ? crypto.randomUUID()
    : Math.random().toString(36).slice(2);

interface TraceStep {
  step: string;
  data: Record<string, unknown>;
}

function buildTraceToolResult(steps: TraceStep[]) {
  const progressSteps = steps.map((s, i) => {
    if (s.step === "kb_retrieval") {
      const count = (s.data.results_count as number) || 0;
      const sources = (s.data.sources as { source: string; score: number }[]) || [];
      const sourceNames = sources.map((src) => src.source.split("/").pop()).join(", ");
      return {
        id: `step-${i}`,
        label: `KB Retrieval: ${count} docs found`,
        description: sourceNames || undefined,
        status: "completed" as const,
      };
    }
    const tool = s.data.tool as string;
    const input = s.data.input as Record<string, unknown>;
    let desc = "";
    if (tool === "query_database") {
      desc = (input.sql as string || "").slice(0, 100);
    } else if (tool === "get_service_status" || tool === "get_service_metrics") {
      desc = input.service_name as string || "";
    }
    return {
      id: `step-${i}`,
      label: `Tool: ${tool}`,
      description: desc || undefined,
      status: "completed" as const,
    };
  });

  return {
    id: "trace-progress",
    steps: progressSteps,
    choice: { outcome: "success" as const, summary: "Pipeline complete", at: new Date().toISOString() },
  };
}

const chatModelAdapter = {
  async *run({ messages, abortSignal }: { messages: Array<{ role: string; content: Array<{ type: string; text?: string }> }>; abortSignal: AbortSignal }) {
    const response = await fetch(`${API_BASE}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        messages: messages.map((m) => ({
          role: m.role,
          content:
            m.content
              .filter(
                (p): p is { type: "text"; text: string } => p.type === "text",
              )
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
    let reasoningText = "";
    const traceSteps: TraceStep[] = [];
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

            if (data.type === "reasoning") {
              reasoningText = data.content;
              yield {
                content: [
                  { type: "reasoning" as const, text: reasoningText },
                  { type: "text" as const, text: "Thinking..." },
                ],
              };
            } else if (data.type === "trace") {
              traceSteps.push({ step: data.step, data: data.data });
              const parts: Array<
                | { type: "reasoning"; text: string }
                | { type: "tool-call"; toolCallId: string; toolName: string; args: Record<string, unknown>; argsText: string; result?: unknown }
                | { type: "text"; text: string }
              > = [];
              if (reasoningText) {
                parts.push({ type: "reasoning" as const, text: reasoningText });
              }
              const traceArgs = buildTraceToolResult(traceSteps);
              parts.push({
                type: "tool-call" as const,
                toolCallId: "trace-pipeline",
                toolName: "geekbrain_trace",
                args: traceArgs,
                argsText: JSON.stringify(traceArgs),
              });
              parts.push({ type: "text" as const, text: "Processing..." });
              yield { content: parts };
            } else if (data.type === "text") {
              fullText = data.content;
              const parts: Array<
                | { type: "reasoning"; text: string }
                | { type: "tool-call"; toolCallId: string; toolName: string; args: Record<string, unknown>; argsText: string; result?: unknown }
                | { type: "text"; text: string }
              > = [];
              if (reasoningText) {
                parts.push({ type: "reasoning" as const, text: reasoningText });
              }
              if (traceSteps.length > 0) {
                const traceArgs = buildTraceToolResult(traceSteps);
                parts.push({
                  type: "tool-call" as const,
                  toolCallId: "trace-pipeline",
                  toolName: "geekbrain_trace",
                  args: traceArgs,
                  argsText: JSON.stringify(traceArgs),
                  result: { complete: true },
                });
              }
              parts.push({ type: "text" as const, text: fullText });
              yield { content: parts };
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
  return useLocalRuntime(chatModelAdapter as unknown as ChatModelAdapter, {
    adapters: {
      suggestion: {
        generate: async () => [
          { prompt: "[L1] What is the current API rate limit for PaymentGW?" },
          { prompt: "[L1] Who leads Team Platform and what services do they own?" },
          { prompt: "[L1] What was the root cause of the March 5, 2026 PaymentGW outage?" },
          { prompt: "[L1] What is GeekBrain's data retention policy for transaction logs?" },
          { prompt: "[L1] What are GeekBrain's production deployment windows?" },
          { prompt: "[L1] What authentication method does the PaymentGW API use?" },
          { prompt: "[L1] What message queue does NotificationSvc use?" },
          { prompt: "[L1] What programming language is AuthSvc written in?" },
          { prompt: "[L1] How often does GeekBrain rotate JWT signing keys?" },
          { prompt: "[L2] What is PaymentGW's API rate limit?" },
          { prompt: "[L2] If Team Commerce discovers a P1 bug in OrderSvc at 21:00 on a Friday, can they deploy a fix?" },
          { prompt: "[L2] Which services would be directly affected if AuthSvc goes completely down?" },
          { prompt: "[L2] Based on the Q1 review and cost optimization initiative, which services are top priorities for cost reduction?" },
          { prompt: "[L2] What common lessons emerged from the March 2026 incidents at PaymentGW and FraudDetector?" },
          { prompt: "[L2] What is the complete escalation path for a P1 incident on PaymentGW?" },
          { prompt: "[L3] What is PaymentGW's current p99 latency?" },
          { prompt: "[L3] What was GeekBrain's total infrastructure cost across all services in Q1 2026?" },
          { prompt: "[L3] Is NotificationSvc currently meeting its SLA targets?" },
          { prompt: "[L3] Which service currently handles the most requests per minute?" },
          { prompt: "[L3] Which service had the highest total cost in March 2026?" },
          { prompt: "[L3] How many total incidents occurred in Q1 2026, and which service had the most?" },
          { prompt: "[L3] Is PaymentGW's current error rate within its SLA target?" },
          { prompt: "[L3] Compare PaymentGW's current p99 latency to its Q1 2026 daily average." },
          { prompt: "[L3] What is FraudDetector's current CPU utilization compared to other services?" },
          { prompt: "[L5] Assess whether PaymentGW is reliable and recommend improvements." },
          { prompt: "[L5] Which service is most at risk of SLA breach right now? What should be done?" },
          { prompt: "[L5] GeekBrain wants to cut infrastructure costs by 15% in Q2. Analyze current spending and recommend optimizations." },
          { prompt: "[L5] Prepare a Q1 2026 reliability report card for all GeekBrain services." },
        ],
      },
    },
  });
}

"use client";

import { makeAssistantToolUI } from "@assistant-ui/react";
import { ProgressTracker } from "@/components/tool-ui/progress-tracker";

export const TraceToolUI = makeAssistantToolUI({
  toolName: "geekbrain_trace",
  render: ({ args }) => {
    const data = args as {
      id: string;
      steps: Array<{
        id: string;
        label: string;
        description?: string;
        status: "pending" | "in-progress" | "completed" | "failed";
      }>;
      choice?: { outcome: "success" | "partial" | "failed" | "cancelled"; summary: string; at: string };
    };

    if (!data?.steps?.length) return null;

    return (
      <div className="my-3">
        <ProgressTracker
          id={data.id}
          steps={data.steps}
          choice={data.choice}
        />
      </div>
    );
  },
});

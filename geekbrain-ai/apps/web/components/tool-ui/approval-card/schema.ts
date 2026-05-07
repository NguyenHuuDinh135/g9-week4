import { z } from "zod";
import { ToolUIIdSchema, ToolUIRoleSchema } from "../shared/schema";
import { defineToolUiContract } from "../shared/contract";

export const MetadataItemSchema = z.object({
  key: z.string().min(1),
  value: z.string(),
});

export type MetadataItem = z.infer<typeof MetadataItemSchema>;

export const ApprovalDecisionSchema = z.enum(["approved", "denied"]);

export type ApprovalDecision = z.infer<typeof ApprovalDecisionSchema>;

export const SerializableApprovalCardSchema = z.object({
  id: ToolUIIdSchema,
  role: ToolUIRoleSchema.optional(),

  title: z.string().min(1),
  description: z.string().optional(),
  icon: z.string().optional(),
  metadata: z.array(MetadataItemSchema).optional(),

  variant: z.enum(["default", "destructive"]).optional(),

  confirmLabel: z.string().optional(),
  cancelLabel: z.string().optional(),

  choice: ApprovalDecisionSchema.optional(),
});

export type SerializableApprovalCard = z.infer<
  typeof SerializableApprovalCardSchema
>;

const SerializableApprovalCardSchemaContract = defineToolUiContract(
  "ApprovalCard",
  SerializableApprovalCardSchema,
);

export const parseSerializableApprovalCard: (
  input: unknown,
) => SerializableApprovalCard = SerializableApprovalCardSchemaContract.parse;

export const safeParseSerializableApprovalCard: (
  input: unknown,
) => SerializableApprovalCard | null =
  SerializableApprovalCardSchemaContract.safeParse;
export interface ApprovalCardProps {
  id: string;
  role?: z.infer<typeof ToolUIRoleSchema>;
  title: string;
  description?: string;
  icon?: string;
  metadata?: MetadataItem[];
  variant?: "default" | "destructive";
  confirmLabel?: string;
  cancelLabel?: string;
  choice?: ApprovalDecision;
  className?: string;
  onConfirm?: () => void | Promise<void>;
  onCancel?: () => void | Promise<void>;
}

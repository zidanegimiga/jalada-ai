import { cn } from "@/shared/styles/cn";

import { ActionCard } from "../ActionCard";

import type { ChatMessage } from "../../types";

const LINK = /(https?:\/\/[^\s)]+[^\s).,])/g;

/** Text with its web addresses as links, such as the tax-year workbook. */
function withLinks(text: string) {
  return text.split(LINK).map((part, index) =>
    index % 2 === 1 ? (
      <a
        key={index}
        href={part}
        className="break-all underline underline-offset-4"
      >
        {part}
      </a>
    ) : (
      part
    ),
  );
}

/** One message: the person's on the right in the dark ink, the assistant's on a card. */
export function MessageBubble({ message }: { message: ChatMessage }) {
  const mine = message.role === "person";
  const actions = message.actions ?? [];
  return (
    <li
      className={cn("flex flex-col gap-2", mine ? "items-end" : "items-start")}
    >
      <div
        className={cn(
          "max-w-[85%] rounded-card px-4 py-3 whitespace-pre-line motion-safe:animate-in motion-safe:fade-in motion-safe:slide-in-from-bottom-1 motion-safe:duration-300",
          mine
            ? "rounded-br-sm bg-foreground text-background"
            : "rounded-bl-sm border border-border bg-card",
        )}
      >
        <span className="sr-only">{mine ? "You: " : "Assistant: "}</span>
        {withLinks(message.text)}
      </div>
      {actions.length > 0 && (
        <div className="flex w-full max-w-[85%] flex-col gap-2">
          {actions.map((action) => (
            <ActionCard key={action.id} action={action} />
          ))}
        </div>
      )}
    </li>
  );
}

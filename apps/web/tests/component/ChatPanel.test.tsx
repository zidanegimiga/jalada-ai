import {
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ChatPanel } from "@/features/agent/components/ChatPanel";
import { MessageBubble } from "@/features/agent/components/MessageBubble";
import { AskLayout } from "@/features/agent/components/AskLayout";
import { ThreadHistory } from "@/features/agent/components/ThreadHistory";
import { ToolActivity } from "@/features/agent/components/ToolActivity";

/** A streamed reply, one chunk per event, as the API sends it. */
function streams(...events: string[]) {
  const body = new ReadableStream<Uint8Array>({
    start(controller) {
      for (const event of events)
        controller.enqueue(new TextEncoder().encode(event));
      controller.close();
    },
  });
  const fetch = vi.fn().mockResolvedValue(
    new Response(body, {
      status: 200,
      headers: { "Content-Type": "text/event-stream" },
    }),
  );
  vi.stubGlobal("fetch", fetch);
  return fetch;
}

const LOOKING =
  'event: progress\ndata: {"stage": "looking_up", "tool": "add_up_payments", "label": "Adding up your payments"}\n\n';
const ANSWER =
  'event: answer\ndata: {"thread_id": "thread-1", "text": "You paid KPLC Ksh 4,500.00.", "outcome": "answered"}\n\n';

function ask(question: string) {
  fireEvent.change(screen.getByLabelText("Your question"), {
    target: { value: question },
  });
  fireEvent.click(screen.getByRole("button", { name: "Send" }));
}

describe("ChatPanel", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("offers questions to start with", () => {
    render(<ChatPanel initial={null} />);

    expect(
      screen.getByRole("button", {
        name: "Is anything waiting for me to check?",
      }),
    ).toBeInTheDocument();
  });

  it("sends the question and shows the answer", async () => {
    const fetch = streams(LOOKING, ANSWER);
    const replace = vi.spyOn(window.history, "replaceState");
    render(<ChatPanel initial={null} />);

    ask("How much did I pay KPLC?");

    expect(
      await screen.findByText("You paid KPLC Ksh 4,500.00."),
    ).toBeInTheDocument();
    expect(screen.getByText("How much did I pay KPLC?")).toBeInTheDocument();
    expect(JSON.parse(fetch.mock.calls[0][1].body)).toEqual({
      question: "How much did I pay KPLC?",
      thread_id: null,
    });
    expect(replace).toHaveBeenCalledWith(null, "", "/ask?thread=thread-1");
  });

  it("continues the conversation it was opened with", async () => {
    const fetch = streams(ANSWER);
    render(
      <ChatPanel
        initial={{
          id: "thread-9",
          title: "KPLC",
          messages: [
            { role: "person", text: "KPLC?", at: "2026-11-18T09:00:00Z" },
            {
              role: "assistant",
              text: "Ksh 4,500.00.",
              at: "2026-11-18T09:00:05Z",
            },
          ],
        }}
      />,
    );

    ask("And in August?");

    await screen.findByText("You paid KPLC Ksh 4,500.00.");
    expect(JSON.parse(fetch.mock.calls[0][1].body).thread_id).toBe("thread-9");
  });

  it("gives the question back when it could not be sent", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            error: {
              message: "Too many attempts. Wait a minute and try again.",
            },
          }),
          { status: 429 },
        ),
      ),
    );
    render(<ChatPanel initial={null} />);

    ask("How much did I pay KPLC?");

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Too many attempts",
    );
    await waitFor(() =>
      expect(screen.getByLabelText("Your question")).toHaveValue(
        "How much did I pay KPLC?",
      ),
    );
    expect(
      screen.queryByRole("list", { name: "Conversation" }),
    ).not.toBeInTheDocument();
  });

  it("shows an error the stream ends with", async () => {
    streams(
      'event: error\ndata: {"code": "assistant_failed", "message": "Something went wrong. Please try again."}\n\n',
    );
    render(<ChatPanel initial={null} />);

    ask("Hello");

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Something went wrong",
    );
  });
});

describe("ToolActivity", () => {
  it("keeps each lookup on show while the assistant thinks again", () => {
    render(
      <ToolActivity
        progress={{ stage: "thinking", tool: null, label: null }}
        lookups={["Adding up your payments"]}
      />,
    );

    expect(screen.getByRole("status")).toHaveTextContent(
      "Adding up your paymentsThinking...",
    );
  });

  it("is empty between turns", () => {
    render(<ToolActivity progress={null} lookups={[]} />);

    expect(screen.getByRole("status")).toBeEmptyDOMElement();
  });
});

describe("MessageBubble", () => {
  it("turns web addresses into links", () => {
    render(
      <ul>
        <MessageBubble
          message={{
            role: "assistant",
            text: "Here it is: https://jalada.example/v1/exports/2025.xlsx.",
            at: "2026-11-18T09:00:00Z",
          }}
        />
      </ul>,
    );

    expect(
      screen.getByRole("link", {
        name: "https://jalada.example/v1/exports/2025.xlsx",
      }),
    ).toHaveAttribute("href", "https://jalada.example/v1/exports/2025.xlsx");
  });
});

describe("ThreadHistory", () => {
  const threads = [
    {
      id: "t-1",
      title: "KPLC this quarter",
      updated_at: "2026-11-18T09:00:00Z",
    },
    { id: "t-2", title: "Rent in July", updated_at: "2026-11-17T09:00:00Z" },
  ];

  it("lists earlier conversations, marks the current one, and offers a new one", () => {
    render(<ThreadHistory threads={threads} current="t-1" />);

    expect(
      screen.getByRole("link", { name: /New conversation/ }),
    ).toHaveAttribute("href", "/ask");
    expect(
      screen.getByRole("link", { name: /KPLC this quarter/ }),
    ).toHaveAttribute("aria-current", "page");
    expect(screen.getByRole("link", { name: /Rent in July/ })).toHaveAttribute(
      "href",
      "/ask?thread=t-2",
    );
  });

  it("tells a new person where conversations will appear", () => {
    render(<ThreadHistory threads={[]} current={null} />);

    expect(
      screen.getByText("Your conversations will be listed here."),
    ).toBeInTheDocument();
  });
});

describe("AskLayout", () => {
  it("puts a new conversation at the top of the history once it is answered", async () => {
    streams(ANSWER);
    vi.spyOn(window.history, "replaceState");
    render(
      <AskLayout threads={[]} current={null}>
        <ChatPanel initial={null} />
      </AskLayout>,
    );

    ask("How much did I pay KPLC?");

    const rail = screen.getAllByRole("navigation", {
      name: "Conversations",
    })[0];
    expect(
      await within(rail).findByRole("link", {
        name: /How much did I pay KPLC\?/,
      }),
    ).toHaveAttribute("aria-current", "page");
  });

  it("opens the history as a drawer and closes it when a conversation is picked", async () => {
    render(
      <AskLayout
        threads={[
          {
            id: "t-1",
            title: "KPLC this quarter",
            updated_at: "2026-11-18T09:00:00Z",
          },
        ]}
        current={null}
      >
        <p>chat</p>
      </AskLayout>,
    );

    fireEvent.click(screen.getByRole("button", { name: "History" }));
    const drawer = await screen.findByRole("dialog", { name: "Conversations" });
    fireEvent.click(
      within(drawer).getByRole("link", { name: /KPLC this quarter/ }),
    );

    await waitFor(() =>
      expect(
        screen.queryByRole("dialog", { name: "Conversations" }),
      ).not.toBeInTheDocument(),
    );
  });
});

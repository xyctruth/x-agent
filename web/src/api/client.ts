const apiBaseUrl = import.meta.env.VITE_X_AGENT_API_BASE_URL ?? "http://127.0.0.1:8000";

export type AgentSession = {
  id: string;
  title: string | null;
  status: "active" | "archived";
  created_at: string;
  updated_at: string;
  metadata: Record<string, string>;
};

export type AgentMessage = {
  id: string;
  session_id: string;
  role: "user" | "assistant" | "system";
  content: string;
  created_at: string;
  metadata: Record<string, string>;
};

type AgentMessageSendResponse = {
  messages: AgentMessage[];
};

type StreamAgentMessageHandlers = {
  onUserMessage: (message: AgentMessage) => void;
  onAssistantDelta: (content: string) => void;
  onAssistantMessage: (message: AgentMessage) => void;
};

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers
    }
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const detail = typeof body?.detail === "string" ? body.detail : "请求失败";
    throw new Error(detail);
  }

  return (await response.json()) as T;
}

export async function createAgentSession(title: string): Promise<AgentSession> {
  return request<AgentSession>("/api/v1/agent-sessions", {
    method: "POST",
    body: JSON.stringify({
      title,
      metadata: {
        client: "web",
        entrypoint: "first-message"
      }
    })
  });
}

export async function createAgentMessage(
  sessionId: string,
  content: string
): Promise<AgentMessage[]> {
  const response = await request<AgentMessageSendResponse>(
    `/api/v1/agent-sessions/${sessionId}/messages`,
    {
      method: "POST",
      body: JSON.stringify({
        content,
        metadata: {
          client: "web"
        }
      })
    }
  );
  return response.messages;
}

export async function streamAgentMessage(
  sessionId: string,
  content: string,
  handlers: StreamAgentMessageHandlers
): Promise<void> {
  const response = await fetch(`${apiBaseUrl}/api/v1/agent-sessions/${sessionId}/messages/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      content,
      metadata: {
        client: "web"
      }
    })
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const detail = typeof body?.detail === "string" ? body.detail : "请求失败";
    throw new Error(detail);
  }
  if (!response.body) {
    throw new Error("浏览器不支持流式响应");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) {
      buffer += decoder.decode();
      break;
    }

    buffer += decoder.decode(value, { stream: true });
    buffer = dispatchBufferedEvents(buffer, handlers);
  }

  dispatchBufferedEvents(buffer, handlers);
}

export async function listAgentMessages(sessionId: string): Promise<AgentMessage[]> {
  return request<AgentMessage[]>(`/api/v1/agent-sessions/${sessionId}/messages`);
}

function dispatchBufferedEvents(
  buffer: string,
  handlers: StreamAgentMessageHandlers
): string {
  let remaining = buffer;
  let separatorIndex = remaining.indexOf("\n\n");

  while (separatorIndex >= 0) {
    const rawEvent = remaining.slice(0, separatorIndex);
    dispatchStreamEvent(rawEvent, handlers);
    remaining = remaining.slice(separatorIndex + 2);
    separatorIndex = remaining.indexOf("\n\n");
  }

  return remaining;
}

function dispatchStreamEvent(
  rawEvent: string,
  handlers: StreamAgentMessageHandlers
): void {
  const lines = rawEvent.split("\n");
  let event = "message";
  const dataLines: string[] = [];

  for (const line of lines) {
    if (line.startsWith("event:")) {
      event = line.slice("event:".length).trim();
    }
    if (line.startsWith("data:")) {
      dataLines.push(line.slice("data:".length).trimStart());
    }
  }

  const data = dataLines.join("\n");
  if (event === "done" || data.length === 0) {
    return;
  }

  const payload = JSON.parse(data) as unknown;
  if (event === "user_message") {
    handlers.onUserMessage(payload as AgentMessage);
    return;
  }
  if (event === "assistant_delta") {
    const content = typeof (payload as { content?: unknown }).content === "string"
      ? (payload as { content: string }).content
      : "";
    handlers.onAssistantDelta(content);
    return;
  }
  if (event === "assistant_message") {
    handlers.onAssistantMessage(payload as AgentMessage);
    return;
  }
  if (event === "error") {
    const detail = typeof (payload as { detail?: unknown }).detail === "string"
      ? (payload as { detail: string }).detail
      : "Agent 执行失败";
    throw new Error(detail);
  }
}

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

export async function listAgentMessages(sessionId: string): Promise<AgentMessage[]> {
  return request<AgentMessage[]>(`/api/v1/agent-sessions/${sessionId}/messages`);
}

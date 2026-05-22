import { FormEvent, useMemo, useState } from "react";

import {
  AgentMessage,
  AgentSession,
  createAgentMessage,
  createAgentSession,
  listAgentMessages
} from "./api/client";

function buildSessionTitle(content: string): string {
  const normalized = content.trim().replace(/\s+/g, " ");
  return normalized.length > 30 ? `${normalized.slice(0, 30)}...` : normalized;
}

function formatTime(value: string): string {
  return new Intl.DateTimeFormat("zh-CN", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit"
  }).format(new Date(value));
}

export function App() {
  const [session, setSession] = useState<AgentSession | null>(null);
  const [messages, setMessages] = useState<AgentMessage[]>([]);
  const [draft, setDraft] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canSend = useMemo(() => draft.trim().length > 0 && !isSending, [draft, isSending]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!canSend) {
      return;
    }

    const content = draft.trim();
    setDraft("");
    setError(null);
    setIsSending(true);

    try {
      const activeSession = session ?? (await createAgentSession(buildSessionTitle(content)));
      if (!session) {
        setSession(activeSession);
      }

      await createAgentMessage(activeSession.id, content);
      const nextMessages = await listAgentMessages(activeSession.id);
      setMessages(nextMessages);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "发送失败");
      setDraft(content);
    } finally {
      setIsSending(false);
    }
  }

  return (
    <main className="shell">
      <aside className="sidebar" aria-label="会话信息">
        <div>
          <p className="eyebrow">x-agent</p>
          <h1>Web Client</h1>
        </div>

        <section className="session-panel">
          <h2>当前会话</h2>
          {session ? (
            <dl>
              <div>
                <dt>标题</dt>
                <dd>{session.title}</dd>
              </div>
              <div>
                <dt>状态</dt>
                <dd>{session.status}</dd>
              </div>
              <div>
                <dt>ID</dt>
                <dd className="session-id">{session.id}</dd>
              </div>
            </dl>
          ) : (
            <p className="empty-copy">输入第一条消息后自动创建会话。</p>
          )}
        </section>
      </aside>

      <section className="workspace" aria-label="消息区">
        <div className="message-list" aria-live="polite">
          {messages.length === 0 ? (
            <div className="empty-state">
              <h2>开始一次 Agent 会话</h2>
              <p>第一条消息会创建 session，并保存为 user message。</p>
            </div>
          ) : (
            messages.map((message) => (
              <article className="message" key={message.id}>
                <div className="message-meta">
                  <span>{message.role}</span>
                  <time dateTime={message.created_at}>{formatTime(message.created_at)}</time>
                </div>
                <p>{message.content}</p>
              </article>
            ))
          )}
        </div>

        {error ? <p className="error-banner">{error}</p> : null}

        <form className="composer" onSubmit={handleSubmit}>
          <label htmlFor="message-input">消息</label>
          <textarea
            id="message-input"
            name="message"
            placeholder="输入要交给 Agent 的第一条任务..."
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            rows={3}
          />
          <button disabled={!canSend} type="submit">
            {isSending ? "发送中" : "发送"}
          </button>
        </form>
      </section>
    </main>
  );
}


"use client";

import { FormEvent, useEffect, useState } from "react";
import { RequireAuth } from "@/components/RequireAuth";
import { api, ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Ticket } from "@/lib/types";

export default function SupportPage() {
  return (
    <RequireAuth>
      <SupportInner />
    </RequireAuth>
  );
}

function SupportInner() {
  const { user } = useAuth();
  const [ticket, setTicket] = useState<Ticket | null>(null);
  const [body, setBody] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const load = async () => {
    try {
      setTicket(await api<Ticket | null>("/api/support/mine"));
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Ошибка");
    }
  };

  useEffect(() => {
    void load();
    const id = setInterval(() => void load(), 10000);
    return () => clearInterval(id);
  }, []);

  const send = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const t = await api<Ticket>("/api/support/mine/messages", {
        method: "POST",
        body: JSON.stringify({ body }),
      });
      setTicket(t);
      setBody("");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Не отправлено");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="stack">
      <div className="panel">
        <h2>Техподдержка</h2>
        <p className="muted">Один общий диалог на команду. Администраторы получат уведомление в колокольчик.</p>
      </div>
      {error && <div className="alert error">{error}</div>}
      <div className="panel">
        <div className="chat">
          {!ticket?.messages?.length && <p className="muted">Напишите первый вопрос организаторам.</p>}
          {ticket?.messages.map((m) => (
            <div
              key={m.id}
              className={`bubble ${m.author_id === user?.id ? "mine" : ""} ${m.author_role === "admin" ? "admin" : ""}`}
            >
              <div className="meta">
                @{m.author_username} · {new Date(m.created_at).toLocaleString("ru-RU")}
                {m.author_role === "admin" ? " · админ" : ""}
              </div>
              <div>{m.body}</div>
            </div>
          ))}
        </div>
        <form onSubmit={send} style={{ marginTop: "1rem" }}>
          <div className="field">
            <label>Сообщение</label>
            <textarea rows={3} value={body} onChange={(e) => setBody(e.target.value)} required />
          </div>
          <button className="btn btn-primary" type="submit" disabled={busy}>
            Отправить
          </button>
        </form>
      </div>
    </div>
  );
}

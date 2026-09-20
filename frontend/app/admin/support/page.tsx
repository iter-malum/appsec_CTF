"use client";

import { FormEvent, useEffect, useState } from "react";
import { RequireAuth } from "@/components/RequireAuth";
import { api, ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Ticket } from "@/lib/types";

export default function AdminSupportPage() {
  return (
    <RequireAuth admin>
      <SupportInner />
    </RequireAuth>
  );
}

function SupportInner() {
  const { user } = useAuth();
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [selected, setSelected] = useState<Ticket | null>(null);
  const [body, setBody] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const load = async () => {
    const list = await api<Ticket[]>("/api/support/tickets");
    setTickets(list);
    if (selected) {
      const fresh = list.find((t) => t.id === selected.id) || null;
      setSelected(fresh);
    }
  };

  useEffect(() => {
    void load().catch((e) => setError(e.message));
    const id = setInterval(() => void load().catch(() => undefined), 10000);
    return () => clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const reply = async (e: FormEvent) => {
    e.preventDefault();
    if (!selected) return;
    setBusy(true);
    setError("");
    try {
      const t = await api<Ticket>(`/api/support/tickets/${selected.id}/messages`, {
        method: "POST",
        body: JSON.stringify({ body }),
      });
      setSelected(t);
      setBody("");
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Ошибка");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="stack">
      <div className="panel">
        <h2>Техподдержка</h2>
        <p className="muted">Все обращения команд в одном месте.</p>
      </div>
      {error && <div className="alert error">{error}</div>}
      <div className="grid-2">
        <div className="panel">
          {tickets.map((t) => (
            <button
              key={t.id}
              type="button"
              className="dropdown-item"
              style={{ marginBottom: 6 }}
              onClick={() => setSelected(t)}
            >
              <div className="row" style={{ justifyContent: "space-between" }}>
                <strong>{t.team_name}</strong>
                <span className={`badge ${t.status === "open" ? "warn" : "green"}`}>{t.status}</span>
              </div>
              <div className="muted" style={{ fontSize: "0.85rem" }}>
                {new Date(t.updated_at).toLocaleString("ru-RU")} · сообщений: {t.messages.length}
              </div>
            </button>
          ))}
          {tickets.length === 0 && <p className="muted">Обращений пока нет</p>}
        </div>
        <div className="panel">
          {!selected && <p className="muted">Выберите тикет</p>}
          {selected && (
            <>
              <h3>{selected.team_name}</h3>
              <div className="chat">
                {selected.messages.map((m) => (
                  <div
                    key={m.id}
                    className={`bubble ${m.author_id === user?.id ? "mine" : ""} ${m.author_role === "admin" ? "admin" : ""}`}
                  >
                    <div className="meta">
                      @{m.author_username} · {new Date(m.created_at).toLocaleString("ru-RU")}
                    </div>
                    <div>{m.body}</div>
                  </div>
                ))}
              </div>
              <form onSubmit={reply} style={{ marginTop: "1rem" }}>
                <div className="field">
                  <label>Ответ</label>
                  <textarea rows={3} value={body} onChange={(e) => setBody(e.target.value)} required />
                </div>
                <button className="btn btn-primary" type="submit" disabled={busy}>
                  Ответить
                </button>
              </form>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

"use client";

import { useEffect, useState } from "react";
import { Markdown } from "@/components/Markdown";
import { RequireAuth } from "@/components/RequireAuth";
import { api, ApiError, downloadAuth } from "@/lib/api";
import type { EventContent } from "@/lib/types";

export default function ChallengePage() {
  return (
    <RequireAuth>
      <ChallengeInner />
    </RequireAuth>
  );
}

function ChallengeInner() {
  const [event, setEvent] = useState<EventContent | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    void api<EventContent>("/api/event").then(setEvent).catch((e) => setError(e.message));
  }, []);

  const download = async () => {
    if (!event?.has_source) return;
    setBusy(true);
    setError("");
    try {
      await downloadAuth("/api/event/source/download", event.source_filename || "source.zip");
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Не удалось скачать");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="stack">
      <div className="panel">
        <div className="row" style={{ justifyContent: "space-between" }}>
          <div>
            <h2 style={{ marginBottom: 4 }}>Задание</h2>
            <p className="muted" style={{ margin: 0 }}>
              Одно задание на всё мероприятие. Отчёт сдаётся от команды.
            </p>
          </div>
          <button className="btn btn-primary" type="button" disabled={!event?.has_source || busy} onClick={download}>
            {event?.has_source ? (busy ? "Скачивание…" : "Скачать исходники (ZIP)") : "Исходники скоро"}
          </button>
        </div>
      </div>
      {error && <div className="alert error">{error}</div>}
      <div className="panel">{event ? <Markdown>{event.challenge_md}</Markdown> : <p className="muted">Загрузка…</p>}</div>
      {event && event.rubric.length > 0 && (
        <div className="panel">
          <h3>Критерии оценки (0–100)</h3>
          <table className="table">
            <thead>
              <tr>
                <th>Критерий</th>
                <th>Макс.</th>
                <th>Описание</th>
              </tr>
            </thead>
            <tbody>
              {event.rubric.map((r) => (
                <tr key={r.id}>
                  <td>{r.title}</td>
                  <td>{r.max_points}</td>
                  <td className="muted">{r.description}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { Countdown } from "@/components/Countdown";
import { RequireAuth } from "@/components/RequireAuth";
import { api, ApiError } from "@/lib/api";
import type { EventContent, RubricItem } from "@/lib/types";

function newItem(): RubricItem {
  return {
    id: `c_${Math.random().toString(36).slice(2, 8)}`,
    title: "",
    max_points: 0,
    description: "",
  };
}

function toLocalInput(iso: string | null | undefined): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

export default function AdminContentPage() {
  return (
    <RequireAuth admin>
      <ContentInner />
    </RequireAuth>
  );
}

function ContentInner() {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [challenge, setChallenge] = useState("");
  const [rubric, setRubric] = useState<RubricItem[]>([]);
  const [endsAtLocal, setEndsAtLocal] = useState("");
  const [eventMeta, setEventMeta] = useState<Pick<EventContent, "ends_at" | "seconds_left" | "is_finished"> | null>(null);
  const [sourceName, setSourceName] = useState<string | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState("");
  const [ok, setOk] = useState("");
  const [busy, setBusy] = useState(false);

  const total = useMemo(() => rubric.reduce((s, r) => s + Number(r.max_points || 0), 0), [rubric]);

  useEffect(() => {
    void api<EventContent>("/api/event").then((e) => {
      setTitle(e.title);
      setDescription(e.description_md);
      setChallenge(e.challenge_md);
      setRubric(e.rubric.length ? e.rubric : [newItem()]);
      setSourceName(e.source_filename);
      setEndsAtLocal(toLocalInput(e.ends_at));
      setEventMeta({ ends_at: e.ends_at, seconds_left: e.seconds_left, is_finished: e.is_finished });
    });
  }, []);

  const save = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError("");
    setOk("");
    try {
      const payload: Record<string, unknown> = {
        title,
        description_md: description,
        challenge_md: challenge,
        rubric,
      };
      if (endsAtLocal.trim()) {
        payload.ends_at = new Date(endsAtLocal).toISOString();
        payload.clear_ends_at = false;
      } else {
        payload.clear_ends_at = true;
        payload.ends_at = null;
      }
      const updated = await api<EventContent>("/api/event", {
        method: "PUT",
        body: JSON.stringify(payload),
      });
      setEndsAtLocal(toLocalInput(updated.ends_at));
      setEventMeta({
        ends_at: updated.ends_at,
        seconds_left: updated.seconds_left,
        is_finished: updated.is_finished,
      });
      setOk("Сохранено");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Ошибка сохранения");
    } finally {
      setBusy(false);
    }
  };

  const uploadZip = async () => {
    if (!file) return;
    setBusy(true);
    setError("");
    try {
      const fd = new FormData();
      fd.append("file", file);
      const e = await api<EventContent>("/api/event/source", { method: "POST", body: fd });
      setSourceName(e.source_filename);
      setFile(null);
      setOk("ZIP загружен");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Ошибка загрузки");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="stack">
      <div className="panel">
        <h2>Контент мероприятия</h2>
        <p className="muted">Markdown для описания и задания. Сумма критериев должна быть ровно 100.</p>
        <Countdown
          endsAt={eventMeta?.ends_at}
          secondsLeft={eventMeta?.seconds_left}
          isFinished={eventMeta?.is_finished}
        />
      </div>
      {error && <div className="alert error">{error}</div>}
      {ok && <div className="alert ok">{ok}</div>}

      <form className="panel stack" onSubmit={save}>
        <div className="field">
          <label>Название</label>
          <input value={title} onChange={(e) => setTitle(e.target.value)} required maxLength={256} />
        </div>
        <div className="field">
          <label>Окончание мероприятия</label>
          <input
            type="datetime-local"
            value={endsAtLocal}
            onChange={(e) => setEndsAtLocal(e.target.value)}
          />
          <span className="muted" style={{ fontSize: "0.85rem" }}>
            После этой даты регистрация и сдача отчётов закрываются. Оставьте пустым, чтобы снять ограничение.
          </span>
        </div>
        <div className="field">
          <label>Описание (Markdown)</label>
          <textarea rows={8} value={description} onChange={(e) => setDescription(e.target.value)} />
        </div>
        <div className="field">
          <label>Задание (Markdown)</label>
          <textarea rows={10} value={challenge} onChange={(e) => setChallenge(e.target.value)} />
        </div>

        <div>
          <div className="row" style={{ justifyContent: "space-between" }}>
            <h3 style={{ margin: 0 }}>Рубрика оценки</h3>
            <span className={total === 100 ? "badge green" : "badge warn"}>Сумма: {total}/100</span>
          </div>
          {rubric.map((item, idx) => (
            <div key={item.id} className="panel" style={{ marginTop: 12, boxShadow: "none" }}>
              <div className="grid-2">
                <div className="field">
                  <label>Название критерия</label>
                  <input
                    value={item.title}
                    onChange={(e) => {
                      const next = [...rubric];
                      next[idx] = { ...item, title: e.target.value };
                      setRubric(next);
                    }}
                    required
                  />
                </div>
                <div className="field">
                  <label>Макс. баллы</label>
                  <input
                    type="number"
                    min={0}
                    max={100}
                    step={0.5}
                    value={item.max_points}
                    onChange={(e) => {
                      const next = [...rubric];
                      next[idx] = { ...item, max_points: Number(e.target.value) };
                      setRubric(next);
                    }}
                    required
                  />
                </div>
              </div>
              <div className="field">
                <label>Описание</label>
                <input
                  value={item.description || ""}
                  onChange={(e) => {
                    const next = [...rubric];
                    next[idx] = { ...item, description: e.target.value };
                    setRubric(next);
                  }}
                />
              </div>
              <button
                className="btn btn-danger"
                type="button"
                onClick={() => setRubric(rubric.filter((_, i) => i !== idx))}
              >
                Удалить критерий
              </button>
            </div>
          ))}
          <button className="btn btn-secondary" type="button" style={{ marginTop: 12 }} onClick={() => setRubric([...rubric, newItem()])}>
            + Критерий
          </button>
        </div>

        <button className="btn btn-primary" type="submit" disabled={busy || total !== 100}>
          Сохранить контент
        </button>
      </form>

      <div className="panel">
        <h3>Исходники (один ZIP)</h3>
        <p className="muted">Сейчас: {sourceName || "не загружено"}</p>
        <div className="field">
          <label>ZIP-файл</label>
          <input type="file" accept=".zip,application/zip" onChange={(e) => setFile(e.target.files?.[0] || null)} />
        </div>
        <button className="btn btn-primary" type="button" disabled={!file || busy} onClick={() => void uploadZip()}>
          Загрузить ZIP
        </button>
      </div>
    </div>
  );
}

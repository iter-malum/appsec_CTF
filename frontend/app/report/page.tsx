"use client";

import { FormEvent, useEffect, useState } from "react";
import { RequireAuth } from "@/components/RequireAuth";
import { api, ApiError, downloadAuth } from "@/lib/api";
import type { Report } from "@/lib/types";

export default function ReportPage() {
  return (
    <RequireAuth>
      <ReportInner />
    </RequireAuth>
  );
}

function ReportInner() {
  const [report, setReport] = useState<Report | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [note, setNote] = useState("");
  const [error, setError] = useState("");
  const [ok, setOk] = useState("");
  const [busy, setBusy] = useState(false);

  const load = async () => {
    try {
      setReport(await api<Report | null>("/api/reports/mine"));
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Ошибка");
    }
  };

  useEffect(() => {
    void load();
  }, []);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (!file) {
      setError("Выберите файл отчёта");
      return;
    }
    setBusy(true);
    setError("");
    setOk("");
    try {
      const fd = new FormData();
      fd.append("file", file);
      if (note.trim()) fd.append("note", note.trim());
      const r = await api<Report>("/api/reports/submit", { method: "POST", body: fd });
      setReport(r);
      setFile(null);
      setOk(report ? "Отчёт обновлён (пересдача)" : "Отчёт сдан");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Не удалось сдать");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="stack">
      <div className="panel">
        <h2>Отчёт команды</h2>
        <p className="muted">Форматы: PDF, DOCX, TXT, MD. Можно пересдавать — после пересдачи оценка снова скрыта до публикации.</p>
      </div>
      {error && <div className="alert error">{error}</div>}
      {ok && <div className="alert ok">{ok}</div>}

      <div className="grid-2">
        <div className="panel">
          <h3>{report ? "Пересдать отчёт" : "Сдать отчёт"}</h3>
          <form onSubmit={submit}>
            <div className="field">
              <label>Файл</label>
              <input
                type="file"
                accept=".pdf,.docx,.txt,.md,application/pdf,text/plain,text/markdown"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
              />
            </div>
            <div className="field">
              <label>Комментарий к сдаче (необязательно)</label>
              <textarea rows={3} value={note} onChange={(e) => setNote(e.target.value)} />
            </div>
            <button className="btn btn-primary" type="submit" disabled={busy}>
              {busy ? "Отправка…" : report ? "Пересдать" : "Сдать"}
            </button>
          </form>
        </div>

        <div className="panel">
          <h3>Текущий статус</h3>
          {!report && <p className="muted">Отчёт ещё не сдан.</p>}
          {report && (
            <div className="stack">
              <div>
                <div className="muted">Файл</div>
                <div className="row">
                  <strong>{report.original_filename}</strong>
                  <button
                    className="btn btn-secondary"
                    type="button"
                    onClick={() => void downloadAuth(`/api/reports/${report.id}/download`, report.original_filename)}
                  >
                    Скачать
                  </button>
                </div>
              </div>
              <div>
                <div className="muted">Обновлён</div>
                <div>{new Date(report.updated_at).toLocaleString("ru-RU")}</div>
              </div>
              {report.note && (
                <div>
                  <div className="muted">Комментарий</div>
                  <div>{report.note}</div>
                </div>
              )}
              {report.is_published && report.can_view_score ? (
                <div>
                  <div className="muted">Оценка</div>
                  <div className="score-total">{report.total_score}/100</div>
                  {report.comment && <p style={{ marginTop: 8 }}>{report.comment}</p>}
                  {report.rubric_scores?.length > 0 && (
                    <table className="table">
                      <thead>
                        <tr>
                          <th>Критерий</th>
                          <th>Балл</th>
                        </tr>
                      </thead>
                      <tbody>
                        {report.rubric_scores.map((s) => (
                          <tr key={s.id}>
                            <td>{s.title}</td>
                            <td>
                              {s.score}/{s.max_points}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </div>
              ) : (
                <span className="badge warn">Оценка ещё не опубликована</span>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

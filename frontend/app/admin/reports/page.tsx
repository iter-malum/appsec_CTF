"use client";

import { useEffect, useMemo, useState } from "react";
import { RequireAuth } from "@/components/RequireAuth";
import { api, ApiError, downloadAuth } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Report, RubricItem, RubricScoreItem } from "@/lib/types";

export default function AdminReportsPage() {
  return (
    <RequireAuth admin>
      <ReportsInner />
    </RequireAuth>
  );
}

function ReportsInner() {
  const { user } = useAuth();
  const [reports, setReports] = useState<Report[]>([]);
  const [selected, setSelected] = useState<Report | null>(null);
  const [scores, setScores] = useState<RubricScoreItem[]>([]);
  const [comment, setComment] = useState("");
  const [error, setError] = useState("");
  const [ok, setOk] = useState("");
  const [busy, setBusy] = useState(false);

  const total = useMemo(() => scores.reduce((s, i) => s + Number(i.score || 0), 0), [scores]);

  const load = async () => {
    const list = await api<Report[]>("/api/reports");
    setReports(list);
  };

  useEffect(() => {
    void load().catch((e) => setError(e.message));
  }, []);

  const openReport = async (r: Report) => {
    setError("");
    setOk("");
    setSelected(r);
    setComment(r.comment || "");
    if (r.rubric_scores?.length) {
      setScores(r.rubric_scores);
      return;
    }
    const rubric = await api<RubricItem[]>("/api/reports/rubric/default");
    setScores(rubric.map((i) => ({ ...i, score: 0 })));
  };

  const claim = async () => {
    if (!selected) return;
    setBusy(true);
    try {
      const r = await api<Report>(`/api/reports/${selected.id}/claim`, { method: "POST" });
      setSelected(r);
      await load();
      setOk("Отчёт закреплён за вами");
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Ошибка");
    } finally {
      setBusy(false);
    }
  };

  const saveScore = async (publish: boolean) => {
    if (!selected) return;
    setBusy(true);
    setError("");
    setOk("");
    try {
      const r = await api<Report>(`/api/reports/${selected.id}/score`, {
        method: "PUT",
        body: JSON.stringify({ rubric_scores: scores, comment, publish }),
      });
      setSelected(r);
      await load();
      setOk(publish ? "Оценка сохранена и опубликована" : "Черновик оценки сохранён");
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Ошибка");
    } finally {
      setBusy(false);
    }
  };

  const publishOnly = async () => {
    if (!selected) return;
    setBusy(true);
    try {
      const r = await api<Report>(`/api/reports/${selected.id}/publish`, { method: "POST" });
      setSelected(r);
      await load();
      setOk("Оценка отправлена участникам");
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Ошибка");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="stack">
      <div className="panel">
        <h2>Отчёты</h2>
        <p className="muted">Один судья на отчёт. Автокалькулятор суммирует баллы по критериям.</p>
      </div>
      {error && <div className="alert error">{error}</div>}
      {ok && <div className="alert ok">{ok}</div>}

      <div className="grid-2">
        <div className="panel">
          <table className="table">
            <thead>
              <tr>
                <th>Команда</th>
                <th>Файл</th>
                <th>Судья</th>
                <th>Статус</th>
              </tr>
            </thead>
            <tbody>
              {reports.map((r) => (
                <tr key={r.id} style={{ cursor: "pointer" }} onClick={() => void openReport(r)}>
                  <td>{r.team_name}</td>
                  <td>{r.original_filename}</td>
                  <td>{r.judge_username ? `@${r.judge_username}` : "—"}</td>
                  <td>
                    {r.is_published ? (
                      <span className="badge green">{r.total_score}/100</span>
                    ) : r.total_score != null ? (
                      <span className="badge warn">черновик {r.total_score}</span>
                    ) : (
                      <span className="badge">новый</span>
                    )}
                  </td>
                </tr>
              ))}
              {reports.length === 0 && (
                <tr>
                  <td colSpan={4} className="muted">
                    Пока нет отчётов
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        <div className="panel">
          {!selected && <p className="muted">Выберите отчёт слева.</p>}
          {selected && (
            <div className="stack">
              <div>
                <h3 style={{ margin: 0 }}>{selected.team_name}</h3>
                <p className="muted" style={{ margin: "0.35rem 0" }}>
                  {selected.original_filename} · сдал @{selected.submitted_by}
                </p>
                <div className="row">
                  <button
                    className="btn btn-secondary"
                    type="button"
                    onClick={() => void downloadAuth(`/api/reports/${selected.id}/download`, selected.original_filename)}
                  >
                    Скачать файл
                  </button>
                  {(!selected.judge_id || selected.judge_id === user?.id) && (
                    <button className="btn btn-secondary" type="button" disabled={busy} onClick={() => void claim()}>
                      Закрепить за мной
                    </button>
                  )}
                </div>
              </div>

              {selected.note && (
                <div>
                  <div className="muted">Комментарий команды</div>
                  <div>{selected.note}</div>
                </div>
              )}

              <div className="row" style={{ justifyContent: "space-between" }}>
                <strong>Оценка</strong>
                <span className="score-total">{total.toFixed(1)}/100</span>
              </div>

              {scores.map((item, idx) => (
                <div key={item.id} className="field">
                  <label>
                    {item.title} (макс. {item.max_points})
                  </label>
                  <input
                    type="number"
                    min={0}
                    max={item.max_points}
                    step={0.5}
                    value={item.score}
                    disabled={!!selected.judge_id && selected.judge_id !== user?.id}
                    onChange={(e) => {
                      const next = [...scores];
                      next[idx] = { ...item, score: Number(e.target.value) };
                      setScores(next);
                    }}
                  />
                </div>
              ))}

              <div className="field">
                <label>Комментарий судьи</label>
                <textarea
                  rows={4}
                  value={comment}
                  disabled={!!selected.judge_id && selected.judge_id !== user?.id}
                  onChange={(e) => setComment(e.target.value)}
                />
              </div>

              <div className="row">
                <button
                  className="btn btn-secondary"
                  type="button"
                  disabled={busy || (!!selected.judge_id && selected.judge_id !== user?.id)}
                  onClick={() => void saveScore(false)}
                >
                  Сохранить черновик
                </button>
                <button
                  className="btn btn-primary"
                  type="button"
                  disabled={busy || (!!selected.judge_id && selected.judge_id !== user?.id)}
                  onClick={() => void saveScore(true)}
                >
                  Сохранить и опубликовать
                </button>
                {selected.total_score != null && !selected.is_published && (
                  <button className="btn btn-primary" type="button" disabled={busy} onClick={() => void publishOnly()}>
                    Отправить участникам
                  </button>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

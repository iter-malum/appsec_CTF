"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import { RequireAuth } from "@/components/RequireAuth";
import { api, ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Team, TeamInvite } from "@/lib/types";

export default function TeamPage() {
  return (
    <RequireAuth>
      <TeamInner />
    </RequireAuth>
  );
}

function TeamInner() {
  const { user, refresh } = useAuth();
  const [team, setTeam] = useState<Team | null>(null);
  const [invites, setInvites] = useState<TeamInvite[]>([]);
  const [name, setName] = useState("");
  const [inviteLogin, setInviteLogin] = useState("");
  const [error, setError] = useState("");
  const [ok, setOk] = useState("");
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [t, inv] = await Promise.all([
        api<Team | null>("/api/teams/mine"),
        api<TeamInvite[]>("/api/teams/invites/incoming"),
      ]);
      setTeam(t);
      setInvites(inv);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Ошибка загрузки");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const createTeam = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setOk("");
    try {
      const t = await api<Team>("/api/teams", { method: "POST", body: JSON.stringify({ name }) });
      setTeam(t);
      setOk("Команда создана");
      await refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Не удалось создать");
    }
  };

  const invite = async (e: FormEvent) => {
    e.preventDefault();
    if (!team) return;
    setError("");
    setOk("");
    try {
      await api(`/api/teams/${team.id}/invites`, {
        method: "POST",
        body: JSON.stringify({ username: inviteLogin }),
      });
      setInviteLogin("");
      setOk("Приглашение отправлено");
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Ошибка приглашения");
    }
  };

  const accept = async (id: number) => {
    try {
      await api(`/api/teams/invites/${id}/accept`, { method: "POST" });
      await refresh();
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Ошибка");
    }
  };

  const decline = async (id: number) => {
    await api(`/api/teams/invites/${id}/decline`, { method: "POST" });
    await load();
  };

  const leave = async () => {
    setError("");
    try {
      await api("/api/teams/leave", { method: "POST" });
      await refresh();
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Нельзя выйти");
    }
  };

  const removeMember = async (memberId: number, username: string) => {
    if (!team) return;
    if (!window.confirm(`Исключить @${username} из команды?`)) return;
    setError("");
    setOk("");
    try {
      const t = await api<Team>(`/api/teams/${team.id}/members/${memberId}/remove`, {
        method: "POST",
      });
      setTeam(t);
      setOk(`Участник @${username} исключён`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Не удалось исключить");
    }
  };

  if (loading) return <div className="panel muted">Загрузка…</div>;

  return (
    <div className="stack">
      <div className="panel">
        <h2>Команда</h2>
        <p className="muted">Максимум 10 участников. Один человек — одна команда. Приглашение по логину.</p>
      </div>
      {error && <div className="alert error">{error}</div>}
      {ok && <div className="alert ok">{ok}</div>}

      {invites.length > 0 && (
        <div className="panel">
          <h3>Входящие приглашения</h3>
          {invites.map((i) => (
            <div key={i.id} className="row" style={{ justifyContent: "space-between", marginBottom: 8 }}>
              <div>
                <strong>{i.team_name}</strong>
                <div className="muted">от @{i.inviter_username}</div>
              </div>
              <div className="row">
                <button className="btn btn-primary" type="button" onClick={() => void accept(i.id)}>
                  Принять
                </button>
                <button className="btn btn-secondary" type="button" onClick={() => void decline(i.id)}>
                  Отклонить
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {!team && (
        <div className="panel">
          <h3>Создать команду</h3>
          <form onSubmit={createTeam}>
            <div className="field">
              <label>Название</label>
              <input value={name} onChange={(e) => setName(e.target.value)} minLength={2} required />
            </div>
            <button className="btn btn-primary" type="submit">
              Создать
            </button>
          </form>
        </div>
      )}

      {team && (
        <div className="grid-2">
          <div className="panel">
            <div className="row" style={{ justifyContent: "space-between" }}>
              <h3 style={{ margin: 0 }}>{team.name}</h3>
              <span className="badge blue">{team.members.length}/10</span>
            </div>
            <table className="table">
              <thead>
                <tr>
                  <th>Участник</th>
                  <th>Роль</th>
                  {user?.id === team.owner_id && <th />}
                </tr>
              </thead>
              <tbody>
                {team.members.map((m) => (
                  <tr key={m.id}>
                    <td>
                      {m.display_name} <span className="muted">@{m.username}</span>
                    </td>
                    <td>{m.is_owner ? <span className="badge green">владелец</span> : "участник"}</td>
                    {user?.id === team.owner_id && (
                      <td style={{ textAlign: "right" }}>
                        {!m.is_owner && (
                          <button
                            className="btn btn-warn"
                            type="button"
                            onClick={() => void removeMember(m.id, m.username)}
                          >
                            Исключить
                          </button>
                        )}
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
            <button className="btn btn-danger" type="button" onClick={() => void leave()}>
              {user?.id === team.owner_id && team.members.length === 1 ? "Удалить команду" : "Покинуть команду"}
            </button>
          </div>

          <div className="panel">
            <h3>Пригласить по логину</h3>
            <form onSubmit={invite}>
              <div className="field">
                <label>Логин участника</label>
                <input value={inviteLogin} onChange={(e) => setInviteLogin(e.target.value)} required />
              </div>
              <button className="btn btn-primary" type="submit">
                Отправить приглашение
              </button>
            </form>
            {team.pending_invites.length > 0 && (
              <>
                <h3 style={{ marginTop: "1.25rem" }}>Ожидают ответа</h3>
                <ul className="muted">
                  {team.pending_invites.map((i) => (
                    <li key={i.id}>@{i.invitee_username}</li>
                  ))}
                </ul>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

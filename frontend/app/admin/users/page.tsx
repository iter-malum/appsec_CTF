"use client";

import { FormEvent, useEffect, useState } from "react";
import { RequireAuth } from "@/components/RequireAuth";
import { api, ApiError } from "@/lib/api";
import type { User } from "@/lib/types";

export default function AdminUsersPage() {
  return (
    <RequireAuth admin>
      <UsersInner />
    </RequireAuth>
  );
}

function UsersInner() {
  const [users, setUsers] = useState<User[]>([]);
  const [username, setUsername] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<"admin" | "participant">("admin");
  const [error, setError] = useState("");
  const [ok, setOk] = useState("");

  const load = async () => setUsers(await api<User[]>("/api/admin/users"));

  useEffect(() => {
    void load().catch((e) => setError(e.message));
  }, []);

  const create = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setOk("");
    try {
      await api("/api/admin/users", {
        method: "POST",
        body: JSON.stringify({
          username,
          password,
          display_name: displayName,
          role,
        }),
      });
      setUsername("");
      setDisplayName("");
      setPassword("");
      setOk("Пользователь создан");
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Ошибка");
    }
  };

  const toggle = async (id: number) => {
    await api(`/api/admin/users/${id}/toggle-active`, { method: "POST" });
    await load();
  };

  return (
    <div className="stack">
      <div className="panel">
        <h2>Пользователи</h2>
        <p className="muted">Админ-аккаунты (судьи) создаются здесь. Участники могут регистрироваться сами.</p>
      </div>
      {error && <div className="alert error">{error}</div>}
      {ok && <div className="alert ok">{ok}</div>}

      <div className="grid-2">
        <form className="panel" onSubmit={create}>
          <h3>Создать аккаунт</h3>
          <div className="field">
            <label>Имя</label>
            <input value={displayName} onChange={(e) => setDisplayName(e.target.value)} required />
          </div>
          <div className="field">
            <label>Логин</label>
            <input value={username} onChange={(e) => setUsername(e.target.value)} required />
          </div>
          <div className="field">
            <label>Пароль</label>
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} minLength={6} required />
          </div>
          <div className="field">
            <label>Роль</label>
            <select value={role} onChange={(e) => setRole(e.target.value as "admin" | "participant")}>
              <option value="admin">Администратор / судья</option>
              <option value="participant">Участник</option>
            </select>
          </div>
          <button className="btn btn-primary" type="submit">
            Создать
          </button>
        </form>

        <div className="panel">
          <table className="table">
            <thead>
              <tr>
                <th>Логин</th>
                <th>Роль</th>
                <th>Статус</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id}>
                  <td>
                    {u.display_name}
                    <div className="muted">@{u.username}</div>
                  </td>
                  <td>
                    <span className={`badge ${u.role === "admin" ? "blue" : "green"}`}>{u.role}</span>
                  </td>
                  <td>{u.is_active ? "активен" : "отключён"}</td>
                  <td>
                    <button className="btn btn-secondary" type="button" onClick={() => void toggle(u.id)}>
                      {u.is_active ? "Отключить" : "Включить"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

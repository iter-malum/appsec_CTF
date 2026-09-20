"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { ApiError, login } from "@/lib/api";
import { useAuth } from "@/lib/auth";

export default function LoginPage() {
  const { setSession } = useAuth();
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const { access_token } = await login(username, password);
      await setSession(access_token);
      router.push("/challenge");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Ошибка входа");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 440, margin: "2rem auto" }}>
      <div className="panel">
        <h2>Вход</h2>
        <p className="muted">Войдите, чтобы работать с командой и отчётом.</p>
        {error && <div className="alert error">{error}</div>}
        <form onSubmit={onSubmit}>
          <div className="field">
            <label>Логин</label>
            <input value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" required />
          </div>
          <div className="field">
            <label>Пароль</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              required
            />
          </div>
          <button className="btn btn-primary" type="submit" disabled={loading} style={{ width: "100%" }}>
            {loading ? "Входим…" : "Войти"}
          </button>
        </form>
        <p className="muted" style={{ marginTop: "1rem" }}>
          Нет аккаунта? <Link href="/register">Регистрация</Link>
        </p>
      </div>
    </div>
  );
}

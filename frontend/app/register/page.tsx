"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { api, ApiError, login } from "@/lib/api";
import { useAuth } from "@/lib/auth";

export default function RegisterPage() {
  const { setSession } = useAuth();
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [password, setPassword] = useState("");
  const [university, setUniversity] = useState("");
  const [course, setCourse] = useState("");
  const [studyProgram, setStudyProgram] = useState("");
  const [contactExtra, setContactExtra] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await api(
        "/api/auth/register",
        {
          method: "POST",
          body: JSON.stringify({
            username,
            password,
            display_name: displayName,
            university,
            course,
            study_program: studyProgram,
            contact_extra: contactExtra,
          }),
        },
        false
      );
      const { access_token } = await login(username, password);
      await setSession(access_token);
      router.push("/team");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Ошибка регистрации");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 560, margin: "2rem auto" }}>
      <div className="panel">
        <h2>Регистрация</h2>
        <p className="muted">Создайте участника. Админ-аккаунты выдаёт организатор.</p>
        {error && <div className="alert error">{error}</div>}
        <form onSubmit={onSubmit}>
          <div className="field">
            <label>Отображаемое имя</label>
            <input value={displayName} onChange={(e) => setDisplayName(e.target.value)} required maxLength={128} />
          </div>
          <div className="field">
            <label>Логин</label>
            <input value={username} onChange={(e) => setUsername(e.target.value)} required minLength={3} maxLength={64} />
          </div>
          <div className="field">
            <label>Пароль (мин. 8 символов)</label>
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} minLength={8} maxLength={128} required />
          </div>
          <div className="field">
            <label>Наименование ВУЗа</label>
            <input value={university} onChange={(e) => setUniversity(e.target.value)} required minLength={2} maxLength={256} placeholder="например, УрФУ" />
          </div>
          <div className="field">
            <label>Курс</label>
            <input value={course} onChange={(e) => setCourse(e.target.value)} required maxLength={64} placeholder="например, 3" />
          </div>
          <div className="field">
            <label>Направление подготовки</label>
            <input
              value={studyProgram}
              onChange={(e) => setStudyProgram(e.target.value)}
              required
              minLength={2}
              maxLength={256}
              placeholder="например, 09.03.01 Информатика и вычислительная техника"
            />
          </div>
          <div className="field">
            <label>Доп. способ связи (телефон или Telegram)</label>
            <input
              value={contactExtra}
              onChange={(e) => setContactExtra(e.target.value)}
              required
              minLength={3}
              maxLength={256}
              placeholder="+7… или @username"
            />
          </div>
          <button className="btn btn-primary" type="submit" disabled={loading} style={{ width: "100%" }}>
            {loading ? "Создаём…" : "Зарегистрироваться"}
          </button>
        </form>
        <p className="muted" style={{ marginTop: "1rem" }}>
          Уже есть аккаунт? <Link href="/login">Войти</Link>
        </p>
      </div>
    </div>
  );
}

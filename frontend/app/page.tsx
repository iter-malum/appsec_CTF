"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Markdown } from "@/components/Markdown";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { EventContent } from "@/lib/types";

export default function HomePage() {
  const { user } = useAuth();
  const [event, setEvent] = useState<EventContent | null>(null);

  useEffect(() => {
    void api<EventContent>("/api/event", {}, false).then(setEvent).catch(() => setEvent(null));
  }, []);

  return (
    <div className="stack">
      <section className="hero">
        <div className="row">
          <span className="partner-chip urfu">УрФУ</span>
          <span className="partner-chip ussc">УЦСБ</span>
        </div>
        <h1>{event?.title || "AppSec CTF"}</h1>
        <p>
          Высокотехнологичная платформа командного соревнования по безопасности приложений.
          Соберите команду, разберите учебное приложение и сдайте отчёт судьям.
        </p>
        <div className="hero-actions">
          {user ? (
            <>
              <Link className="btn btn-primary" href="/challenge">
                К заданию
              </Link>
              <Link className="btn btn-secondary" href="/team">
                Моя команда
              </Link>
            </>
          ) : (
            <>
              <Link className="btn btn-primary" href="/register">
                Участвовать
              </Link>
              <Link className="btn btn-secondary" href="/login">
                Войти
              </Link>
            </>
          )}
        </div>
      </section>

      <div className="grid-2">
        <article className="panel">
          <h2>О мероприятии</h2>
          {event ? <Markdown>{event.description_md}</Markdown> : <p className="muted">Загрузка…</p>}
        </article>
        <aside className="stack">
          <div className="panel">
            <h3>Как проходит</h3>
            <ol className="muted" style={{ margin: 0, paddingLeft: "1.1rem", lineHeight: 1.7 }}>
              <li>Регистрация и создание команды (до 10 человек)</li>
              <li>Скачивание исходников и анализ</li>
              <li>Сдача отчёта PDF / DOCX / TXT / MD</li>
              <li>Оценка по критериям 0–100 и публикация результата</li>
            </ol>
          </div>
          <div className="panel">
            <h3>Партнёры</h3>
            <p className="muted" style={{ margin: 0 }}>
              Совместная инициатива Уральского федерального университета и УЦСБ — связка академической
              экспертизы и индустрии информационной безопасности.
            </p>
          </div>
        </aside>
      </div>
    </div>
  );
}

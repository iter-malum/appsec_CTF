"use client";

import Link from "next/link";
import { RequireAuth } from "@/components/RequireAuth";

const cards = [
  { href: "/admin/content", title: "Контент и исходники", desc: "Описание, задание, ZIP, рубрика" },
  { href: "/admin/reports", title: "Отчёты и оценка", desc: "Закрепление судьи, автокалькулятор, публикация" },
  { href: "/admin/support", title: "Техподдержка", desc: "Ответы на обращения команд" },
  { href: "/admin/users", title: "Пользователи", desc: "Создание админов/участников" },
];

export default function AdminHome() {
  return (
    <RequireAuth admin>
      <div className="stack">
        <div className="panel">
          <h2>Админ-панель</h2>
          <p className="muted">Управление мероприятием AppSec CTF. Судьи работают как администраторы.</p>
        </div>
        <div className="grid-2">
          {cards.map((c) => (
            <Link key={c.href} href={c.href} className="panel" style={{ color: "inherit" }}>
              <h3>{c.title}</h3>
              <p className="muted" style={{ margin: 0 }}>
                {c.desc}
              </p>
            </Link>
          ))}
        </div>
      </div>
    </RequireAuth>
  );
}

"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { NotificationItem } from "@/lib/types";

const links = [
  { href: "/", label: "Главная" },
  { href: "/challenge", label: "Задание", auth: true },
  { href: "/team", label: "Команда", auth: true },
  { href: "/report", label: "Отчёт", auth: true },
  { href: "/support", label: "Поддержка", auth: true },
];

export function AppHeader() {
  const { user, loading, logout } = useAuth();
  const pathname = usePathname();
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState<NotificationItem[]>([]);
  const [unread, setUnread] = useState(0);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!user) return;
    let alive = true;
    const load = async () => {
      try {
        const [list, count] = await Promise.all([
          api<NotificationItem[]>("/api/notifications"),
          api<{ count: number }>("/api/notifications/unread-count"),
        ]);
        if (!alive) return;
        setItems(list);
        setUnread(count.count);
      } catch {
        /* ignore */
      }
    };
    void load();
    const id = setInterval(load, 15000);
    return () => {
      alive = false;
      clearInterval(id);
    };
  }, [user]);

  useEffect(() => {
    const onDoc = (e: MouseEvent) => {
      if (!ref.current?.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, []);

  const markAll = async () => {
    await api("/api/notifications/read-all", { method: "POST" });
    setUnread(0);
    setItems((prev) => prev.map((n) => ({ ...n, is_read: true })));
  };

  const openNotif = async (n: NotificationItem) => {
    if (!n.is_read) {
      await api(`/api/notifications/${n.id}/read`, { method: "POST" });
      setUnread((c) => Math.max(0, c - 1));
      setItems((prev) => prev.map((x) => (x.id === n.id ? { ...x, is_read: true } : x)));
    }
    setOpen(false);
    if (n.link) router.push(n.link);
  };

  return (
    <header className="nav">
      <div className="container nav-inner">
        <Link href="/" className="brand">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src="/brand/appsec-ctf-iso.png" alt="" className="brand-iso" />
          <div className="brand-text">
            <strong>AppSec CTF</strong>
            <span>УрФУ × УЦСБ</span>
          </div>
        </Link>

        <div className="partners" aria-label="Организаторы">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src="/brand/urfu-iso.png" alt="УрФУ" className="nav-iso" title="УрФУ" />
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src="/brand/ussc-iso.png" alt="УЦСБ" className="nav-iso" title="УЦСБ" />
        </div>

        <nav className="nav-links">
          {links
            .filter((l) => !l.auth || !!user)
            .map((l) => (
              <Link key={l.href} href={l.href} className={pathname === l.href ? "active" : ""}>
                {l.label}
              </Link>
            ))}
          {user?.role === "admin" && (
            <Link href="/admin" className={pathname.startsWith("/admin") ? "active" : ""}>
              Админ
            </Link>
          )}

          {!loading && !user && (
            <>
              <Link href="/login">Вход</Link>
              <Link href="/register">Регистрация</Link>
            </>
          )}

          {user && (
            <>
              <div style={{ position: "relative" }} ref={ref}>
                <button
                  className="linkish notif-btn"
                  type="button"
                  aria-label="Уведомления"
                  onClick={() => setOpen((v) => !v)}
                >
                  Увед.
                  {unread > 0 && <span className="notif-dot">{unread}</span>}
                </button>
                {open && (
                  <div className="dropdown">
                    <div className="row" style={{ justifyContent: "space-between", padding: "0.4rem 0.5rem" }}>
                      <strong>Уведомления</strong>
                      <button className="btn btn-secondary" style={{ padding: "0.3rem 0.6rem" }} type="button" onClick={markAll}>
                        Прочитать все
                      </button>
                    </div>
                    {items.length === 0 && <div className="muted" style={{ padding: "0.8rem" }}>Пока пусто</div>}
                    {items.slice(0, 8).map((n) => (
                      <button
                        key={n.id}
                        type="button"
                        className={`dropdown-item ${n.is_read ? "" : "unread"}`}
                        onClick={() => void openNotif(n)}
                      >
                        <div style={{ fontWeight: 600 }}>{n.title}</div>
                        <div className="muted" style={{ fontSize: "0.85rem" }}>{n.body}</div>
                      </button>
                    ))}
                  </div>
                )}
              </div>
              <span className="muted" style={{ fontSize: "0.85rem" }}>@{user.username}</span>
              <button className="linkish" type="button" onClick={logout}>
                Выйти
              </button>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}

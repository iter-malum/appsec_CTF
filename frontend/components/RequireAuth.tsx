"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { useAuth } from "@/lib/auth";

export function RequireAuth({
  children,
  admin,
}: {
  children: React.ReactNode;
  admin?: boolean;
}) {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (loading) return;
    if (!user) router.replace("/login");
    else if (admin && user.role !== "admin") router.replace("/");
  }, [user, loading, admin, router]);

  if (loading || !user || (admin && user.role !== "admin")) {
    return <div className="panel muted">Загрузка…</div>;
  }

  return <>{children}</>;
}

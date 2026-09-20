import type { Metadata } from "next";
import { AuthProvider } from "@/lib/auth";
import { AppHeader } from "@/components/AppHeader";
import "./globals.css";

export const metadata: Metadata = {
  title: "AppSec CTF — УрФУ × УЦСБ",
  description: "Соревнование по безопасности приложений",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru">
      <body>
        <AuthProvider>
          <div className="app-shell">
            <AppHeader />
            <main className="main">
              <div className="container">{children}</div>
            </main>
          </div>
        </AuthProvider>
      </body>
    </html>
  );
}

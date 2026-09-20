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
            <footer className="footer">
              <div className="container row" style={{ justifyContent: "space-between" }}>
                <div className="row">
                  <div className="footer-logos">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src="/brand/urfu-dark.png" alt="УрФУ" />
                    <span className="ussc-wrap">
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img src="/brand/ussc-wordmark.png" alt="УЦСБ" />
                    </span>
                  </div>
                  <span>AppSec CTF · совместное мероприятие</span>
                </div>
                <span>HTTPS · Docker · Secure by design</span>
              </div>
            </footer>
          </div>
        </AuthProvider>
      </body>
    </html>
  );
}

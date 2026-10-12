import type { Metadata } from "next";
import { Inter, IBM_Plex_Mono } from "next/font/google";
import { AuthProvider } from "@/lib/auth";
import { AppHeader } from "@/components/AppHeader";
import "./globals.css";

const inter = Inter({
  subsets: ["latin", "cyrillic"],
  variable: "--font-inter",
  display: "swap",
});

const plexMono = IBM_Plex_Mono({
  subsets: ["latin", "cyrillic"],
  weight: ["400", "500", "600"],
  variable: "--font-plex-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "AppSec CTF — УрФУ × УЦСБ",
  description: "Соревнование по безопасности приложений",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru" className={`${inter.variable} ${plexMono.variable}`}>
      <body style={{ fontFamily: "var(--font-inter), Inter, system-ui, sans-serif" }}>
        <style>{`:root{--font:var(--font-inter),Inter,system-ui,sans-serif;--mono:var(--font-plex-mono),"IBM Plex Mono",ui-monospace,monospace}`}</style>
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

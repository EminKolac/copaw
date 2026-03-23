import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CoPaw — AI Recipe Assistant",
  description: "Browse Cookidoo recipes and discover meals with ingredients you have",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="tr">
      <body className="min-h-screen">
        <nav className="sticky top-0 z-50 border-b border-[var(--border)] bg-[var(--bg-primary)]/95 backdrop-blur-sm">
          <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3">
            <a href="/" className="flex items-center gap-2 text-xl font-bold">
              <span className="text-2xl">🐾</span>
              <span className="gradient-text">CoPaw</span>
            </a>
            <div className="flex items-center gap-6">
              <a href="/recipes" className="text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors">
                Tarifler
              </a>
              <a
                href="/chat"
                className="rounded-full bg-[var(--accent)] px-4 py-2 text-sm font-medium text-white hover:bg-[var(--accent-hover)] transition-colors"
              >
                Ne Pişirsem?
              </a>
            </div>
          </div>
        </nav>
        <main>{children}</main>
      </body>
    </html>
  );
}

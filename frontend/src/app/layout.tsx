import type { Metadata } from "next";
import { Geist_Mono, JetBrains_Mono } from "next/font/google";

import { AppShell } from "@/components/layout/app-shell";
import { QueryProvider } from "@/components/providers/query-provider";
import { ThemeProvider } from "@/components/theme-provider";

import "./globals.css";

const geistMono = Geist_Mono({
  variable: "--font-sans",
  subsets: ["latin"],
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "EventForge",
  description: "Event-driven multi-agent research platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      suppressHydrationWarning
      className={`${geistMono.variable} ${jetbrainsMono.variable} h-full antialiased`}
    >
      <body className="min-h-full">
        <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
          <QueryProvider>
            <AppShell>{children}</AppShell>
          </QueryProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}

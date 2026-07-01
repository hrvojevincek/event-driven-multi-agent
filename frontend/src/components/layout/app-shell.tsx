"use client";

import { useEffect, useState } from "react";

import { SiteHeader } from "@/components/layout/site-header";
import { SiteSidebar } from "@/components/layout/site-sidebar";
import { cn } from "@/lib/utils";

export function AppShell({ children }: { children: React.ReactNode }) {
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  useEffect(() => {
    if (!mobileNavOpen) return;

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setMobileNavOpen(false);
    };

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [mobileNavOpen]);

  return (
    <div className="flex min-h-full">
      <SiteSidebar className="hidden md:flex" />

      {mobileNavOpen ? (
        <button
          type="button"
          aria-label="Close navigation"
          className="fixed inset-0 z-40 bg-background/80 backdrop-blur-sm md:hidden"
          onClick={() => setMobileNavOpen(false)}
        />
      ) : null}

      <SiteSidebar
        className={cn(
          "fixed inset-y-0 left-0 z-50 shadow-xl transition-transform md:hidden",
          mobileNavOpen ? "translate-x-0" : "-translate-x-full",
        )}
        onNavigate={() => setMobileNavOpen(false)}
      />

      <div className="flex min-w-0 flex-1 flex-col">
        <SiteHeader onMenuClick={() => setMobileNavOpen(true)} />
        <main className="flex flex-1 flex-col">{children}</main>
      </div>
    </div>
  );
}

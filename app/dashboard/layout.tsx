"use client";

import type { ReactNode } from "react";
import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { Activity, BarChart3, Bot, BriefcaseBusiness, History, LogOut, Settings } from "lucide-react";
import { clearSession, getToken } from "@/lib/api";
import { cn } from "@/lib/utils";

const nav = [
  { href: "/dashboard", label: "Overview", icon: BarChart3 },
  { href: "/dashboard/bot", label: "Paper Engine", icon: Bot },
  { href: "/dashboard/positions", label: "Positions", icon: BriefcaseBusiness },
  { href: "/dashboard/history", label: "Trade History", icon: History },
  { href: "/dashboard/settings", label: "Account", icon: Settings }
];

export default function DashboardLayout({ children }: { children: ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!getToken()) router.replace("/");
    else setReady(true);
  }, [router]);

  function logout() {
    clearSession();
    router.replace("/");
  }

  if (!ready) return <div className="flex min-h-screen items-center justify-center text-sm text-muted-foreground">Loading session...</div>;

  return (
    <div className="min-h-screen bg-background">
      <aside className="fixed inset-y-0 left-0 hidden w-64 border-r border-white/10 bg-card/70 p-4 backdrop-blur-xl lg:block">
        <Link href="/dashboard/bot" className="mb-8 flex items-center gap-2 font-semibold">
          <span className="flex h-8 w-8 items-center justify-center rounded-md bg-primary text-background"><Bot size={18} /></span>
          TradePilot AI
        </Link>
        <nav className="space-y-1">
          {nav.map((item) => (
            <Link key={item.href} href={item.href} className={cn("flex items-center gap-3 rounded-md px-3 py-2 text-sm transition", pathname === item.href ? "bg-white/[0.08] text-foreground" : "text-muted-foreground hover:bg-white/[0.05] hover:text-foreground")}>
              <item.icon size={17} />{item.label}
            </Link>
          ))}
        </nav>
        <div className="absolute bottom-4 left-4 right-4 space-y-3">
          <div className="rounded-lg border border-primary/20 bg-primary/10 p-4">
            <div className="flex items-center gap-2 text-sm font-medium text-primary"><Activity size={16} /> Paper Mode</div>
            <p className="mt-2 text-xs text-muted-foreground">Mock market data. No real orders.</p>
          </div>
          <button onClick={logout} className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm text-muted-foreground hover:bg-white/[0.06] hover:text-foreground"><LogOut size={16} /> Sign out</button>
        </div>
      </aside>
      <div className="lg:pl-64">
        <header className="sticky top-0 z-20 border-b border-white/10 bg-background/[0.88] px-5 py-4 backdrop-blur-xl">
          <div className="mx-auto flex max-w-7xl items-center justify-between gap-4">
            <Link href="/dashboard/bot" className="flex items-center gap-2 font-semibold lg:hidden"><Bot size={18} /> TradePilot AI</Link>
            <div className="hidden text-sm text-muted-foreground lg:block">Paper trading development environment</div>
            <div className="flex items-center gap-3 text-sm">
              <span className="rounded-full border border-primary/20 bg-primary/10 px-3 py-1 text-primary">Simulation Active</span>
              <button onClick={logout} className="lg:hidden"><LogOut size={17} /></button>
            </div>
          </div>
          <nav className="mt-4 flex gap-2 overflow-x-auto pb-1 lg:hidden">
            {nav.map((item) => <Link key={item.href} href={item.href} className={cn("flex shrink-0 items-center gap-2 rounded-md border px-3 py-2 text-xs", pathname === item.href ? "border-primary/30 bg-primary/10 text-primary" : "border-white/10 bg-white/[0.04] text-muted-foreground")}><item.icon size={14} />{item.label}</Link>)}
          </nav>
        </header>
        <main className="mx-auto max-w-7xl px-5 py-8">{children}</main>
      </div>
    </div>
  );
}

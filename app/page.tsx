"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Activity, Bot, BrainCircuit, LockKeyhole, ShieldCheck } from "lucide-react";
import { api, getToken, setSession } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

type AuthResponse = { data: { access_token: string; user: unknown } };

export default function AuthPage() {
  const router = useRouter();
  const [mode, setMode] = useState<"register" | "login">("register");
  const [username, setUsername] = useState("ilyanozary");
  const [password, setPassword] = useState("ilyalm10");
  const [fullName, setFullName] = useState("Ilya Nozary");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (getToken()) router.replace("/dashboard/bot");
  }, [router]);

  async function authenticate(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      let response: AuthResponse;
      if (mode === "register") {
        try {
          response = await api<AuthResponse>("/api/auth/register", {
            method: "POST",
            body: JSON.stringify({ username, password, full_name: fullName })
          });
        } catch (registerError) {
          if (!(registerError instanceof Error) || !registerError.message.includes("already registered")) throw registerError;
          response = await api<AuthResponse>("/api/auth/login", {
            method: "POST",
            body: JSON.stringify({ username, password })
          });
        }
      } else {
        response = await api<AuthResponse>("/api/auth/login", {
          method: "POST",
          body: JSON.stringify({ username, password })
        });
      }
      setSession(response.data.access_token, response.data.user);
      router.push("/dashboard/bot");
    } catch (authError) {
      setError(authError instanceof Error ? authError.message : "Authentication failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="grid min-h-screen lg:grid-cols-[1.1fr_0.9fr]">
      <section className="relative hidden overflow-hidden border-r border-white/10 p-12 lg:flex lg:flex-col lg:justify-between">
        <div className="absolute inset-0 chart-grid opacity-25" />
        <div className="relative flex items-center gap-3 text-lg font-semibold">
          <span className="flex h-10 w-10 items-center justify-center rounded-md bg-primary text-background"><Bot size={21} /></span>
          TradePilot AI
        </div>
        <div className="relative max-w-2xl">
          <Badge className="border-primary/30 bg-primary/10 text-primary">Development Paper Trading</Badge>
          <h1 className="mt-6 text-5xl font-semibold leading-tight">See every decision before a virtual order opens.</h1>
          <p className="mt-5 max-w-xl text-lg leading-8 text-muted-foreground">Technical strategy, GPT confidence, risk checks, position sizing, TP/SL monitoring, and PnL in one transparent flow.</p>
          <div className="mt-10 grid grid-cols-3 gap-3">
            {[
              [BrainCircuit, "GPT filter"],
              [ShieldCheck, "Risk rules"],
              [Activity, "Live simulation"]
            ].map(([Icon, label]) => {
              const FeatureIcon = Icon as typeof BrainCircuit;
              return <div key={label as string} className="glass rounded-md border border-white/10 p-4"><FeatureIcon className="mb-3 h-5 w-5 text-primary" /><span className="text-sm">{label as string}</span></div>;
            })}
          </div>
        </div>
        <p className="relative text-xs text-muted-foreground">Simulation only. No exchange orders or real funds.</p>
      </section>

      <section className="flex items-center justify-center px-5 py-12">
        <Card className="w-full max-w-md">
          <CardHeader>
            <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-md bg-white/[0.07]"><LockKeyhole size={19} /></div>
            <CardTitle className="text-2xl">{mode === "register" ? "Create development account" : "Sign in"}</CardTitle>
            <CardDescription>Your paper bot and development subscription are activated automatically.</CardDescription>
          </CardHeader>
          <CardContent>
            <form className="space-y-4" onSubmit={authenticate}>
              {mode === "register" && <label className="block space-y-2 text-sm">Full name<Input value={fullName} onChange={(event) => setFullName(event.target.value)} /></label>}
              <label className="block space-y-2 text-sm">Username<Input value={username} onChange={(event) => setUsername(event.target.value)} autoComplete="username" /></label>
              <label className="block space-y-2 text-sm">Password<Input type="password" value={password} onChange={(event) => setPassword(event.target.value)} autoComplete={mode === "register" ? "new-password" : "current-password"} /></label>
              {error && <p className="rounded-md border border-red-400/20 bg-red-400/10 px-3 py-2 text-sm text-red-200">{error}</p>}
              <Button className="w-full" size="lg" disabled={loading}>{loading ? "Connecting..." : mode === "register" ? "Create Account & Start" : "Sign In"}</Button>
            </form>
            <button className="mt-5 w-full text-sm text-muted-foreground hover:text-foreground" onClick={() => setMode(mode === "register" ? "login" : "register")}>
              {mode === "register" ? "Account already exists? Sign in" : "Need a fresh account? Register"}
            </button>
          </CardContent>
        </Card>
      </section>
    </main>
  );
}

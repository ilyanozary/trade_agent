"use client";

import type { ReactNode } from "react";
import { useEffect, useState } from "react";
import { AlertTriangle, BrainCircuit, Check, CheckCircle2, Play, Power, Settings2, ShieldCheck, TrendingDown, TrendingUp, Waves, X } from "lucide-react";
import { api } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

type Profile = { mode: string; risk_profile: string; symbol: string; is_enabled: boolean; confidence_threshold: number; risk_per_trade_percent: number; max_daily_loss_percent: number };
type EngineResult = {
  mode: string; symbol: string; position_opened: boolean; reason: string;
  strategy_signal: { action: string; confidence_base: number; entry_price: number; stop_loss: number; take_profit: number; strategy_reason: string; directional_confidence: { long: number; short: number; bias: string }; market_summary: Record<string, number | string> };
  ai_signal: { action: string; confidence: number; ai_reason: string };
  scenario_comparison: { preferred_scenario: string; note: string; long: TradeScenario; short: TradeScenario };
  position: null | { id: number; side: string; quantity: number; margin_usdt: number; entry_price: number; stop_loss: number; take_profit: number };
};
type TradeScenario = { side: "LONG" | "SHORT"; entry_price: number; stop_loss: number; take_profit: number; quantity: number; margin_usdt: number; risk_usdt: number; target_profit_usdt: number; target_return_percent: number; risk_reward_ratio: number; confidence: number; confidence_threshold: number; conditions_met: number; conditions_total: number; volume_confirmed: boolean; eligible: boolean; conditions: Array<{ label: string; passed: boolean }> };
type TickResult = { latest_price: number; timestamp: string; account: { balance_usdt: number; equity_usdt: number; unrealized_pnl: number }; open_positions: Array<{ id: number; symbol: string; side: string; pnl_usdt: number; pnl_percent: number }> };

export default function TradingBotPage() {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [result, setResult] = useState<EngineResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [tick, setTick] = useState<TickResult | null>(null);
  const [supportedSymbols, setSupportedSymbols] = useState<string[]>(["BTCUSDT", "ETHUSDT", "SOLUSDT"]);

  async function loadProfile() {
    const response = await api<{ data: { bot_profile: Profile; supported_symbols: string[] } }>("/api/bot/profile");
    setProfile(response.data.bot_profile);
    setSupportedSymbols(response.data.supported_symbols);
  }
  useEffect(() => { loadProfile().catch(error => setError(error.message)); }, []);
  useEffect(() => {
    if (!profile?.is_enabled) return;
    let active = true;
    async function refreshTick() {
      try {
        const response = await api<TickResult>("/api/paper/engine/tick", { method: "POST" });
        if (active) setTick(response);
      } catch (tickError) {
        if (active) setError(tickError instanceof Error ? tickError.message : "Price update failed");
      }
    }
    refreshTick();
    const interval = window.setInterval(refreshTick, 2000);
    return () => { active = false; window.clearInterval(interval); };
  }, [profile?.is_enabled, profile?.symbol]);

  async function updateProfile(changes: Partial<Profile>) {
    const response = await api<{ data: { bot_profile: Profile } }>("/api/bot/profile", { method: "PATCH", body: JSON.stringify({ ...changes, mode: "paper" }) });
    setProfile(response.data.bot_profile);
  }

  async function runEngine() {
    setLoading(true); setError(""); setResult(null);
    try {
      if (!profile?.is_enabled) await updateProfile({ is_enabled: true });
      const response = await api<EngineResult>("/api/paper/engine/run-once", { method: "POST" });
      setResult(response);
      await loadProfile();
    } catch (engineError) { setError(engineError instanceof Error ? engineError.message : "Engine failed"); }
    finally { setLoading(false); }
  }

  return <div className="space-y-6">
    <div><Badge className="border-primary/30 bg-primary/10 text-primary">Paper Trading = Simulated</Badge><h1 className="mt-4 text-3xl font-semibold">Trading Engine</h1><p className="mt-2 text-muted-foreground">Inspect transparent paper decisions and guarded live controls.</p></div>
    <LiveSafetyPanel />
    <div className="grid gap-4 lg:grid-cols-[0.8fr_1.2fr]">
      <Card><CardHeader><CardTitle>Engine Controls</CardTitle><CardDescription>No real funds or exchange orders are used.</CardDescription></CardHeader><CardContent className="space-y-5">
        <div className="rounded-md border border-primary/20 bg-primary/[0.06] p-4"><div className="flex items-center justify-between gap-3"><div><p className="text-xs uppercase text-muted-foreground">Live mock market · {profile?.symbol || "BTCUSDT"}</p><p className="mt-2 text-3xl font-semibold">{tick ? `$${tick.latest_price.toLocaleString(undefined, { maximumFractionDigits: tick.latest_price < 1 ? 6 : 2 })}` : "Waiting..."}</p></div><span className={`h-3 w-3 rounded-full ${profile?.is_enabled ? "animate-pulse bg-primary" : "bg-white/20"}`} /></div><div className="mt-4 grid grid-cols-3 gap-2 text-xs"><Stat label="Equity" value={tick ? `$${tick.account.equity_usdt.toFixed(2)}` : "-"} /><Stat label="Unrealized" value={tick ? `$${tick.account.unrealized_pnl.toFixed(2)}` : "-"} /><Stat label="Open" value={tick ? tick.open_positions.length : 0} /></div></div>
        <div className="flex items-center justify-between rounded-md border border-white/10 p-4"><div><p className="font-medium">Bot Status</p><p className="text-sm text-muted-foreground">{profile?.is_enabled ? "Enabled" : "Paused"}</p></div><button onClick={() => updateProfile({ is_enabled: !profile?.is_enabled })} className={`relative h-7 w-12 rounded-full transition ${profile?.is_enabled ? "bg-primary" : "bg-white/10"}`}><span className={`absolute left-1 top-1 h-5 w-5 rounded-full bg-white transition ${profile?.is_enabled ? "translate-x-5 bg-background" : ""}`} /></button></div>
        <label className="block space-y-2 text-sm">Symbol<select value={profile?.symbol || "BTCUSDT"} onChange={event => updateProfile({ symbol: event.target.value })} className="h-10 w-full rounded-md border border-white/10 bg-background px-3">{supportedSymbols.map(symbol=><option key={symbol}>{symbol}</option>)}</select></label>
        <label className="block space-y-2 text-sm">Risk profile<select value={profile?.risk_profile || "balanced"} onChange={event => updateProfile({ risk_profile: event.target.value })} className="h-10 w-full rounded-md border border-white/10 bg-background px-3"><option value="conservative">Conservative</option><option value="balanced">Balanced</option><option value="aggressive">Aggressive</option></select></label>
        <div className="grid grid-cols-2 gap-3 text-sm"><div className="rounded-md bg-white/[0.04] p-3"><p className="text-muted-foreground">Confidence gate</p><p className="mt-1 font-medium">{profile?.confidence_threshold || 70}%</p></div><div className="rounded-md bg-white/[0.04] p-3"><p className="text-muted-foreground">Risk / trade</p><p className="mt-1 font-medium">{profile?.risk_per_trade_percent || 1}%</p></div></div>
        <Button size="lg" className="w-full" onClick={runEngine} disabled={loading}>{loading ? <><Waves className="animate-pulse" size={18} /> Analyzing market...</> : <><Play size={18} /> {profile?.is_enabled ? "Run Analysis Now" : "Start Continuous Paper Bot"}</>}</Button>
        {error && <p className="rounded-md border border-red-400/20 bg-red-400/10 p-3 text-sm text-red-200">{error}</p>}
      </CardContent></Card>
      <Card><CardHeader><CardTitle>Decision Pipeline</CardTitle><CardDescription>Every stage of the virtual order decision.</CardDescription></CardHeader><CardContent>
        {!result ? <div className="flex h-80 flex-col items-center justify-center text-center text-muted-foreground"><BrainCircuit className="mb-4 h-10 w-10 opacity-40" /><p>Start a cycle to inspect strategy and GPT scoring.</p></div> : <div className="space-y-3">
          <PipelineStep icon={Settings2} title="1. Technical Strategy" status={`${result.strategy_signal.action} · ${result.strategy_signal.confidence_base}%`}><p>{result.strategy_signal.strategy_reason}</p><div className="mt-3 grid grid-cols-3 gap-2 text-xs"><Stat label="LONG score" value={`${result.strategy_signal.directional_confidence.long}%`} /><Stat label="SHORT score" value={`${result.strategy_signal.directional_confidence.short}%`} /><Stat label="Market bias" value={result.strategy_signal.directional_confidence.bias} /><Stat label="Entry" value={result.strategy_signal.entry_price} /><Stat label="Stop" value={result.strategy_signal.stop_loss} /><Stat label="Target" value={result.strategy_signal.take_profit} /></div></PipelineStep>
          <PipelineStep icon={BrainCircuit} title="2. GPT Confidence Filter" status={`${result.ai_signal.action} · ${result.ai_signal.confidence}%`}><p>{result.ai_signal.ai_reason}</p></PipelineStep>
          <PipelineStep icon={ShieldCheck} title="3. Risk Check" status={result.position_opened ? "Passed" : "Blocked"}><p>{result.reason}</p></PipelineStep>
          <PipelineStep icon={CheckCircle2} title="4. Virtual Position" status={result.position_opened ? "Opened" : "No order"}>{result.position ? <div className="grid grid-cols-2 gap-2 text-xs"><Stat label="Side" value={result.position.side} /><Stat label="Margin" value={`$${result.position.margin_usdt.toFixed(2)}`} /><Stat label="Quantity" value={result.position.quantity.toFixed(6)} /><Stat label="Position ID" value={`#${result.position.id}`} /></div> : <p>Nothing was executed. This is a valid risk outcome.</p>}</PipelineStep>
        </div>}
      </CardContent></Card>
    </div>
    {result && <ScenarioComparison comparison={result.scenario_comparison} livePrice={tick?.latest_price ?? result.strategy_signal.entry_price} />}
  </div>;
}

function LiveSafetyPanel(){
 const[accepted,setAccepted]=useState(false),[status,setStatus]=useState<{server_enabled:boolean;profile:{live_trading_enabled:boolean}}|null>(null),[message,setMessage]=useState("");
 const[risk,setRisk]=useState({max_daily_loss_percent:2,risk_per_trade_percent:.5,max_leverage:2,max_open_positions:1,confidence_threshold:75});
 async function load(){const r=await api<{data:{server_enabled:boolean;profile:{live_trading_enabled:boolean}}}>("/api/live/status");setStatus(r.data);}
 useEffect(()=>{load().catch(()=>undefined);},[]);
 async function enable(){try{await api("/api/live/enable",{method:"POST",body:JSON.stringify({accept_risk_disclaimer:accepted,...risk})});setMessage("Live mode enabled with V1 safety limits.");await load();}catch(e){setMessage(e instanceof Error?e.message:"Unable to enable live mode");}}
 async function kill(){await api("/api/live/kill-switch",{method:"POST"});setMessage("Kill switch active. New live orders are blocked.");await load();}
 const field=(key:keyof typeof risk,label:string,min:number,max:number,step:number)=><label className="space-y-2 text-xs text-muted-foreground">{label}<input type="number" min={min} max={max} step={step} value={risk[key]} onChange={e=>setRisk({...risk,[key]:Number(e.target.value)})} className="h-10 w-full rounded-md border border-white/10 bg-background px-3 text-sm text-foreground"/></label>;
 return <Card className="border-red-400/25"><CardHeader><div className="flex items-center gap-2 text-red-300"><AlertTriangle size={18}/><CardTitle>Live Trading = Real Money</CardTitle></div><CardDescription>Disabled by default. Losses are possible and AI does not guarantee success.</CardDescription></CardHeader><CardContent className="space-y-4"><div className="grid gap-3 md:grid-cols-5">{field("risk_per_trade_percent","Risk / trade %",.1,5,.1)}{field("max_daily_loss_percent","Daily loss %",.1,10,.1)}{field("max_leverage","Max leverage",1,3,1)}{field("max_open_positions","Max positions",1,5,1)}{field("confidence_threshold","Confidence gate",75,100,1)}</div><label className="flex items-start gap-3 rounded-md border border-red-400/20 bg-red-400/[0.06] p-4 text-sm"><input className="mt-1" type="checkbox" checked={accepted} onChange={e=>setAccepted(e.target.checked)}/><span>I understand that live trading uses real funds and losses are possible.</span></label><div className="flex flex-wrap gap-3"><Button className="bg-red-500 text-white hover:bg-red-400" disabled={!accepted||!status?.server_enabled||status?.profile.live_trading_enabled} onClick={enable}><Power size={16}/>Enable Live Trading</Button><Button variant="outline" className="border-red-400/30 text-red-300" onClick={kill}><AlertTriangle size={16}/>Kill Switch</Button><Badge>{status?.server_enabled?"Server gate enabled":"Server gate locked"}</Badge></div>{message&&<p className="text-sm text-muted-foreground">{message}</p>}</CardContent></Card>;
}

function PipelineStep({ icon: Icon, title, status, children }: { icon: typeof BrainCircuit; title: string; status: string; children: ReactNode }) {
  return <div className="rounded-md border border-white/10 bg-white/[0.025] p-4"><div className="mb-3 flex items-center justify-between gap-3"><div className="flex items-center gap-2 font-medium"><Icon size={17} className="text-primary" />{title}</div><Badge>{status}</Badge></div><div className="text-sm leading-6 text-muted-foreground">{children}</div></div>;
}
function Stat({ label, value }: { label: string; value: string | number }) { return <div className="rounded-md bg-black/20 p-2"><p className="text-muted-foreground">{label}</p><p className="mt-1 break-all text-foreground">{typeof value === "number" ? value.toFixed(2) : value}</p></div>; }

function ScenarioComparison({ comparison, livePrice }: { comparison: EngineResult["scenario_comparison"]; livePrice: number }) {
  return <Card>
    <CardHeader><div className="flex flex-wrap items-start justify-between gap-3"><div><CardTitle>What-If Scenario Comparison</CardTitle><CardDescription>If LONG or SHORT had been opened at analysis time, this is how each plan would look now.</CardDescription></div><Badge>Preferred: {comparison.preferred_scenario}</Badge></div></CardHeader>
    <CardContent>
      <div className="grid gap-4 lg:grid-cols-2">
        <ScenarioPanel scenario={comparison.long} livePrice={livePrice} icon={TrendingUp} />
        <ScenarioPanel scenario={comparison.short} livePrice={livePrice} icon={TrendingDown} />
      </div>
      <p className="mt-4 text-xs text-muted-foreground">{comparison.note}</p>
    </CardContent>
  </Card>;
}

function ScenarioPanel({ scenario, livePrice, icon: Icon }: { scenario: TradeScenario; livePrice: number; icon: typeof TrendingUp }) {
  const hypotheticalPnl = (scenario.side === "LONG" ? livePrice - scenario.entry_price : scenario.entry_price - livePrice) * scenario.quantity;
  const pnlPercent = scenario.margin_usdt ? hypotheticalPnl / scenario.margin_usdt * 100 : 0;
  const positive = hypotheticalPnl >= 0;
  const priceDigits = scenario.entry_price < 1 ? 6 : 2;
  return <section className={`rounded-md border p-4 ${scenario.eligible ? "border-primary/30 bg-primary/[0.045]" : "border-white/10 bg-white/[0.025]"}`}>
    <div className="flex items-start justify-between gap-3"><div className="flex items-center gap-2"><Icon size={19} className={scenario.side === "LONG" ? "text-primary" : "text-accent"} /><div><h3 className="font-semibold">If {scenario.side}</h3><p className="text-xs text-muted-foreground">{scenario.conditions_met}/{scenario.conditions_total} technical conditions</p></div></div><Badge className={scenario.eligible ? "border-primary/30 text-primary" : ""}>{scenario.confidence}% · {scenario.eligible ? "Eligible" : "Blocked"}</Badge></div>
    <div className="mt-4 rounded-md bg-black/20 p-3"><p className="text-xs text-muted-foreground">Hypothetical PnL at live price ${livePrice.toLocaleString(undefined, { maximumFractionDigits: priceDigits })}</p><p className={`mt-1 text-2xl font-semibold ${positive ? "text-primary" : "text-red-300"}`}>{positive ? "+" : ""}${hypotheticalPnl.toFixed(2)} <span className="text-sm font-normal">({positive ? "+" : ""}{pnlPercent.toFixed(2)}%)</span></p></div>
    <div className="mt-3 grid grid-cols-3 gap-2 text-xs"><Stat label="Entry" value={scenario.entry_price.toFixed(priceDigits)} /><Stat label="Stop Loss" value={scenario.stop_loss.toFixed(priceDigits)} /><Stat label="Take Profit" value={scenario.take_profit.toFixed(priceDigits)} /><Stat label="Margin" value={`$${scenario.margin_usdt.toFixed(2)}`} /><Stat label="Max Risk" value={`-$${scenario.risk_usdt.toFixed(2)}`} /><Stat label="Target" value={`+$${scenario.target_profit_usdt.toFixed(2)}`} /></div>
    <div className="mt-4 space-y-2">{scenario.conditions.map(condition => <div key={condition.label} className="flex items-center gap-2 text-sm"><span className={`flex h-5 w-5 items-center justify-center rounded-full ${condition.passed ? "bg-primary/15 text-primary" : "bg-red-400/10 text-red-300"}`}>{condition.passed ? <Check size={13} /> : <X size={13} />}</span><span className={condition.passed ? "text-foreground" : "text-muted-foreground"}>{condition.label}</span></div>)}<div className="flex items-center gap-2 text-sm"><span className={`flex h-5 w-5 items-center justify-center rounded-full ${scenario.volume_confirmed ? "bg-primary/15 text-primary" : "bg-white/[0.06] text-muted-foreground"}`}>{scenario.volume_confirmed ? <Check size={13} /> : <X size={13} />}</span><span className={scenario.volume_confirmed ? "text-foreground" : "text-muted-foreground"}>Volume above average (confidence bonus)</span></div></div>
  </section>;
}

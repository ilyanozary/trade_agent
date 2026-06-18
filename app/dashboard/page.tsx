"use client";

import { useCallback, useEffect, useState } from "react";
import { RefreshCw } from "lucide-react";
import { api } from "@/lib/api";
import { MetricCard } from "@/components/metric-card";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

type Overview = {
  paper_balance: number; paper_equity: number; paper_realized_pnl: number; paper_unrealized_pnl: number;
  open_positions_count: number; bot_status: string;
  recent_paper_trades: Array<{ id: number; symbol: string; side: string; pnl_usdt: number; status: string; confidence: number }>;
  latest_paper_signals: Array<{ id: number; symbol: string; action: string; confidence: number; executed: boolean; ai_reason: string }>;
};

export default function DashboardOverview() {
  const [data, setData] = useState<Overview | null>(null);
  const [error, setError] = useState("");
  const load = useCallback(async () => {
    try { const response = await api<{ data: Overview }>("/api/dashboard/overview"); setData(response.data); setError(""); }
    catch (e) { setError(e instanceof Error ? e.message : "Could not load dashboard"); }
  }, []);
  useEffect(() => { load(); }, [load]);

  if (!data) return <p className="text-sm text-muted-foreground">{error || "Loading paper account..."}</p>;
  const money = (value: number) => `$${value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  return <div className="space-y-6">
    <div className="flex items-start justify-between gap-4"><div><h1 className="text-3xl font-semibold">Paper Overview</h1><p className="mt-2 text-muted-foreground">Real values from the Flask paper trading engine.</p></div><Button variant="outline" size="sm" onClick={load}><RefreshCw size={15} /> Refresh</Button></div>
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      <MetricCard title="Available Balance" value={money(data.paper_balance)} detail="Virtual USDT available" />
      <MetricCard title="Paper Equity" value={money(data.paper_equity)} detail={`Unrealized ${money(data.paper_unrealized_pnl)}`} />
      <MetricCard title="Realized PnL" value={money(data.paper_realized_pnl)} detail="Closed simulated trades" />
      <MetricCard title="Open Positions" value={String(data.open_positions_count)} detail={`Bot ${data.bot_status}`} />
    </div>
    <div className="grid gap-4 xl:grid-cols-2">
      <Card><CardHeader><CardTitle>Latest GPT-Filtered Signals</CardTitle></CardHeader><CardContent className="space-y-3">{data.latest_paper_signals.length ? data.latest_paper_signals.map(signal => <div key={signal.id} className="rounded-md border border-white/10 bg-white/[0.03] p-3"><div className="flex justify-between gap-3"><span className="font-medium">{signal.symbol} · {signal.action}</span><span className="text-primary">{signal.confidence}%</span></div><p className="mt-2 text-sm text-muted-foreground">{signal.ai_reason}</p><p className="mt-2 text-xs text-muted-foreground">{signal.executed ? "Position executed" : "Not executed"}</p></div>) : <p className="text-sm text-muted-foreground">Run the paper engine to create the first signal.</p>}</CardContent></Card>
      <Card><CardHeader><CardTitle>Recent Paper Trades</CardTitle></CardHeader><CardContent className="space-y-3">{data.recent_paper_trades.length ? data.recent_paper_trades.map(trade => <div key={trade.id} className="flex items-center justify-between rounded-md border border-white/10 p-3 text-sm"><div><p className="font-medium">{trade.symbol} · {trade.side}</p><p className="text-muted-foreground">Confidence {trade.confidence}% · {trade.status}</p></div><span className={trade.pnl_usdt >= 0 ? "text-primary" : "text-red-300"}>{money(trade.pnl_usdt)}</span></div>) : <p className="text-sm text-muted-foreground">Closed virtual trades will appear here.</p>}</CardContent></Card>
    </div>
  </div>;
}

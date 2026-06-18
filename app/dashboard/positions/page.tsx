"use client";
import { useCallback, useEffect, useState } from "react";
import { RefreshCw, X } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

type Position = { id:number; symbol:string; side:string; entry_price:number; current_price:number; quantity:number; margin_usdt:number; stop_loss:number; take_profit:number; confidence:number; pnl_usdt:number; pnl_percent:number; status:string };
export default function PositionsPage(){
 const [positions,setPositions]=useState<Position[]>([]); const [error,setError]=useState("");
 const load=useCallback(async()=>{try{const r=await api<{data:{positions:Position[]}}>("/api/paper/positions");setPositions(r.data.positions);setError("");}catch(e){setError(e instanceof Error?e.message:"Load failed");}},[]);
 useEffect(()=>{load();},[load]);
 async function close(id:number){try{await api(`/api/paper/positions/${id}/close`,{method:"POST",body:"{}"});await load();}catch(e){setError(e instanceof Error?e.message:"Close failed");}}
 return <div className="space-y-6"><div className="flex justify-between gap-4"><div><h1 className="text-3xl font-semibold">Paper Positions</h1><p className="mt-2 text-muted-foreground">Virtual positions with live simulated PnL and TP/SL.</p></div><Button variant="outline" size="sm" onClick={load}><RefreshCw size={15}/>Refresh</Button></div>{error&&<p className="text-red-200">{error}</p>}<Card><CardHeader><CardTitle>All Positions</CardTitle></CardHeader><CardContent className="overflow-x-auto"><table className="w-full min-w-[950px] text-left text-sm"><thead className="text-muted-foreground"><tr className="border-b border-white/10">{["Symbol","Side","Entry","Current","Margin","PnL","SL / TP","GPT Score","Status",""].map(x=><th key={x} className="py-3 font-medium">{x}</th>)}</tr></thead><tbody>{positions.map(p=><tr key={p.id} className="border-b border-white/[0.07]"><td className="py-4 font-medium">{p.symbol}</td><td>{p.side}</td><td>${p.entry_price.toFixed(2)}</td><td>${p.current_price.toFixed(2)}</td><td>${p.margin_usdt.toFixed(2)}</td><td className={p.pnl_usdt>=0?"text-primary":"text-red-300"}>${p.pnl_usdt.toFixed(2)} ({p.pnl_percent.toFixed(2)}%)</td><td className="text-xs text-muted-foreground">{p.stop_loss.toFixed(2)} / {p.take_profit.toFixed(2)}</td><td>{p.confidence}%</td><td>{p.status}</td><td>{p.status==="open"&&<Button variant="outline" size="sm" onClick={()=>close(p.id)}><X size={14}/>Close</Button>}</td></tr>)}</tbody></table>{!positions.length&&<p className="py-10 text-center text-sm text-muted-foreground">No positions yet. Run the paper engine.</p>}</CardContent></Card></div>;
}

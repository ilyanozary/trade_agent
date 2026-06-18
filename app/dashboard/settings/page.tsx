"use client";
import { useEffect, useState } from "react";
import { KeyRound, RotateCcw, Unplug } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

type User={username:string;full_name:string;email:string|null;role:string};
type Connection={exchange:string;is_connected:boolean;last_validated_at:string|null};
export default function SettingsPage(){
 const[user,setUser]=useState<User|null>(null),[connection,setConnection]=useState<Connection|null>(null),[apiKey,setApiKey]=useState(""),[apiSecret,setApiSecret]=useState(""),[msg,setMsg]=useState(""),[error,setError]=useState("");
 async function load(){const[u,c]=await Promise.all([api<{data:{user:User}}>("/api/auth/me"),api<{data:{connection:Connection}}>("/api/exchange/bitunix/status")]);setUser(u.data.user);setConnection(c.data.connection);}
 useEffect(()=>{load().catch(e=>setError(e.message));},[]);
 async function connect(){setError("");setMsg("");try{await api("/api/exchange/bitunix/connect",{method:"POST",body:JSON.stringify({api_key:apiKey,api_secret:apiSecret})});setApiKey("");setApiSecret("");setMsg("Bitunix connection validated. Credentials are encrypted and never returned to the browser.");await load();}catch(e){setError(e instanceof Error?e.message:"Connection failed");}}
 async function disconnect(){await api("/api/exchange/bitunix/disconnect",{method:"DELETE"});setMsg("Bitunix disconnected and stored credentials removed.");await load();}
 async function reset(){if(!window.confirm("Reset the virtual balance, positions, signals and trade history?"))return;await api("/api/paper/account/reset",{method:"POST"});setMsg("Paper account reset to $10,000.");}
 return <div className="space-y-6"><div><h1 className="text-3xl font-semibold">Account Settings</h1><p className="mt-2 text-muted-foreground">Identity, simulation, and encrypted read-only exchange access.</p></div>
 <Card><CardHeader><CardTitle>Profile</CardTitle><CardDescription>Authentication uses username and password.</CardDescription></CardHeader><CardContent className="grid gap-4 md:grid-cols-2"><label className="space-y-2 text-sm">Username<Input value={user?.username||""} readOnly/></label><label className="space-y-2 text-sm">Full name<Input value={user?.full_name||""} readOnly/></label><label className="space-y-2 text-sm">Role<Input value={user?.role||"user"} readOnly/></label><label className="space-y-2 text-sm">Environment<Input value="Development" readOnly/></label></CardContent></Card>
 <Card><CardHeader><CardTitle>Bitunix Futures</CardTitle><CardDescription>Use a key without withdrawal permission. Start with read-only permissions.</CardDescription></CardHeader><CardContent className="space-y-4"><div className={`rounded-md border p-3 text-sm ${connection?.is_connected?"border-primary/30 bg-primary/[0.06]":"border-white/10"}`}>{connection?.is_connected?`Connected and validated ${connection.last_validated_at?new Date(connection.last_validated_at).toLocaleString():""}`:"Not connected"}</div>{!connection?.is_connected?<><div className="grid gap-3 md:grid-cols-2"><label className="space-y-2 text-sm">API Key<Input type="password" autoComplete="off" value={apiKey} onChange={e=>setApiKey(e.target.value)}/></label><label className="space-y-2 text-sm">API Secret<Input type="password" autoComplete="new-password" value={apiSecret} onChange={e=>setApiSecret(e.target.value)}/></label></div><Button onClick={connect} disabled={apiKey.length<8||apiSecret.length<8}><KeyRound size={16}/>Validate and Connect</Button></>:<Button variant="outline" onClick={disconnect}><Unplug size={16}/>Disconnect</Button>}</CardContent></Card>
 <Card><CardHeader><CardTitle>Reset Simulation</CardTitle><CardDescription>Clears virtual positions, signals and trades only.</CardDescription></CardHeader><CardContent><Button variant="outline" onClick={reset}><RotateCcw size={16}/>Reset Paper Account</Button></CardContent></Card>{msg&&<p className="text-sm text-primary">{msg}</p>}{error&&<p className="rounded-md border border-red-400/20 bg-red-400/10 p-3 text-sm text-red-200">{error}</p>}</div>;
}

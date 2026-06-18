export const equityCurve = [42, 45, 44, 49, 53, 52, 58, 61, 60, 66, 72, 76];
export const monthlyPerformance = [
  { month: "Jan", value: 4.2 },
  { month: "Feb", value: 6.1 },
  { month: "Mar", value: 3.4 },
  { month: "Apr", value: 8.7 },
  { month: "May", value: 5.8 },
  { month: "Jun", value: 7.2 }
];

export const recentTrades = [
  { symbol: "BTCUSDT", side: "Long", entry: "$67,420", exit: "$68,190", pnl: "+$184.20", confidence: "87%" },
  { symbol: "ETHUSDT", side: "Short", entry: "$3,485", exit: "$3,441", pnl: "+$96.80", confidence: "82%" },
  { symbol: "SOLUSDT", side: "Long", entry: "$151.20", exit: "$149.85", pnl: "-$34.10", confidence: "71%" },
  { symbol: "LINKUSDT", side: "Long", entry: "$17.42", exit: "$18.08", pnl: "+$52.30", confidence: "78%" }
];

export const openPositions = [
  { symbol: "BTCUSDT", direction: "Long", entry: "$67,880", current: "$68,240", pnl: "+$112.40", confidence: "89%", status: "Trailing" },
  { symbol: "ETHUSDT", direction: "Long", entry: "$3,412", current: "$3,436", pnl: "+$48.70", confidence: "84%", status: "Active" },
  { symbol: "AVAXUSDT", direction: "Short", entry: "$31.82", current: "$31.54", pnl: "+$27.60", confidence: "76%", status: "Watching" },
  { symbol: "BNBUSDT", direction: "Long", entry: "$612.40", current: "$608.10", pnl: "-$22.90", confidence: "68%", status: "Guarded" }
];

export const tradeHistory = [
  { date: "Jun 11", symbol: "BTCUSDT", entry: "$67,420", exit: "$68,190", pnl: "+$184.20", confidence: "87", reason: "Momentum confirmed after liquidity sweep." },
  { date: "Jun 10", symbol: "ETHUSDT", entry: "$3,485", exit: "$3,441", pnl: "+$96.80", confidence: "82", reason: "Trend rejection at volume node." },
  { date: "Jun 09", symbol: "SOLUSDT", entry: "$151.20", exit: "$149.85", pnl: "-$34.10", confidence: "71", reason: "Setup invalidated by volatility expansion." },
  { date: "Jun 08", symbol: "LINKUSDT", entry: "$17.42", exit: "$18.08", pnl: "+$52.30", confidence: "78", reason: "Breakout retest with improving breadth." }
];

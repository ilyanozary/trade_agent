import { monthlyPerformance } from "@/lib/data";

export function EquityChart({ data }: { data: number[] }) {
  const width = 640;
  const height = 260;
  const min = Math.min(...data) - 4;
  const max = Math.max(...data) + 4;
  const points = data.map((value, index) => {
    const x = (index / (data.length - 1)) * width;
    const y = height - ((value - min) / (max - min)) * height;
    return `${x},${y}`;
  });

  return (
    <div className="chart-grid h-72 overflow-hidden rounded-lg border border-white/10 bg-white/[0.03] p-4">
      <svg viewBox={`0 0 ${width} ${height}`} className="h-full w-full" role="img" aria-label="Equity curve">
        <defs>
          <linearGradient id="equityStroke" x1="0" x2="1">
            <stop stopColor="#24cbdb" />
            <stop offset="1" stopColor="#d9a549" />
          </linearGradient>
          <linearGradient id="equityFill" x1="0" x2="0" y1="0" y2="1">
            <stop stopColor="#24cbdb" stopOpacity="0.18" />
            <stop offset="1" stopColor="#24cbdb" stopOpacity="0" />
          </linearGradient>
        </defs>
        <polygon points={`0,${height} ${points.join(" ")} ${width},${height}`} fill="url(#equityFill)" />
        <polyline points={points.join(" ")} fill="none" stroke="url(#equityStroke)" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    </div>
  );
}

export function MonthlyPerformanceChart() {
  const max = Math.max(...monthlyPerformance.map((item) => item.value));
  return (
    <div className="flex h-72 items-end gap-3 rounded-lg border border-white/10 bg-white/[0.03] p-4">
      {monthlyPerformance.map((item) => (
        <div key={item.month} className="flex flex-1 flex-col items-center gap-3">
          <div className="w-full rounded-t-md bg-gradient-to-t from-secondary/70 to-primary/80" style={{ height: `${(item.value / max) * 210}px` }} />
          <span className="text-xs text-muted-foreground">{item.month}</span>
        </div>
      ))}
    </div>
  );
}

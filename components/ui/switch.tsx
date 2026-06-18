"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";

export function Switch({ defaultChecked = false }: { defaultChecked?: boolean }) {
  const [checked, setChecked] = useState(defaultChecked);
  return (
    <button
      type="button"
      aria-pressed={checked}
      onClick={() => setChecked((value) => !value)}
      className={cn("relative h-7 w-12 rounded-full border border-white/10 transition", checked ? "bg-primary" : "bg-white/10")}
    >
      <span className={cn("absolute left-1 top-1 h-5 w-5 rounded-full bg-white transition", checked && "translate-x-5 bg-background")} />
    </button>
  );
}

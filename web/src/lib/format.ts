import { format } from "d3-format";

const pct0 = format(".0%");
const int = format(",d");
const dec2 = format(".2f");

export const fmtPct = (v: number | null | undefined) => (v === null || v === undefined ? "—" : pct0(v));
export const fmtInt = (v: number | null | undefined) => (v === null || v === undefined ? "—" : int(v));
export const fmtScore = (v: number | null | undefined) => (v === null || v === undefined ? "—" : dec2(v));
export const fmtTemp = (v: number | null | undefined) =>
  v === null || v === undefined ? "—" : `${v >= 0 ? "+" : "−"}${Math.abs(v).toFixed(1)} °C`;

/** "6 of 29 (3–9)" — the median rank with its 90% interval. */
export function fmtRank(rank: number | null, ci: [number | null, number | null], of: number): string {
  if (rank === null) return "Not ranked";
  const [lo, hi] = ci;
  const range = lo !== null && hi !== null && lo !== hi ? ` (90%: ${lo}–${hi})` : "";
  return `${Math.round(rank)} of ${of}${range}`;
}

export function fmtDate(iso: string): string {
  if (!iso) return "—";
  const d = new Date(iso);
  return Number.isNaN(d.getTime())
    ? iso
    : d.toLocaleDateString("en-PH", { year: "numeric", month: "short", day: "numeric", timeZone: "Asia/Manila" });
}

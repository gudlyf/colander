// Recipe times are free text ("1 hr 15 min", "10-12 min", "2 hours (includes chilling)").
// When a recipe has no total time, show prep + cook instead, if both can be read.

import { parseNumber } from "./scale";

interface Times {
  prep_time: string | null;
  cook_time: string | null;
  total_time: string | null;
}

/** The recipe's total time, or prep + cook when it has none. */
export function totalTime(r: Times): string | null {
  const given = r.total_time?.trim();
  if (given) return given;
  const prep = parseDuration(r.prep_time);
  const cook = parseDuration(r.cook_time);
  if (!prep || !cook) return null;
  return formatDuration({ lo: prep.lo + cook.lo, hi: prep.hi + cook.hi });
}

/** A duration in minutes; lo < hi for a range such as "10-12 min". */
export interface Duration {
  lo: number;
  hi: number;
}

const UNITS: [RegExp, number][] = [
  [/^d(ays?)?$/, 1440],
  [/^h(ours?|rs?)?$/, 60],
  [/^m(in(ute)?s?)?$/, 1],
];
const TERM = /(\d+(?:[.,]\d+)?\s*[½¼¾]?|[½¼¾])\s*([a-z]*)/g;

export function parseDuration(text: string | null): Duration | null {
  if (!text) return null;
  const s = text
    .toLowerCase()
    .replace(/\(.*?\)/g, " ") // "(includes chilling time)"
    .replace(/\s+to\s+/g, "-")
    .replace(/[–—]/g, "-")
    .trim();
  const parts = s.split("-");
  if (parts.length > 2) return null;
  const terms = parts.map(parseTerms);
  if (terms.some((t) => !t || t.length === 0)) return null;
  const [first, second] = terms as Term[][];
  // "10-12 min": the first half takes its unit from the second.
  if (second) for (const t of first) t.unit ??= second[0].unit;
  const lo = minutes(first);
  const hi = second ? minutes(second) : lo;
  return hi >= lo ? { lo, hi } : null;
}

interface Term {
  value: number;
  unit: number | undefined;
}

function parseTerms(part: string): Term[] | null {
  const terms: Term[] = [];
  let rest = part;
  for (const m of part.matchAll(TERM)) {
    const value = parseNumber(m[1]);
    let unit: number | undefined;
    if (m[2]) {
      const u = UNITS.find(([re]) => re.test(m[2]));
      if (!u) return null; // "5 servings", "overnight"
      unit = u[1];
    }
    if (value === null) return null;
    terms.push({ value, unit });
    rest = rest.replace(m[0], "");
  }
  // Only numbers, units and filler ("and", commas) are allowed.
  return rest.replace(/\band\b|[,+\s]/g, "") ? null : terms;
}

function minutes(terms: Term[]): number {
  return Math.round(terms.reduce((sum, t) => sum + t.value * (t.unit ?? 1), 0));
}

export function formatDuration({ lo, hi }: Duration): string | null {
  if (hi <= 0) return null;
  if (lo === hi) return format(lo);
  if (hi < 60) return `${lo}–${hi} min`;
  return `${format(lo)} – ${format(hi)}`;
}

function format(total: number): string {
  const days = Math.floor(total / 1440);
  const hours = Math.floor((total % 1440) / 60);
  const mins = total % 60;
  const out = [];
  if (days) out.push(`${days} ${days === 1 ? "day" : "days"}`);
  if (hours) out.push(`${hours} hr`);
  if (mins || out.length === 0) out.push(`${mins} min`);
  return out.join(" ");
}

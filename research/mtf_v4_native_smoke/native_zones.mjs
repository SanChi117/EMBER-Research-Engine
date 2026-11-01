// Archived SMOKE source-native 4H zone snapshot runner.
// The imported source files are byte-identical to their pinned Git blobs.
// The wrapper only supplies closed candles as-of each requested timestamp.
import { buildZones } from "./source/zones.ts";
import { detectStructure, findPivots } from "./source/structure.ts";
import { wilderAtr } from "./source/math.ts";


function eligibleOriginalKeys(candles) {
  const set = new Set();
  const pivots = findPivots(candles, 3, 3);
  for (const p of pivots.slice(-20)) {
    set.add(["swing", p.kind === "low" ? "demand" : "supply", p.time].join("|"));
  }
  const events = detectStructure(candles, "4h", 3);
  for (const event of events.slice(-24)) {
    const idx = candles.findIndex(c => c.time === event.time);
    if (idx < 1) continue;
    let origin = null;
    for (let j = idx - 1; j >= Math.max(0, idx - 10); j--) {
      const bearish = candles[j].close < candles[j].open;
      if ((event.side === "long" && bearish) || (event.side === "short" && !bearish)) {
        origin = candles[j];
        break;
      }
    }
    if (!origin) origin = candles[Math.max(0, idx - 1)];
    if (origin) {
      set.add(["order_block", event.side === "long" ? "demand" : "supply", origin.time].join("|"));
    }
  }
  const atr = wilderAtr(candles, 14);
  for (let i = Math.max(2, candles.length - 180); i < candles.length; i++) {
    const first = candles[i - 2], current = candles[i];
    const threshold = (atr[i] || current.close * .005) * .12;
    if (current.low > first.high && current.low - first.high >= threshold) {
      set.add(["fvg", "demand", current.time].join("|"));
    } else if (current.high < first.low && first.low - current.high >= threshold) {
      set.add(["fvg", "supply", current.time].join("|"));
    }
  }
  return [...set];
}

let input = "";
for await (const chunk of process.stdin) input += chunk;
const payload = JSON.parse(input);
if (!payload || !Array.isArray(payload.snapshots)) {
  throw new Error("snapshots array required");
}
const output = [];
for (const s of payload.snapshots) {
  if (!Array.isArray(s.candles) || s.candles.length < 20) {
    throw new Error("insufficient closed candles " + s.symbol);
  }
  const latest = s.candles[s.candles.length - 1];
  if (latest.time + 4 * 3600000 !== s.asof) {
    throw new Error("future/incomplete close in " + s.symbol);
  }
  const zones = buildZones(s.candles, "4h");
  output.push({
    symbol: s.symbol,
    n: s.n,
    asof: s.asof,
    eligible_keys: eligibleOriginalKeys(s.candles),
    zones: zones.map(z => ({
      family: z.source,
      kind: z.kind,
      origin_at: z.originTime,
      low: z.low,
      high: z.high,
      active: z.active,
      score: z.score,
      touches: z.touches,
      id: z.id
    }))
  });
}
process.stdout.write(JSON.stringify({ snapshots: output }));

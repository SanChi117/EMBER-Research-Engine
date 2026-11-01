// Archived SMOKE source-native 4H zone snapshot runner.
// The imported source files are byte-identical to their pinned Git blobs.
// The wrapper only supplies closed candles as-of each requested timestamp.
import { buildZones } from "./source/zones.ts";

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

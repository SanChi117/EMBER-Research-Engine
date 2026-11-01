import type { Candle, PriceZone, Side, Timeframe, ZoneKind } from "./types.ts";
import { wilderAtr } from "./math.ts";
import { detectStructure, findPivots } from "./structure.ts";

function lastOppositeCandle(candles: Candle[], breakIndex: number, side: Side): Candle | null {
  for (let index = breakIndex - 1; index >= Math.max(0, breakIndex - 10); index -= 1) {
    const candle = candles[index];
    const bearish = candle.close < candle.open;
    if ((side === "long" && bearish) || (side === "short" && !bearish)) return candle;
  }
  return candles[Math.max(0, breakIndex - 1)] ?? null;
}

function overlaps(candle: Candle, zone: { low: number; high: number }): boolean {
  return candle.low <= zone.high && candle.high >= zone.low;
}

/** A cluster of consecutive candles inside a zone counts as one separate visit. */
function countDistinctTouches(candles: Candle[], zone: { low: number; high: number }, afterTime: number): number {
  let touches = 0;
  let inside = false;
  for (const candle of candles) {
    if (candle.time <= afterTime) continue;
    const current = overlaps(candle, zone);
    if (current && !inside) touches += 1;
    inside = current;
  }
  return touches;
}

function zoneStillActive(
  candles: Candle[],
  zone: { kind: ZoneKind; low: number; high: number },
  afterTime: number,
): boolean {
  const subsequent = candles.filter((candle) => candle.time > afterTime);
  return zone.kind === "demand"
    ? !subsequent.some((candle) => candle.close < zone.low)
    : !subsequent.some((candle) => candle.close > zone.high);
}

function departureQuality(
  candles: Candle[],
  index: number,
  kind: ZoneKind,
  price: number,
  atr: number,
): number {
  const future = candles.slice(index + 1, index + 9);
  if (!future.length) return 0;
  const excursion = kind === "demand"
    ? Math.max(...future.map((candle) => candle.high)) - price
    : price - Math.min(...future.map((candle) => candle.low));
  return Math.max(0, excursion / Math.max(atr, 1e-9));
}

function timeframeBonus(timeframe: Timeframe): number {
  if (timeframe === "1w") return 10;
  if (timeframe === "1d") return 7;
  if (timeframe === "4h") return 3;
  return 0;
}

function addPreviousRangeLevels(
  candles: Candle[],
  timeframe: Timeframe,
  atr: number[],
  zones: PriceZone[],
): void {
  if ((timeframe !== "1d" && timeframe !== "1w") || candles.length < 2) return;
  const previous = candles.at(-1)!;
  const atrValue = atr.at(-1) || Math.max(previous.high - previous.low, previous.close * 0.005);
  const width = atrValue * (timeframe === "1w" ? 0.16 : 0.12);
  const rows: Array<{ kind: ZoneKind; price: number; suffix: string }> = [
    { kind: "supply", price: previous.high, suffix: timeframe === "1w" ? "PWH" : "PDH" },
    { kind: "demand", price: previous.low, suffix: timeframe === "1w" ? "PWL" : "PDL" },
  ];
  for (const row of rows) {
    const low = row.price - width;
    const high = row.price + width;
    zones.push({
      id: `${timeframe}-range-${row.kind}-${previous.time}`,
      timeframe,
      kind: row.kind,
      source: "range_level",
      low,
      high,
      midpoint: row.price,
      originTime: previous.time,
      score: timeframe === "1w" ? 72 : 64,
      active: true,
      touches: 0,
      label: row.suffix,
    });
  }
}

function addFairValueGaps(
  candles: Candle[],
  timeframe: Timeframe,
  atr: number[],
  zones: PriceZone[],
): void {
  if (timeframe !== "1d" && timeframe !== "4h") return;
  const start = Math.max(2, candles.length - (timeframe === "1d" ? 90 : 180));
  for (let index = start; index < candles.length; index += 1) {
    const first = candles[index - 2];
    const current = candles[index];
    const atrValue = atr[index] || current.close * 0.005;
    let kind: ZoneKind | null = null;
    let low = 0;
    let high = 0;
    if (current.low > first.high) {
      kind = "demand";
      low = first.high;
      high = current.low;
    } else if (current.high < first.low) {
      kind = "supply";
      low = current.high;
      high = first.low;
    }
    if (!kind || high - low < atrValue * 0.12) continue;
    const touches = countDistinctTouches(candles, { low, high }, current.time);
    const active = zoneStillActive(candles, { kind, low, high }, current.time);
    const gapAtr = (high - low) / Math.max(atrValue, 1e-9);
    const score = Math.max(0, Math.min(
      100,
      45 + timeframeBonus(timeframe) + Math.min(18, gapAtr * 14) - touches * 7,
    ));
    zones.push({
      id: `${timeframe}-fvg-${kind}-${current.time}`,
      timeframe,
      kind,
      source: "fvg",
      low,
      high,
      midpoint: (low + high) / 2,
      originTime: current.time,
      score: Math.round(active ? score : 20),
      active,
      touches,
      label: `${timeframe.toUpperCase()} ${kind === "demand" ? "Bullish" : "Bearish"} FVG`,
    });
  }
}

export function buildZones(candles: Candle[], timeframe: Timeframe): PriceZone[] {
  if (candles.length < 20) return [];
  const atr = wilderAtr(candles, 14);
  const events = detectStructure(candles, timeframe, timeframe === "1w" ? 2 : 3);
  const zones: PriceZone[] = [];

  for (const event of events.slice(-24)) {
    const breakIndex = candles.findIndex((candle) => candle.time === event.time);
    if (breakIndex < 1) continue;
    const origin = lastOppositeCandle(candles, breakIndex, event.side);
    if (!origin) continue;
    const atrAtBreak = atr[breakIndex] || origin.high - origin.low;
    const kind: ZoneKind = event.side === "long" ? "demand" : "supply";
    const low = kind === "demand" ? origin.low : Math.min(origin.open, origin.close);
    const high = kind === "demand" ? Math.max(origin.open, origin.close) : origin.high;
    const displacement = Math.abs(candles[breakIndex].close - origin.close) / Math.max(atrAtBreak, 1e-9);
    const touches = countDistinctTouches(candles, { low, high }, origin.time);
    const active = zoneStillActive(candles, { kind, low, high }, origin.time);
    const score = Math.max(0, Math.min(
      100,
      43 + timeframeBonus(timeframe) + displacement * 12
        - Math.max(0, touches - 1) * 7 + (event.tag === "CHoCH" ? 8 : 4),
    ));
    zones.push({
      id: `${timeframe}-ob-${kind}-${origin.time}`,
      timeframe,
      kind,
      source: "order_block",
      low,
      high,
      midpoint: (low + high) / 2,
      originTime: origin.time,
      score: Math.round(active ? score : 20),
      active,
      touches,
      label: `${timeframe.toUpperCase()} ${kind === "demand" ? "Demand OB" : "Supply OB"}`,
    });
  }

  const pivotSize = timeframe === "1w" ? 2 : 3;
  const pivots = findPivots(candles, pivotSize, pivotSize);
  for (const pivot of pivots.slice(-20)) {
    const atrAtPivot = atr[pivot.index] || pivot.price * 0.005;
    const width = atrAtPivot * (timeframe === "4h" ? 0.28 : 0.35);
    const kind: ZoneKind = pivot.kind === "low" ? "demand" : "supply";
    const low = kind === "demand" ? pivot.price - width * 0.15 : pivot.price - width;
    const high = kind === "demand" ? pivot.price + width : pivot.price + width * 0.15;
    const active = zoneStillActive(candles, { kind, low, high }, pivot.time);
    const touches = countDistinctTouches(candles, { low, high }, pivot.time);
    const departure = departureQuality(candles, pivot.index, kind, pivot.price, atrAtPivot);
    const structuralBonus = pivot.label === "HL" || pivot.label === "LH" ? 6 : 2;
    const score = Math.max(0, Math.min(
      100,
      48 + timeframeBonus(timeframe) + Math.min(22, departure * 6)
        + structuralBonus - Math.max(0, touches - 1) * 6,
    ));
    zones.push({
      id: `${timeframe}-swing-${kind}-${pivot.time}`,
      timeframe,
      kind,
      source: "swing",
      low,
      high,
      midpoint: (low + high) / 2,
      originTime: pivot.time,
      score: Math.round(active ? score : 20),
      active,
      touches,
      label: `${timeframe.toUpperCase()} ${pivot.label}`,
    });
  }

  addFairValueGaps(candles, timeframe, atr, zones);
  addPreviousRangeLevels(candles, timeframe, atr, zones);

  return zones
    .filter((zone) => zone.high > zone.low && Number.isFinite(zone.low) && Number.isFinite(zone.high))
    .filter((zone, index, all) => all.findIndex((item) => (
      item.kind === zone.kind
      && item.timeframe === zone.timeframe
      && Math.abs(item.midpoint - zone.midpoint) / Math.max(zone.midpoint, 1e-9) < 0.0006
    )) === index)
    .sort((a, b) => b.score - a.score || b.originTime - a.originTime);
}

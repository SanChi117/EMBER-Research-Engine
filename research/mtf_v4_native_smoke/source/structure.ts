import type { Bias, Candle, Pivot, StructureEvent, StructureTag, Timeframe } from "./types.ts";

export function findPivots(candles: Candle[], left = 3, right = 3): Pivot[] {
  const pivots: Pivot[] = [];
  let previousHigh: number | null = null;
  let previousLow: number | null = null;
  for (let index = left; index < candles.length - right; index += 1) {
    const candle = candles[index];
    const window = candles.slice(index - left, index + right + 1);
    const isHigh = window.every((item, offset) => offset === left || candle.high > item.high);
    const isLow = window.every((item, offset) => offset === left || candle.low < item.low);
    if (isHigh) {
      const label: Pivot["label"] = previousHigh === null || candle.high > previousHigh ? "HH" : "LH";
      pivots.push({ index, time: candle.time, price: candle.high, kind: "high", label });
      previousHigh = candle.high;
    }
    if (isLow) {
      const label: Pivot["label"] = previousLow === null || candle.low > previousLow ? "HL" : "LL";
      pivots.push({ index, time: candle.time, price: candle.low, kind: "low", label });
      previousLow = candle.low;
    }
  }
  return pivots.sort((a, b) => a.index - b.index);
}

export function detectStructure(candles: Candle[], timeframe: Timeframe, pivotSize = 3): StructureEvent[] {
  const pivots = findPivots(candles, pivotSize, pivotSize);
  const events: StructureEvent[] = [];
  let lastHigh: Pivot | null = null;
  let lastLow: Pivot | null = null;
  let bias: Bias = "neutral";
  let crossedHighTime = 0;
  let crossedLowTime = 0;

  for (let index = 0; index < candles.length; index += 1) {
    for (const pivot of pivots) {
      if (pivot.index + pivotSize !== index) continue;
      if (pivot.kind === "high") lastHigh = pivot;
      else lastLow = pivot;
    }
    const candle = candles[index];
    if (lastHigh && candle.close > lastHigh.price && crossedHighTime !== lastHigh.time) {
      const tag: StructureTag = bias === "down" ? "CHoCH" : "BOS";
      events.push({ time: candle.time, price: lastHigh.price, side: "long", tag, timeframe, pivotTime: lastHigh.time });
      bias = "up";
      crossedHighTime = lastHigh.time;
    }
    if (lastLow && candle.close < lastLow.price && crossedLowTime !== lastLow.time) {
      const tag: StructureTag = bias === "up" ? "CHoCH" : "BOS";
      events.push({ time: candle.time, price: lastLow.price, side: "short", tag, timeframe, pivotTime: lastLow.time });
      bias = "down";
      crossedLowTime = lastLow.time;
    }
  }
  return events;
}

export function structureBias(candles: Candle[], timeframe: Timeframe, pivotSize = 3): Bias {
  const events = detectStructure(candles, timeframe, pivotSize);
  const last = events.at(-1);
  if (last) return last.side === "long" ? "up" : "down";
  const pivots = findPivots(candles, pivotSize, pivotSize);
  const highs = pivots.filter((pivot) => pivot.kind === "high").slice(-2);
  const lows = pivots.filter((pivot) => pivot.kind === "low").slice(-2);
  if (highs.length === 2 && lows.length === 2) {
    if (highs[1].price > highs[0].price && lows[1].price > lows[0].price) return "up";
    if (highs[1].price < highs[0].price && lows[1].price < lows[0].price) return "down";
  }
  return "neutral";
}

import type { Candle, Timeframe } from "./types.ts";

export const TF_MS: Record<Timeframe, number> = {
  "5m": 5 * 60_000,
  "15m": 15 * 60_000,
  "4h": 4 * 60 * 60_000,
  "1d": 24 * 60 * 60_000,
  "1w": 7 * 24 * 60 * 60_000,
};

export function closedCandles(candles: Candle[], timeframe: Timeframe, now = Date.now()): Candle[] {
  const duration = TF_MS[timeframe];
  return candles.filter((candle) => candle.time + duration <= now);
}

export function mean(values: number[]): number {
  if (!values.length) return 0;
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

export function ema(values: number[], length: number): number[] {
  if (!values.length) return [];
  const result = new Array<number>(values.length);
  const alpha = 2 / (length + 1);
  let value = values[0];
  for (let index = 0; index < values.length; index += 1) {
    if (index === 0) value = values[0];
    else value = alpha * values[index] + (1 - alpha) * value;
    result[index] = value;
  }
  return result;
}

export function wilderAtr(candles: Candle[], length = 14): number[] {
  if (!candles.length) return [];
  const tr = candles.map((candle, index) => {
    const previous = candles[index - 1];
    if (!previous) return candle.high - candle.low;
    return Math.max(
      candle.high - candle.low,
      Math.abs(candle.high - previous.close),
      Math.abs(candle.low - previous.close),
    );
  });
  const result = new Array<number>(candles.length);
  let atr = tr[0];
  for (let index = 0; index < tr.length; index += 1) {
    if (index < length) atr = mean(tr.slice(0, index + 1));
    else atr = ((atr * (length - 1)) + tr[index]) / length;
    result[index] = atr;
  }
  return result;
}

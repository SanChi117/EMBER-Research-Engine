export type Side = "long" | "short";
export type Bias = "up" | "down" | "neutral";
export type ZoneKind = "demand" | "supply";
export type ZoneSource = "order_block" | "swing" | "fvg" | "range_level";
export type StructureTag = "BOS" | "CHoCH";
export type Timeframe = "1w" | "1d" | "4h" | "15m" | "5m";
export type SetupModel = "location" | "reversal" | "continuation" | "blocked";
export type QualitySegment = "QFVG_FS15";

export type Candle = {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
};

export type TimeframeBundle = Record<Timeframe, Candle[]>;

export type Pivot = {
  index: number;
  time: number;
  price: number;
  kind: "high" | "low";
  label: "HH" | "HL" | "LH" | "LL";
};

export type StructureEvent = {
  time: number;
  price: number;
  side: Side;
  tag: StructureTag;
  timeframe: Timeframe;
  pivotTime: number;
};

export type PriceZone = {
  id: string;
  timeframe: Timeframe;
  kind: ZoneKind;
  source: ZoneSource;
  low: number;
  high: number;
  midpoint: number;
  originTime: number;
  score: number;
  active: boolean;
  touches: number;
  label: string;
};

export type StrategyTraceStep = {
  id: "context" | "level" | "approach" | "reaction" | "entry";
  label: string;
  state: "pass" | "pending" | "fail";
  detail: string;
};

export type Reaction = {
  confirmed: boolean;
  side: Side | null;
  type: "sweep_reclaim" | "structure_retest" | "displacement" | "none";
  score: number;
  time: number | null;
  triggerPrice: number | null;
  sweepPrice: number | null;
  detail: string;
};

export type TrendStrength = "strong" | "normal" | "weak";

export type AuxiliaryMetrics = {
  dailyEma50: number | null;
  dailyEma200: number | null;
  fourHourEma50: number | null;
  fourHourEma200: number | null;
  fourHourRsi14: number | null;
  fifteenMinuteRsi14: number | null;
  reactionVolumeRatio: number | null;
};

export type FourHourRoute = {
  bias: Bias;
  state: "approaching" | "inside" | "departing" | "moving_away" | "invalidated" | "no_level";
  distanceAtr: number | null;
  distanceDecreasing: boolean;
  detail: string;
};

export type MtfLevelAnalysis = {
  version: "SMOKE_LEVEL_FLOW_V1" | "SMOKE_LEVEL_FLOW_V3_AUDIT";
  evaluatedAt: number;
  symbol: string;
  bias: Bias;
  weeklyBias: Bias;
  dailyBias: Bias;
  trendStrength: TrendStrength;
  range: {
    low: number;
    high: number;
    equilibrium: number;
    position: "premium" | "discount" | "equilibrium";
  } | null;
  side: Side | null;
  state: "ready" | "watch" | "blocked";
  confidence: number;
  setupModel?: SetupModel | null;
  modelDetail?: string | null;
  qualitySegment?: QualitySegment | null;
  activeZone: PriceZone | null;
  targetZone: PriceZone | null;
  zones: PriceZone[];
  structure: StructureEvent[];
  route4h: FourHourRoute;
  metrics: AuxiliaryMetrics;
  reaction: Reaction;
  entry: number | null;
  stop: number | null;
  target: number | null;
  rr: number | null;
  reason: string;
  blockers: string[];
  trace: StrategyTraceStep[];
};

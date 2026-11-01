"""Point-in-time 4H POI -> 1H effort/result event registry across futures pairs.

NO trade entries are issued here. All zones and original 1H attempts are
recorded, independently of final outcome. Future returns are separate labels.
"""
from __future__ import annotations

from bisect import bisect_right
from collections import defaultdict
from dataclasses import asdict, dataclass
from typing import Sequence

from ember.research.mtf_v2_bars import D1, H1, H4, FlowBar
from ember.research.mtf_v3_zones import Zone, wilder_atr

HORIZONS = (1, 3, 6, 12, 24)


@dataclass(frozen=True)
class Contact:
    symbol: str
    event_id: str
    event_at: int  # end of original observed 1H contact
    available_at: int
    zone_id: str
    zone_family: str
    side: str
    origin_at: int
    zone_known_at: int
    zone_low: float
    zone_high: float
    h4_atr_asof: float
    h4_close_available_at: int
    d1_bias_asof: str
    zone_4h_age: int
    zone_prior_retests: int
    effort_volume_ratio: float
    taker_buy_fraction: float
    aggressor_pressure: float
    close_position: float
    penetration_atr4: float
    reclaimed_zone_at_close: bool
    closed_inside_zone: bool
    contact_close: float
    indicative_stop: float
    opposite_structural_target: float | None

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class LabeledEvent:
    event_id: str
    symbol: str
    side: str
    cohort: str
    label_available_at: int | None
    status: str
    entry_time: int | None
    entry_price: float | None
    forward_close_returns_pct: dict
    forward_max_favorable_pct: dict
    forward_max_adverse_pct: dict
    prospective_transfer_at: int | None
    future_label_not_entry_signal: bool = True

    def as_dict(self) -> dict:
        return asdict(self)


def validate_hourly(bars: Sequence[FlowBar]) -> None:
    for i,b in enumerate(bars):
        if (b.ts % H1 or b.low <= 0 or b.high < max(b.open,b.close)
                or b.low > min(b.open,b.close) or b.high < b.low or b.volume < 0
                or not 0 <= b.taker_buy <= b.volume*(1+1e-9)
                or (i and b.ts != bars[i-1].ts + H1)):
            raise ValueError(f"invalid/gapped 1H futures series at {i}")


def d1_bias(four: Sequence[FlowBar], end_times: Sequence[int], asof: int) -> str:
    """Use 4H bars only up to last *complete UTC day*."""
    previous_midnight = (asof // D1) * D1
    j = bisect_right(end_times, previous_midnight)
    if j < 126:
        return "UNKNOWN"
    days = []
    for i in range(j-6*21, j, 6):
        part = four[i:i+6]
        if len(part) == 6 and part[0].ts % D1 == 0 and part[-1].ts + H4 <= previous_midnight:
            days.append(part[-1].close)
    if len(days) < 21:
        return "UNKNOWN"
    return "UP" if days[-1] > days[0]*1.02 else "DOWN" if days[-1] < days[0]*.98 else "RANGE"


def registry(symbol: str, one: Sequence[FlowBar], four: Sequence[FlowBar],
             zones: Sequence[Zone]) -> tuple[list[Contact], list[LabeledEvent]]:
    """All distinct 1H contacts with known-active source-derived 4H zones.

    Repeated hours overlapping the SAME zone form one episode until the
    previous hour stops overlapping it. Nearby distinct zones remain separate
    observations (cannot be counted as independent PnL).
    """
    validate_hourly(one)
    if len(four) < 135:
        raise ValueError("insufficient 4H warmup")
    four_closes = [x.ts + H4 for x in four]
    atr = wilder_atr(four)
    active_cache: dict[int,list[Zone]] = {}
    previous_contact: dict[str,bool] = defaultdict(bool)
    contacts: list[Contact] = []
    labels: list[LabeledEvent] = []
    for i in range(21,len(one)):
        b = one[i]
        known_at = b.ts  # 1H candle OPEN, before its intrabar future
        k = bisect_right(four_closes, known_at)-1
        if k < 20:
            continue
        parent_time = four_closes[k]
        if parent_time not in active_cache:
            active_cache[parent_time] = [z for z in zones if z.known_active(known_at)]
        active = active_cache[parent_time]
        volume_mean = sum(x.volume for x in one[i-20:i])/20
        if volume_mean <= 0:
            continue
        prior_bias = d1_bias(four, four_closes, known_at)
        touched: set[str] = set()
        for z in active:
            if not(b.low <= z.high and b.high >= z.low):
                continue
            touched.add(z.zone_id)
            if previous_contact.get(z.zone_id):
                continue
            sign = 1 if z.kind == "demand" else -1
            pressure = b.taker_buy / b.volume if b.volume else .5
            # Positive when attempted aggressor is aligned with pressure toward the zone breach.
            aggressor_pressure = (1-2*pressure) if sign == 1 else (2*pressure-1)
            close_pos = (b.close-b.low)/(b.high-b.low) if sign == 1 else (b.high-b.close)/(b.high-b.low)
            if b.high == b.low:
                close_pos = .5
            outer = z.low if sign == 1 else z.high
            penetration = max(0,(outer-b.low) if sign == 1 else (b.high-outer))/max(atr[k],1e-12)
            reclaimed = b.close > z.low if sign == 1 else b.close < z.high
            in_zone = z.low <= b.close <= z.high
            opposite = [
                t for t in active
                if t.kind != z.kind and (
                    t.low > b.close if sign == 1 else t.high < b.close
                )
            ]
            if sign == 1:
                opposite.sort(key=lambda t:t.low)
                target = opposite[0].low if opposite else None
            else:
                opposite.sort(key=lambda t:-t.high)
                target = opposite[0].high if opposite else None
            stop = z.low-.15*atr[k] if sign == 1 else z.high+.15*atr[k]
            eid = f"{symbol}|{z.zone_id}|{b.ts+H1}"
            event = Contact(
                symbol,eid,b.ts+H1,b.ts+H1,z.zone_id,z.family,
                "long" if sign == 1 else "short",z.origin_at,z.available_at,
                z.low,z.high,atr[k],parent_time,prior_bias,
                (known_at-z.available_at)//H4,
                sum(x<=known_at for x in z.retests),
                b.volume/volume_mean,pressure,aggressor_pressure,
                close_pos,penetration,reclaimed,in_zone,b.close,stop,target,
            )
            contacts.append(event)
            labels.append(_label(event,one,i))
        for z in zones:
            if previous_contact.get(z.zone_id) and z.zone_id not in touched:
                previous_contact[z.zone_id] = False
        for zid in touched:
            previous_contact[zid] = True
    return contacts,labels


def _label(event: Contact, one: Sequence[FlowBar], i: int) -> LabeledEvent:
    """Future labels never enter recognition inputs; censor incomplete windows."""
    sign = 1 if event.side == "long" else -1
    # Coarse analytic cohort, not a presupposed validated entry.
    if event.penetration_atr4 > 0 and event.reclaimed_zone_at_close:
        cohort = "SWEEP_RECLAIM"
    elif event.closed_inside_zone:
        cohort = "TOUCH_INSIDE"
    else:
        cohort = "CONTACT_OTHER"
    # Next-hour open can occur at the contact's close. No trade is executed.
    if i+1 >= len(one):
        return LabeledEvent(event.event_id,event.symbol,event.side,cohort,None,"CENSORED",None,None,{}, {}, {},None)
    price = one[i+1].open
    future: dict = {}
    mfe: dict = {}
    mae: dict = {}
    maximum = max(HORIZONS)
    full = i+maximum<len(one)
    for horizon in HORIZONS:
        if i+horizon >= len(one):
            continue
        segment = one[i+1:i+horizon+1]
        if len(segment) != horizon:
            continue
        # horizon end: close of the horizon-th next fully closed 1H candle.
        future[str(horizon)] = sign*(segment[-1].close-price)/price*100
        mfe[str(horizon)] = max((x.high-price)/price*100 if sign == 1 else (price-x.low)/price*100 for x in segment)
        mae[str(horizon)] = min((x.low-price)/price*100 if sign == 1 else (price-x.high)/price*100 for x in segment)
    transfer_at = None
    # The label becomes known ONLY AFTER future confirmation closes.
    for j in range(i+1,min(i+4,len(one))):
        x=one[j]
        fraction=x.taker_buy/x.volume if x.volume else .5
        if sign*(x.close-event.contact_close)> .1*event.h4_atr_asof and (
            (fraction >= .52) if sign == 1 else (fraction <= .48)
        ):
            transfer_at=x.ts+H1
            break
    return LabeledEvent(
        event.event_id,event.symbol,event.side,cohort,
        one[i+maximum].ts+H1 if full else None,
        "LABELED" if full else "CENSORED",
        one[i+1].ts,price,future,mfe,mae,transfer_at,
    )

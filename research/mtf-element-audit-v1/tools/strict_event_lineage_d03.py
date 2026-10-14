#!/usr/bin/env python3
"""D03 — immutable, as-of causal event graph. No pattern or order execution.

Formal contract only: D03 cannot attest to whether a particular IDM, POI, BOS,
raid or VC label is visually/financially meaningful. Times are UTC epoch ms,
with known_at representing the earliest *verifiable* time, not an asserted
value we can independently verify from arbitrary supplied labels.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import hashlib, json


class D03Rejected(ValueError):
    def __init__(self, code, details=''):
        self.code = code
        super().__init__(code + (': '+details if details else ''))


def _time(v, field, optional=False):
    if v is None and optional: return
    if type(v) is not int or v < 0: raise D03Rejected('BAD_TIME', field)


def _str(v, field):
    if type(v) is not str or not v.strip() or len(v) > 255:
        raise D03Rejected('BAD_STRING', field)


@dataclass(frozen=True)
class CausalEvent:
    uid: str
    kind: str
    symbol: str
    venue: str
    market: str
    timeframe: str
    origin_open_ms: int
    origin_close_ms: int
    known_at_ms: int
    parent_uids: tuple[str, ...]
    evidence_uids: tuple[str, ...]
    decision_at_ms: Optional[int] = None
    order_at_ms: Optional[int] = None
    fill_at_ms: Optional[int] = None
    # Invalidation is a new event referring to an already known target; it
    # must never retroactively mutate the immutable target record.

    def __post_init__(self):
        for field in ('uid','kind','symbol','venue','market','timeframe'):
            _str(getattr(self,field), field)
        if self.kind not in {'SOURCE','POI','LIQUIDITY','TEST','RAID','VC','TRIGGER',
                             'IDM','BOS','REACTION','CONFIRMATION','INTENT','ORDER','FILL','INVALIDATION'}:
            raise D03Rejected('UNKNOWN_KIND')
        if self.market not in {'USDM_FUTURES','SPOT','COINM_FUTURES'}:
            raise D03Rejected('UNKNOWN_MARKET')
        for field in ('origin_open_ms','origin_close_ms','known_at_ms'):
            _time(getattr(self,field),field)
        for field in ('decision_at_ms','order_at_ms','fill_at_ms'):
            _time(getattr(self,field),field,optional=True)
        if self.origin_open_ms >= self.origin_close_ms:
            raise D03Rejected('BAD_ORIGIN_INTERVAL')
        if self.origin_close_ms > self.known_at_ms:
            raise D03Rejected('UNKNOWN_UNCLOSED_EVENT')
        if self.kind not in {'ORDER','FILL'} and self.decision_at_ms is not None and self.known_at_ms > self.decision_at_ms:
            raise D03Rejected('DECISION_BEFORE_KNOWN')
        if self.order_at_ms is not None and (self.decision_at_ms is None or self.order_at_ms < self.decision_at_ms):
            raise D03Rejected('ORDER_BEFORE_DECISION')
        if self.fill_at_ms is not None and (self.order_at_ms is None or self.fill_at_ms < self.order_at_ms):
            raise D03Rejected('FILL_BEFORE_ORDER')
        if type(self.parent_uids) is not tuple or type(self.evidence_uids) is not tuple:
            raise D03Rejected('MUTABLE_OR_INVALID_REFERENCES')
        for name, items in [('parent_uids',self.parent_uids),('evidence_uids',self.evidence_uids)]:
            if len(set(items)) != len(items):raise D03Rejected('DUPLICATE_REFERENCE', name)
            for x in items:_str(x,name)
        if self.uid in self.parent_uids: raise D03Rejected('SELF_PARENT')
        if not self.evidence_uids: raise D03Rejected('NO_EVIDENCE_REFERENCE')
        if self.kind == 'SOURCE' and self.parent_uids:
            raise D03Rejected('SOURCE_HAS_PARENTS')
        if self.kind != 'SOURCE' and not self.parent_uids:
            raise D03Rejected('ORPHAN_DERIVED_EVENT')
        if self.kind == 'INVALIDATION' and len(self.parent_uids) != 1:
            raise D03Rejected('INVALIDATION_TARGET_REQUIRED')
        if self.kind == 'INTENT' and self.decision_at_ms is None:
            raise D03Rejected('INTENT_NEEDS_DECISION_TIME')
        if self.kind == 'ORDER' and self.order_at_ms is None:
            raise D03Rejected('ORDER_NEEDS_ORDER_TIME')
        if self.kind == 'FILL' and self.fill_at_ms is None:
            raise D03Rejected('FILL_NEEDS_FILL_TIME')
        if self.kind == 'ORDER' and self.order_at_ms is not None and self.known_at_ms < self.order_at_ms:
            raise D03Rejected('ORDER_ACK_FUTURE_LEAK')
        if self.kind == 'FILL' and self.fill_at_ms is not None and self.known_at_ms < self.fill_at_ms:
            raise D03Rejected('FILL_ACK_FUTURE_LEAK')

    def as_record(self):
        return {k: (list(v) if isinstance(v,tuple) else v) for k,v in vars(self).items()}


class EventLedger:
    def __init__(self):
        self._events:dict[str,CausalEvent] = {}
        self._ordered:list[str] = []
        self._invalidated_at:dict[str,int] = {}

    def add(self, ev: CausalEvent):
        if not isinstance(ev,CausalEvent): raise D03Rejected('INVALID_EVENT_OBJECT')
        if ev.uid in self._events: raise D03Rejected('DUPLICATE_EVENT_UID')
        if self._ordered and ev.known_at_ms < self._events[self._ordered[-1]].known_at_ms:
            raise D03Rejected('RETROACTIVE_INSERTION')
        parents=[]
        for pid in ev.parent_uids:
            if pid not in self._events:raise D03Rejected('UNKNOWN_PARENT',pid)
            p=self._events[pid]
            if (p.symbol,p.venue,p.market)!=(ev.symbol,ev.venue,ev.market):
                raise D03Rejected('CROSS_INSTRUMENT_PARENT',pid)
            if p.known_at_ms>ev.known_at_ms:
                raise D03Rejected('PARENT_NOT_YET_KNOWN')
            # Check the entire ancestral chain. A valid old trigger cannot
            # resurrect a 4H POI invalidated after that trigger formed.
            if ev.kind != 'INVALIDATION' and not self._causally_active(pid,ev.known_at_ms):
                raise D03Rejected('PARENT_ANCESTRY_INVALIDATED',pid)
            if ev.kind not in {'ORDER','FILL'} and ev.decision_at_ms is not None and p.known_at_ms>ev.decision_at_ms:
                raise D03Rejected('PARENT_AFTER_DECISION')
            parents.append(p)
        if ev.kind == 'INVALIDATION':
            target=parents[0]
            if target.kind=='INVALIDATION':raise D03Rejected('INVALIDATION_OF_INVALIDATION')
            if target.uid in self._invalidated_at:raise D03Rejected('DUPLICATE_INVALIDATION')
            self._invalidated_at[target.uid]=ev.known_at_ms
        self._events[ev.uid]=ev
        self._ordered.append(ev.uid)
        return self

    def _causally_active(self,uid:str,at:int) -> bool:
        if self._invalidated_at.get(uid,2**63-1)<=at:return False
        return all(self._causally_active(pid,at) for pid in self._events[uid].parent_uids)

    def snapshot(self, as_of_ms:int, *, active_only=False) -> tuple[CausalEvent,...]:
        _time(as_of_ms,'as_of_ms')
        return tuple(self._events[k] for k in self._ordered
                     if self._events[k].known_at_ms<=as_of_ms
                     and (not active_only or self._causally_active(k,as_of_ms)))

    def ancestors(self, uid, *, as_of_ms:int):
        _time(as_of_ms,'as_of_ms')
        if uid not in self._events or self._events[uid].known_at_ms>as_of_ms:
            raise D03Rejected('CHILD_NOT_KNOWN_AS_OF')
        collected=set()
        def walk(x):
            for p in self._events[x].parent_uids:
                if self._events[p].known_at_ms>as_of_ms:
                    raise D03Rejected('FUTURE_PARENT')
                if p not in collected:
                    collected.add(p);walk(p)
        walk(uid)
        return tuple(self._events[k] for k in self._ordered if k in collected)

    def export(self):
        # Returned as new data; callers cannot mutate internal event objects.
        return [self._events[k].as_record() for k in self._ordered]

    def digest(self):
        raw=json.dumps(self.export(),sort_keys=True,separators=(',',':'),ensure_ascii=False)
        return hashlib.sha256(raw.encode()).hexdigest()

    @classmethod
    def replay(cls, rows):
        if type(rows) not in {list,tuple}: raise D03Rejected('BAD_REPLAY_INPUT')
        g=cls()
        for row in rows:
            if not isinstance(row,dict):raise D03Rejected('BAD_REPLAY_ROW')
            allowed=set(CausalEvent.__dataclass_fields__)
            if set(row)!=allowed:raise D03Rejected('REPLAY_SCHEMA_MISMATCH')
            data=dict(row)
            for field in ('parent_uids','evidence_uids'):
                if type(data[field]) is not list:raise D03Rejected('REPLAY_REF_SCHEMA')
                data[field]=tuple(data[field])
            g.add(CausalEvent(**data))
        return g

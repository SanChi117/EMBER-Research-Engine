"""Durable, read-only research-side order/position replay and risk-state store.

NO exchange gateway is available. Fills are only accepted when caller provides
explicit evidence; no OHLC approximation is silently turned into an actual fill.
"""
from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any,Mapping,Sequence
import json, sqlite3

from .accounting import RiskState, update_risk, CashEvent, replay_cash_events
from .market import OrderSnapshot, transition_order
from .types import finite,positive


class SQLiteResearchLedger:
    """Transactional, idempotent ledger; risk latch survives restarts.

    One process or many processes on the same SQLite file; durability relies
    on the host filesystem. NOT a substitute for exchange reconciliation.
    """
    def __init__(self,path:str|Path):
        self.path=str(path)
        self._init()

    def _connection(self):
        db=sqlite3.connect(self.path,timeout=15,isolation_level=None)
        db.execute('PRAGMA busy_timeout=15000')
        db.execute('PRAGMA journal_mode=WAL')
        db.execute('PRAGMA synchronous=FULL')
        return db

    def _init(self):
        with self._connection() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS research_cash (
                    account TEXT NOT NULL, symbol TEXT NOT NULL,side TEXT NOT NULL,
                    sequence INTEGER NOT NULL,event_id TEXT NOT NULL PRIMARY KEY,
                    payload TEXT NOT NULL, UNIQUE(account,symbol,side,sequence));
                CREATE TABLE IF NOT EXISTS research_risk (
                    account TEXT PRIMARY KEY, revision INTEGER NOT NULL, payload TEXT NOT NULL);
            ''')

    def record_cash(self, account:str, symbol:str, side:str, event:CashEvent)->str:
        if not account or not symbol or side not in ('long','short'):
            raise ValueError('invalid event identity')
        payload=json.dumps(asdict(event),sort_keys=True,allow_nan=False)
        with self._connection() as db:
            db.execute('BEGIN IMMEDIATE')
            old=db.execute('SELECT account,symbol,side,payload FROM research_cash WHERE event_id=?',(event.event_id,)).fetchone()
            if old is not None:
                if old!=(account,symbol,side,payload):
                    raise ValueError('same event_id has conflicting payload')
                db.execute('COMMIT')
                return 'DUPLICATE_SAFE'
            db.execute('INSERT INTO research_cash VALUES(?,?,?,?,?,?)',
                       (account,symbol,side,event.sequence,event.event_id,payload))
            db.execute('COMMIT')
        return 'RECORDED'

    def position(self, account:str, symbol:str, side:str):
        with self._connection() as db:
            rows=db.execute('SELECT payload FROM research_cash WHERE account=? AND symbol=? AND side=? ORDER BY sequence',(account,symbol,side)).fetchall()
        return replay_cash_events(symbol,side,[CashEvent(**json.loads(row[0])) for row in rows])

    def set_risk_if_version(self, account:str, state:RiskState, *, expected_revision:int|None)->int:
        if not account:
            raise ValueError('missing account')
        newpayload=json.dumps(asdict(state),sort_keys=True,allow_nan=False)
        with self._connection() as db:
            db.execute('BEGIN IMMEDIATE')
            old=db.execute('SELECT revision,payload FROM research_risk WHERE account=?',(account,)).fetchone()
            previous=old[0] if old else None
            if previous!=expected_revision:
                raise ValueError('concurrent risk write: revision changed')
            if old and json.loads(old[1]).get('halted') and not state.halted:
                raise ValueError('risk latch cannot be reset by normal update')
            newversion=0 if previous is None else previous+1
            db.execute('INSERT INTO research_risk(account,revision,payload) VALUES(?,?,?) '
                       'ON CONFLICT(account) DO UPDATE SET revision=excluded.revision,payload=excluded.payload',
                       (account,newversion,newpayload))
            db.execute('COMMIT')
            return newversion

    def risk(self,account:str)->tuple[int,RiskState]|None:
        with self._connection() as db:
            row=db.execute('SELECT revision,payload FROM research_risk WHERE account=?',(account,)).fetchone()
        if row is None:
            return None
        return row[0],RiskState(**json.loads(row[1]))

    def post_risk(self,account:str,pnl_usdt:float,*,day:str,week:str,
                  daily_limit:float,weekly_limit:float,max_losses:int)->tuple[int,RiskState]:
        """Atomic CAS update, rejects missing initialized state."""
        old=self.risk(account)
        if old is None:
            raise ValueError('initialize risk state before recording PnL')
        v,s=old
        updated=update_risk(s,pnl_usdt,day=day,week=week,
                            daily_limit=daily_limit,weekly_limit=weekly_limit,max_losses=max_losses)
        nv=self.set_risk_if_version(account,updated,expected_revision=v)
        return nv,updated


def resolve_order_replay(initial:OrderSnapshot,receipts:Sequence[Mapping[str,Any]])->dict[str,Any]:
    """Z09/Z10: distinguish observed fills from price-touch-only guesses."""
    current=initial
    seen=set()
    for receipt in sorted(receipts,key=lambda r:(r['received_at'],r['event_id'])):
        eid=receipt['event_id']
        if eid in seen:
            raise ValueError('duplicate receipt identifier')
        seen.add(eid)
        if receipt.get('origin')!='exchange_observed':
            raise ValueError('fill receipt not from observed exchange source')
        current=transition_order(current,receipt['kind'],receipt['received_at'],receipt.get('quantity',0.0))
    return {'order':current,'receipt_ids':sorted(seen),'source':'exchange_observed'}


def bar_bracket_uncertainty(candles,side:str,stop:float,target:float)->dict[str,Any]:
    """Z09: best/worst outcome envelope, explicitly unresolved ambiguous bars."""
    from .market import classify_bracket_bar
    outcomes=[classify_bracket_bar(bar,side,stop,target).value for bar in candles]
    first=next(((i,v) for i,v in enumerate(outcomes) if v!='NEITHER'),None)
    if first is None:
        return {'outcome':'OPEN','best':'OPEN','worst':'OPEN','first_bar':None}
    i,state=first
    if state=='AMBIGUOUS':
        return {'outcome':'AMBIGUOUS','best':'TARGET','worst':'STOP','first_bar':i}
    return {'outcome':state,'best':state,'worst':state,'first_bar':i}

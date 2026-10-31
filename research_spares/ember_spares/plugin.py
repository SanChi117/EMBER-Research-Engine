"""Single-call, fail-closed adapter for every EMBER spare part.

No dependency on EMBER/SMOKE internals, no exchange credentials, trading, HTTP,
background execution, dynamic user-defined code, or strategy parameter tuning.

``invoke('Z09', {'bar': {...}, 'side': 'long', 'stop': 96, 'target': 104})``
returns a JSON-compatible value. Callers can pass Binance kline arrays directly
for Candle arguments. All adapter errors fail closed; never fabricate fills.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import fields, is_dataclass
from enum import Enum
from importlib import import_module
from inspect import Parameter, signature
import base64
import json
from math import isfinite
from pathlib import Path
from types import UnionType
from typing import Any, Union, get_args, get_origin, get_type_hints

from .registry import REGISTRY, get_component
from .types import Candle, Evidence

_ALLOWED_MODULES = frozenset({'market', 'accounting', 'signals', 'structure', 'research', 'extra', 'advanced', 'operations', 'workflow', 'adapters'})
# Additional algorithms belong to existing Z families; the 37 required IDs stay stable.
_EXTENSIONS = {
    'Z15.patterns': ('extra', 'detect_patterns'),
    'Z19.ott': ('extra', 'ott_line'),
    'Z19.var': ('extra', 'efficiency_weighted_ema'),
    'Z27.predict_linear': ('extra', 'predict_verified_linear'),
    'Z30.holdout_gate': ('extra', 'check_train_holdout'),
    'Z01.signal_frame': ('advanced', 'historical_signal_frame'),
    'Z02.liquidation_boundary': ('advanced', 'liquidation_boundary'),
    'Z03.depth': ('advanced', 'orderbook_depth'),
    'Z03.quote_fill': ('advanced', 'quote_fill'),
    'Z04.parity': ('advanced', 'full_trace_parity'),
    'Z05.cash_ledger': ('advanced', 'two_leg_cash_ledger'),
    'Z07.correlated_gate': ('advanced', 'correlated_risk_gate'),
    'Z09.bracket_uncertainty': ('operations', 'bar_bracket_uncertainty'),
    'Z10.replay': ('advanced', 'portfolio_replay'),
    'Z11.history': ('advanced', 'progress_zone_history'),
    'Z14.compression': ('advanced', 'compression_breakout'),
    'Z17.failure_exit': ('advanced', 'failure_exit'),
    'Z20.funding': ('advanced', 'funding_pressure'),
    'Z21.oi': ('advanced', 'oi_signal'),
    'Z22.taker_series': ('advanced', 'taker_series'),
    'Z24.basket': ('advanced', 'basket_orders'),
    'Z25.pair_diagnostics': ('advanced', 'pair_diagnostics'),
    'Z26.dislocation': ('advanced', 'dislocation_plan'),
    'Z28.dual_entry': ('advanced', 'dual_entry_risk'),
    'Z30.bootstrap': ('advanced', 'bootstrap_mean_ci'),
    'Z31.regimes': ('advanced', 'attribution_by_regime'),
    'Z32.scan_source': ('advanced', 'review_source_for_lookahead'),
    'Z34.impact_envelope': ('advanced', 'volume_impact_envelope'),
    'Z35.preregistered': ('advanced', 'session_preregistered'),
    'Z37.with_addons': ('advanced', 'risk_with_addons'),
    'Z00.bundle': ('workflow', 'calculate_indicators'),
    'Z38.parity_exports': ('adapters', 'parity_from_exports'),
    'Z38.normalize_original': ('adapters', 'normalized_signal_rows'),
    'Z31.trade_exports': ('adapters', 'trade_report_rows'),
}

_CALLABLES: dict[str, Any] = {}


class SpareInputError(ValueError):
    """Invalid source data, missing argument, or unsafe time assumption."""


def _resolve(component_id: str):
    if component_id in _EXTENSIONS:
        module, entrypoint = _EXTENSIONS[component_id]
        metadata = type('Entry', (), {'module':module,'entrypoint':entrypoint})
    else:
        metadata = get_component(component_id)
    if metadata.module not in _ALLOWED_MODULES:
        raise SpareInputError('unknown code module')
    if component_id not in _CALLABLES:
        fn = getattr(import_module(f'.{metadata.module}', 'ember_spares'), metadata.entrypoint)
        _CALLABLES[component_id] = fn
    return _CALLABLES[component_id]


def _decode(value: Any, hint: Any) -> Any:
    if hint is Any or hint is Parameter.empty:
        return value
    if value is None:
        return None
    origin = get_origin(hint)
    args = get_args(hint)
    if origin in (Union, UnionType):
        alternatives = [a for a in args if a is not type(None)]
        for alternative in alternatives:
            try:
                return _decode(value, alternative)
            except SpareInputError:
                continue
        raise SpareInputError('no union alternative accepted')
    if hint is bytes:
        if not isinstance(value, str) or not value.startswith('base64:'):
            raise SpareInputError('binary model artifact must use base64: prefix')
        try:
            return base64.b64decode(value[7:], validate=True)
        except (ValueError, base64.binascii.Error) as exc:
            raise SpareInputError('invalid base64 artifact') from exc
    if hint is Path:
        if not isinstance(value, str):
            raise SpareInputError('path must be text')
        return Path(value)
    if hint in (str, int, float, bool):
        if hint in (int, float) and isinstance(value, (int, float)) and not isfinite(value):
            raise SpareInputError('nonfinite numeric input')
        if not isinstance(value, hint) or (hint in (int, float) and isinstance(value, bool)):
            if hint is float and isinstance(value, int) and not isinstance(value, bool):
                return float(value)
            raise SpareInputError(f'expected {hint.__name__}, got {type(value).__name__}')
        return value
    if isinstance(hint, type) and issubclass(hint, Enum):
        try:
            return hint(value)
        except ValueError as exc:
            raise SpareInputError('invalid enum value') from exc
    if isinstance(hint, type) and is_dataclass(hint):
        if hint is Candle and isinstance(value, (list, tuple)):
            from .binance import parse_kline
            return parse_kline(value)
        if not isinstance(value, Mapping):
            raise SpareInputError(f'expected object for {hint.__name__}')
        allowed = {field.name for field in fields(hint)}
        extra = set(value) - allowed
        if extra:
            raise SpareInputError(f'unknown {hint.__name__} fields: {sorted(extra)}')
        fieldtypes = get_type_hints(hint)
        return hint(**{k: _decode(v, fieldtypes[k]) for k, v in value.items()})
    if origin is tuple:
        if not isinstance(value, (list, tuple)):
            raise SpareInputError('tuple expected')
        if len(args) == 2 and args[1] is Ellipsis:
            return tuple(_decode(item, args[0]) for item in value)
        if len(value) != len(args):
            raise SpareInputError('tuple length mismatch')
        return tuple(_decode(item, a) for item, a in zip(value, args))
    if origin in (list, Sequence, Iterable):
        if not isinstance(value, (list, tuple)):
            raise SpareInputError('list expected')
        return [_decode(item, args[0]) for item in value] if args else list(value)
    if origin in (dict, Mapping):
        if not isinstance(value, Mapping):
            raise SpareInputError('mapping expected')
        return {_decode(k, args[0]): _decode(v, args[1]) for k, v in value.items()} if len(args) == 2 else dict(value)
    # Unknown annotations are never turned into executable objects.
    raise SpareInputError(f'unsupported type annotation: {hint!r}')


def _check_time(value: Any, decision_at: int) -> None:
    """Fail closed if any OHLCV or L1 Book was unavailable at decision time.

    Z01 as-of Evidence intentionally may contain future events: filtering is the
    function's job; other components must receive prefiltered market snapshots.
    """
    from .market import Book
    if isinstance(value, (Candle, Book)) and value.available_at > decision_at:
        raise SpareInputError('LOOKAHEAD: market data was unavailable at decision_at')
    if is_dataclass(value) and not isinstance(value, (Candle, Book, Evidence)):
        for field in fields(value):
            _check_time(getattr(value, field.name), decision_at)
    if isinstance(value, Mapping):
        for child in value.values():
            _check_time(child, decision_at)
    elif isinstance(value, (list, tuple)):
        for child in value:
            _check_time(child, decision_at)


def _jsonify(value: Any) -> Any:
    if is_dataclass(value):
        return {f.name: _jsonify(getattr(value, f.name)) for f in fields(value)}
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        return {str(k): _jsonify(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_jsonify(v) for v in value]
    if isinstance(value, float) and not isfinite(value):
        raise SpareInputError('nonfinite result; cannot serialize honestly')
    return value


def invoke(component_id: str, payload: Mapping[str, Any], *, decision_at: int | None = None) -> Any:
    """Run any registered component with JSON data, return JSON-ready output.

    ``decision_at`` is an optional, explicit epoch-second cutoff. When passed,
    closed market data are checked before the actual component is called.
    No function may secretly load market data or place an order.
    """
    if not isinstance(payload, Mapping):
        raise SpareInputError('payload must be a JSON object')
    try:
        fn = _resolve(component_id)
        params = signature(fn).parameters
        types = get_type_hints(fn)
        unknown = set(payload) - set(params)
        if unknown:
            raise SpareInputError(f'unknown arguments for {component_id}: {sorted(unknown)}')
        kwargs = {k: _decode(v, types.get(k, Parameter.empty)) for k, v in payload.items()}
        if decision_at is not None:
            if not isinstance(decision_at, int) or isinstance(decision_at, bool) or decision_at < 0:
                raise SpareInputError('decision_at must be a nonnegative epoch-second integer')
            if 'decision_at' in params and 'decision_at' not in kwargs:
                kwargs['decision_at'] = decision_at
            if 'at' in params and 'at' not in kwargs and component_id in ('Z27','Z27.predict_linear'):
                kwargs['at'] = decision_at
            _check_time(kwargs, decision_at)
        bound = signature(fn).bind(**kwargs)
        bound.apply_defaults()
        return _jsonify(fn(*bound.args, **bound.kwargs))
    except KeyError as exc:
        raise SpareInputError(f'unknown component: {component_id}') from exc
    except (TypeError, AssertionError) as exc:
        raise SpareInputError(f'bad {component_id} arguments: {exc}') from exc


def manifest() -> list[dict[str, str]]:
    entries = [dict(id=c.id, module=c.module, entrypoint=c.entrypoint, readiness=c.readiness, notes=c.notes)
            for c in REGISTRY]
    entries.extend(dict(id=k,module=m,entrypoint=f,readiness='OFFLINE_RESEARCH',notes='Additional implementation for existing family')
                   for k,(m,f) in _EXTENSIONS.items())
    return entries


def main(argv: list[str] | None = None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description='Offline EMBER spare parts; NO exchange orders')
    parser.add_argument('component', help='Z01-Z38, excluding already existing Z12; or "list"')
    parser.add_argument('input', nargs='?', help='JSON path, or - for stdin')
    parser.add_argument('--decision-at', type=int, default=None, help='UTC epoch seconds')
    args = parser.parse_args(argv)
    if args.component == 'list':
        print(json.dumps(manifest(), ensure_ascii=False, indent=2)); return 0
    if not args.input:
        parser.error('input JSON path required')
    import sys
    source = sys.stdin.read() if args.input == '-' else Path(args.input).read_text(encoding='utf-8')
    try:
        payload = json.loads(source)
        result = invoke(args.component, payload, decision_at=args.decision_at)
    except (ValueError, TypeError) as exc:
        print(json.dumps({'ok': False, 'component': args.component, 'error': str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps({'ok': True, 'component': args.component, 'result': result}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

"""D05 schema-only evidence gate. NEVER declares academic semantics approved.

Source-linked chart cases require immutable raw numeric image, dated source,
actual event bounds, timing and independently annotated geometry. Validation
only checks missing/inconsistent fields; truth must be separately reviewed.
"""
from __future__ import annotations
from datetime import datetime, timezone
import re

SHA=re.compile(r'[0-9a-f]{64}\Z')
MODELS={'R01_IMB_SNR','R02_IDM','R03_RAID_BOS','R04_POI_TRIGGER_VC'}
TFS={'1w','1d','4h','1h','15m','5m','3m'}

class D05Rejected(ValueError):pass

def _datetime_utc(v):
    if not isinstance(v,str):raise D05Rejected('MISSING_TIME')
    try:d=datetime.fromisoformat(v.replace('Z','+00:00'))
    except ValueError as exc:raise D05Rejected('BAD_TIME') from exc
    if d.tzinfo is None or d.utcoffset().total_seconds()!=0:
        raise D05Rejected('NON_UTC_OR_NAIVE_TIME')
    return d

def validate_chart_case(case):
    """Returns SCHEMA_VALID_NEEDS_VISUAL_REVIEW, never semantic approval."""
    if not isinstance(case,dict):raise D05Rejected('NOT_OBJECT')
    required={'case_id','course_uri','course_section','raw_chart_uri',
              'raw_chart_sha256','raw_chart_kind','symbol','market_type',
              'model_id','side','tf','event_origin_at','event_known_at',
              'decision_as_of','zone_low','zone_high','event_price',
              'annotated_object','case_kind','rule_reference',
              'independent_review_status','negative_reason'}
    if not required<=set(case):
        raise D05Rejected('MISSING_SOURCE_OR_GEOMETRY_FIELDS')
    if case['raw_chart_kind']!='ORIGINAL_NUMERIC_AUTHOR_CHART':
        raise D05Rejected('SCHEMATIC_SCREENSHOT_NOT_GOLDEN')
    if not isinstance(case['raw_chart_sha256'],str) or not SHA.fullmatch(case['raw_chart_sha256']):
        raise D05Rejected('UNVERIFIABLE_IMAGE_SHA')
    if not all(isinstance(case[k],str) and case[k].strip()
               for k in ('case_id','course_uri','course_section',
                         'raw_chart_uri','symbol','annotated_object','rule_reference')):
        raise D05Rejected('MISSING_ATTRIBUTION')
    if case['market_type']!='FUTURES_UM':
        raise D05Rejected('NOT_FROZEN_FUTURES_MARKET')
    if case['model_id'] not in MODELS or case['tf'] not in TFS or case['side'] not in {'LONG','SHORT'}:
        raise D05Rejected('INVALID_ROUTE_TF_OR_SIDE')
    if case['case_kind'] not in {'POSITIVE','NEGATIVE'}:
        raise D05Rejected('UNSPECIFIED_POSITIVE_OR_NEGATIVE')
    if case['case_kind']=='NEGATIVE' and not case['negative_reason']:
        raise D05Rejected('NEGATIVE_WITHOUT_REASON')
    try:
        lo,hi,price=(*(float(case[x]) for x in ('zone_low','zone_high','event_price')),)
    except (ValueError,TypeError) as exc:raise D05Rejected('BAD_PRICE') from exc
    from math import isfinite
    if not all(isfinite(v) and v>0 for v in (lo,hi,price)) or lo>=hi:
        raise D05Rejected('INVALID_ZONE_GEOMETRY')
    t0=_datetime_utc(case['event_origin_at'])
    t1=_datetime_utc(case['event_known_at'])
    t2=_datetime_utc(case['decision_as_of'])
    if not t0<=t1<=t2:
        raise D05Rejected('LOOKAHEAD_OR_INVALID_CAUSAL_TIME')
    if case['independent_review_status']!='PENDING':
        raise D05Rejected('SELF_APPROVED_OR_UNREVIEWED_CASE')
    return 'SCHEMA_VALID_NEEDS_INDEPENDENT_VISUAL_REVIEW'

def summarize_candidates(manifest):
    if not isinstance(manifest,dict) or 'candidates' not in manifest:
        raise D05Rejected('BAD_CANDIDATE_MANIFEST')
    if manifest.get('visual_course_cases_accepted')!=0:
        raise D05Rejected('UNPROVEN_VISUAL_ACCEPTANCE')
    for candidate in manifest['candidates']:
        if candidate['status'] not in ('NEEDS_NUMERIC_CHART_SOURCE','SCHEMATIC_ONLY_NOT_GOLDEN'):
            raise D05Rejected('PROMOTED_WITHOUT_INDEPENDENT_LABEL')
        if not SHA.fullmatch(candidate['sha256']):
            raise D05Rejected('INVALID_SCREENSHOT_HASH')
    return {'screen_captures':len(manifest['candidates']),
            'numeric_golden_cases_accepted':0,
            'gate':'NO_TRADING_SEMANTICS_APPROVED'}

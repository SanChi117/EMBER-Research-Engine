"""B1/C61 complete academic prerequisite contract (research only).

Primary owner lessons checked 2026-10-25:
POI.txt / Rejection Block.txt / Order Flow.txt / Strong High & Low.txt /
Fair Value Gap Imbalance.txt / 2. Entry by IMB & SNR.txt /
3. Entry by Inducement [IDM].txt / previous day PDH PDL lesson.

Academic constraints: HTF context -> typed POI -> FIRST VALID test (except
Route B may place LIMIT at known IDM ahead of test) -> liquidity or
inefficiency contact -> subsequent 4H/1H/lower TF VC POI or BOS -> StrongHL.
RB requires liquidity raid or proper IMB work. The exact chart-specific
price/candle author labels ARE NOT provided by these text files, therefore
this contract can check chronology and prerequisites ONLY.

Neither synthetics nor source geometry may approve positions. Any claim of
approved author golden, 4H/1H POI, StrongHL, SL, TP, entry is fail-closed.
"""
from dataclasses import dataclass
from decimal import Decimal
import re

DAY=86400000
THREE=180000
RAW=re.compile(r"[a-f0-9]{64}:[0-9]{13}\Z")
TYPES=("IMB","SNR","RB","LIQUIDITY")
SRC_STATES=("NO_CLOSED_PRIOR_DAY","FIRST_SOURCE_VISIT_ABSENT",
            "FIRST_SOURCE_VISIT_ONLY","REPEATED_SOURCE_VISITS",
            "FINAL_VISIT_RIGHT_CENSORED")
REASONS=(
  "COURSE_DAILY_OR_4H_CONTEXT_NOT_AUTHOR_SELECTED",
  "COURSE_TYPED_POI_IS_NOT_SOURCE_IMB_ONLY",
  "COURSE_FIRST_VALID_TEST_NOT_AUTHOR_VERIFIED",
  "COURSE_CONTACT_LIQUIDITY_OR_INEFFICIENCY_NOT_VERIFIED",
  "COURSE_REACTION_VC_POI_OR_BOS_NOT_AUTHOR_VERIFIED",
  "COURSE_STRONG_HIGH_LOW_NOT_AUTHOR_VERIFIED",
  "COURSE_FTA_AND_EXECUTION_NOT_VERIFIED")
@dataclass(frozen=True)
class AcademicPoiCase:
    route:str
    source_kind:str
    source_tf:str
    source_created_known_ms:int
    parent_context_known_ms:int|None
    parent_context_typed:str|None
    parent_context_author_verified:bool
    original_first_contact_known_ms:int|None
    first_valid_test_author_verified:bool
    liquidity_or_inefficiency_contact_known_ms:int|None
    liquidity_or_inefficiency_kind:str|None
    confirming_event_kind:str|None
    confirming_event_known_ms:int|None
    confirming_tf:str|None
    strong_extreme_kind:str|None
    stronghl_author_verified:bool
    source_visited_again:bool
    rb_raid_or_imb_overlap_author_verified:bool=False
    direct_idm_known_ms:int|None=None
    author_price_golden:bool=False
    author_entry_approved:bool=False
    orders:tuple=()
    trades:tuple=()

@dataclass(frozen=True)
class AcademicPoiVerdict:
    text_preconditions_consistent:bool
    blockers:tuple[str,...]
    author_verified_typed_poi:bool=False
    author_verified_first_valid_poi_test:bool=False
    author_verified_stronghl:bool=False
    author_verified_entry:bool=False
    orders:tuple=()
    trades:tuple=()
    readiness:str="NOT_TRADE_READY"

def _ms(x):return type(x) is int and x>=0
def _when(x):return x is None or _ms(x)

def academic_poi_lifecycle_contract(x):
    if not isinstance(x,AcademicPoiCase):
        raise ValueError("C61_NOT_AN_AUTHENTIC_ACADEMIC_POI_CASE")
    if x.author_price_golden or x.author_entry_approved or x.orders or x.trades:
        raise ValueError("C61_FORGED_AUTHOR_PRICE_GOLDEN_OR_ORDER")
    if (x.route not in ("A_4H_TRIGGER_15M_VC","A_4H_NO_TRIGGER_1H_VC",
                       "B_4H_VC_1H_IDM","B_1H_VC_15M_IDM","C_RAID_BOS")
        or x.source_kind not in TYPES or x.source_tf not in ("1D","4H","1H")
        or not _ms(x.source_created_known_ms)
        or any(not _when(v) for v in (
            x.parent_context_known_ms,x.original_first_contact_known_ms,
            x.liquidity_or_inefficiency_contact_known_ms,
            x.confirming_event_known_ms,x.direct_idm_known_ms))):
        raise ValueError("C61_INVALID_COURSE_EVENT_OR_TIMESTAMP")
    errors=[]
    def must(ok,code):
        if not ok:errors.append(code)
    must(x.parent_context_author_verified and x.parent_context_typed in TYPES
        and x.parent_context_known_ms is not None and
        x.parent_context_known_ms<=x.source_created_known_ms,
        "C61_UNVERIFIED_PRIOR_HTF_CONTEXT")
    must(x.source_created_known_ms<=x.original_first_contact_known_ms
        if x.original_first_contact_known_ms is not None else False,
        "C61_UNVERIFIED_FIRST_SOURCE_CONTACT")
    is_idm=x.route.startswith("B_")
    # The owner explicitly allows direct IDM limit BEFORE a first POI test;
    # forbid imposing Route A first-test condition on direct Route B.
    if is_idm:
        must(x.direct_idm_known_ms is not None and
             x.direct_idm_known_ms>=x.source_created_known_ms,
             "C61_ROUTE_B_IDM_NOT_PROVEN")
    else:
        must(x.first_valid_test_author_verified and
             x.original_first_contact_known_ms is not None and
             not x.source_visited_again,
             "C61_NOT_FIRST_VALID_POI_TEST")
    must(x.liquidity_or_inefficiency_kind in ("LIQUIDITY","INEFFICIENCY") and
         x.liquidity_or_inefficiency_contact_known_ms is not None and
         x.liquidity_or_inefficiency_contact_known_ms>=x.source_created_known_ms,
         "C61_LIQUIDITY_INEFFICIENCY_CONTACT_UNVERIFIED")
    must(x.confirming_event_kind in ("VC_POI","BOS") and
         x.confirming_event_known_ms is not None and
         x.liquidity_or_inefficiency_contact_known_ms is not None and
         x.confirming_event_known_ms>x.liquidity_or_inefficiency_contact_known_ms and
         x.confirming_tf in ("4H","1H","15M","5M","3M"),
         "C61_STRONGHL_VC_BOS_WRONG_CHRONOLOGY")
    must(x.strong_extreme_kind in ("STRONG_HIGH","STRONG_LOW") and
         x.stronghl_author_verified,
         "C61_BARE_PIVOT_NOT_STRONGHL")
    if x.source_kind=="RB":
        must(x.rb_raid_or_imb_overlap_author_verified,
             "C61_RB_REQUIRES_RAID_OR_IMB_WORK")
    if is_idm:
        must(x.confirming_event_kind is not None,
             "C61_IDM_REQUIRES_PREEXISTING_VC_CONTEXT")
    return AcademicPoiVerdict(not errors,tuple(dict.fromkeys(errors)))

@dataclass(frozen=True)
class SourceDayContext:
    symbol:str
    source_4h_known_ms:int
    latest_prior_closed_native1d_id:str|None
    latest_prior_day_known_ms:int|None
    prior_day_high:str|None
    prior_day_low:str|None
    source_only:bool=True
    author_daily_POI_selected:bool=False
    author_daily_context_approved:bool=False
    readiness:str="NOT_TRADE_READY"

def last_closed_original_day_before_zone(days,*,symbol,zone_known_ms,as_of_ms):
    """Native 1d provenance and strict as-of; never treat day high/low as POI."""
    from c16_c08_monthly_daily_htf_lineage import NativeKline,SEPT_START
    if (not isinstance(days,tuple) or not days or
        type(zone_known_ms) is not int or type(as_of_ms) is not int or
        zone_known_ms>as_of_ms or zone_known_ms%THREE):
        raise ValueError("C61_NO_TRUSTED_ORIGINAL_NATIVE_1D_PREFIX")
    chosen=None
    for i,z in enumerate(days):
        if (not isinstance(z,NativeKline) or z.symbol!=symbol or z.tf!="1d"
            or type(z.start_ms) is not int
            or z.start_ms!=SEPT_START+i*DAY
            or z.known_at_ms!=z.start_ms+DAY
            or z.known_at_ms>as_of_ms
            or z.origin_zip_sha256!=z.origin_raw_row_id.split(":")[0]
            or not RAW.fullmatch(z.origin_raw_row_id)
            or int(z.origin_raw_row_id.rsplit(":",1)[1])!=z.start_ms
            or not all(isinstance(v,Decimal) and v.is_finite()
                       for v in (z.open,z.high,z.low,z.close,z.volume))
            or not(0<z.low<=min(z.open,z.close)<=max(z.open,z.close)<=z.high
                   and z.volume>=0)):
            raise ValueError("C61_FORGED_OR_UNCLOSED_NATIVE_1D_HISTORY")
        if z.known_at_ms<=zone_known_ms:chosen=z
    return SourceDayContext(symbol,zone_known_ms,
        chosen.origin_raw_row_id if chosen else None,
        chosen.known_at_ms if chosen else None,
        str(chosen.high) if chosen else None,
        str(chosen.low) if chosen else None)

def join_source_poi_context(c46obs,c47obs,c59obs,c60obs,prior):
    """Join FOUR already independently anchored C46/C47/C59/C60 sources.
    This protects identity and time; deliberately no author promotion.
    """
    if not all(isinstance(x,dict) for x in (c46obs,c47obs,c59obs,c60obs)):
        raise ValueError("C61_UNTRUSTED_C46_C47_C59_C60_LINEAGE")
    c=c46obs.get("candidate")
    if not isinstance(c,dict) or not isinstance(prior,SourceDayContext):
        raise ValueError("C61_MISSING_PARENT_COURSE_SOURCE")
    if (c.get("source_status")!="C46_NATIVE_4H_CLASSIC_IMB_GEOMETRY_ONLY" or
        c.get("author_poi_certified") or
        c46obs.get("academic_poi_test_certified") or
        c46obs.get("academic_volume_confirmation_certified") or
        c47obs.get("course_typed_poi_approved") or
        c47obs.get("course_first_valid_test_approved") or
        c47obs.get("course_volume_confirmation_approved") or
        c60obs.get("course_author_valid_first_test") or
        c60obs.get("course_author_StrongHL") or
        c60obs.get("academic_trade_signal") or
        c59obs.get("course_author_strongHL") or
        c59obs.get("course_author_first_valid_test") or
        c59obs.get("course_author_routeA_trigger") or
        c59obs.get("course_author_routeB_IDM") or
        prior.author_daily_POI_selected or prior.author_daily_context_approved):
        raise ValueError("C61_SOURCE_PRETENDS_AUTHOR_APPROVAL")
    for x in (c,c46obs,c47obs,c59obs,c60obs):
        if (x.get("orders") or x.get("trades")
            or x.get("readiness","NOT_TRADE_READY")!="NOT_TRADE_READY"):
            raise ValueError("C61_TRADE_FORGED_IN_RESEARCH_SOURCE")
    if (not isinstance(c60obs.get("all_closed_3m_visit_episodes"),list)
        or c60obs.get("source_4h_known_ms") is not None
        or c.get("fully_known_ms")!=prior.source_4h_known_ms
        or c.get("fully_known_ms")!=c60obs.get("zone_known_ms")
        or c.get("fully_known_ms")!=c47obs.get("original4h_zone_known_ms")
        or c.get("fully_known_ms")!=c59obs.get("original_4h_known_ms")
        or c.get("side")!=c60obs.get("technical_4h_zone_side")
        or c.get("side")!=c47obs.get("original4h_zone_side")
        or c.get("side")!=c59obs.get("original_4h_side")
        or c.get("three_original_source_first_native3m_ids")!=
           c47obs.get("original4h_zone_first_raw3m_ids")
        or c.get("three_original_source_first_native3m_ids")!=
           c59obs.get("original_4h_first_native3m_ids")
        or tuple(c.get("three_original_source_first_native3m_ids",()))!=
           tuple(c60obs.get("original_4h_first_row_ids",()))
        or c46obs.get("first_contact_original3m_id")!=c60obs.get("first_contact_original3m_id")
        or c46obs.get("first_contact_original3m_id")!=c59obs.get("first_original3m_contact_id")
        or c46obs.get("first_contact_original3m_id")!=c47obs.get("original4h_first_contact_native3m_id")
        or str(c.get("bottom"))!=str(c60obs.get("zone_bottom"))
        or str(c.get("top"))!=str(c60obs.get("zone_top"))):
        raise ValueError("C61_CROSS_SOURCE_PARENT_ID_OR_PRICE_MISMATCH")
    visits=c60obs["all_closed_3m_visit_episodes"]
    if (visits and (visits[0].get("first_original3m_raw_id")!=c46obs.get("first_contact_original3m_id")
                   or visits[0].get("first_bar_known_ms")!=c46obs.get("first_contact_closed_known_ms"))
        or not visits and c46obs.get("first_contact_original3m_id") is not None
        or len(visits)-1!=c60obs.get("repeated_distinct_returns_after_first",0) if visits else
        c60obs.get("repeated_distinct_returns_after_first",0)!=0):
        raise ValueError("C61_FIRST_VISIT_AND_REVISIT_LINEAGE_DRIFT")
    if (c59obs.get("post_contact_1h_imb_known_ms") is not None and
        c59obs["post_contact_1h_imb_known_ms"]<=c46obs["first_contact_closed_known_ms"]):
        raise ValueError("C61_POST_CONTACT_REACTION_PRECEDES_CONTACT")
    status=("NO_OBSERVED_FIRST_SOURCE_CONTACT" if not visits else
            "REVISITED_TECHNICAL_ZONE" if len(visits)>1 else
            "ONE_TECHNICAL_SOURCE_VISIT")
    return {
      "symbol":prior.symbol,"source_parent_known_ms":c["fully_known_ms"],
      "original_first3m_touch_id":c46obs.get("first_contact_original3m_id"),
      "original_prior_day_raw_id":prior.latest_prior_closed_native1d_id,
      "source_previous_closed_day_high":prior.prior_day_high,
      "source_previous_closed_day_low":prior.prior_day_low,
      "source_4h_technical_type":"IMB",
      "first_source_visit_episode_count":len(visits),
      "source_visit_status":status,
      "last_source_visit_right_censored":bool(visits and visits[-1].get("still_inside_at_source_end")),
      "later_same_side_1h_technical_imb_known_ms":c59obs.get("post_contact_1h_imb_known_ms"),
      "c59_routeA_1h_imb_geometry_status":c59obs.get("status"),
      "author_daily_context":False,
      "author_typed_4h_poi":False,
      "author_first_valid_test":False,
      "author_reaction_vc_or_bos":False,
      "author_strongHL":False,
      "course_fully_verified":False,
      "blocking_reasons":REASONS,
      "orders":0,"trades":0,"readiness":"NOT_TRADE_READY"}

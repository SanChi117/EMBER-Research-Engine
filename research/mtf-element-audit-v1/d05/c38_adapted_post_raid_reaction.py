"""C38 source-native adapted post-1H-confirmation Reaction predicates.

Three explicit ADAPTED research hypotheses, never author positive goldens.
For every C37 adapted first closed-break, inspect ONLY native original 3m
bars fully closed after 1H raid confirmation and BEFORE the beginning
of that BOS break bar. A reaction is not a fill, order or complete trade.

The course may consider an earlier reaction DURING the raid hour; these
post-confirmation rules intentionally form an adapted-only comparison.
"""
from dataclasses import dataclass
from decimal import Decimal
from c21b_original_3m_raid_break_geometry import _source
from c37_native_adapted_bos_event_scanner import scan_original_3m_adapted,AdaptedClosedBreak
from c36_adapted_pivot_hypotheses import VARIANTS
from c36_adapted_slot_registry import ACADEMIC_CORE_ID

REACTION_VARIANTS=(
    "POST_CONFIRM_DIRECTIONAL_BODY_V1",
    "POST_CONFIRM_TWO_PROGRESSIVE_CLOSES_V1",
    "POST_CONFIRM_HALF_SWEEP_DISPLACEMENT_V1",
)

@dataclass(frozen=True)
class ReactionWitness:
    reaction_hypothesis_id:str
    bos_hypothesis_id:str
    symbol:str
    raid_fractal_center_ms:int
    original_bos_break_row_id:str
    bos_break_bar_start_ms:int
    eligible_prior_3m_bars:int
    condition_satisfied:bool
    first_confirmed_reaction_bar_start_ms:int|None
    first_confirmed_reaction_bar_closed_ms:int|None
    first_confirmed_native3m_row_id:str|None
    source_scope:str="ADAPTED_POST_1H_CONFIRM_PRE_BOS_ONLY"
    author_reaction_verified:bool=False
    author_bos_verified:bool=False
    paper_signal_allowed:bool=False
    orders:tuple=()
    trades:tuple=()
    readiness:str="NOT_TRADE_READY"

@dataclass(frozen=True)
class ReactionRouteReview:
    bos_hypothesis_id:str
    reaction_hypothesis_id:str
    total_bos_parent_contexts:int
    observed_with_prior_reaction:int
    observed_without_prior_reaction:int
    observations:tuple[ReactionWitness,...]
    readiness:str="NOT_TRADE_READY"
    orders:tuple=()
    trades:tuple=()

@dataclass(frozen=True)
class ReactionReview:
    symbol:str
    as_of_ms:int
    original_closed_3m_bars:int
    academic_core_id:str
    reaction_hypotheses:tuple[str,...]
    bos_hypotheses:tuple[str,...]
    routes:tuple[ReactionRouteReview,...]
    author_reaction_goldens:int=0
    author_bos_goldens:int=0
    trades:tuple=()
    orders:tuple=()
    readiness:str="NOT_TRADE_READY"

def _eligible_window(e,rows):
    if not isinstance(e,AdaptedClosedBreak):
        raise ValueError("C38_UNTRUSTED_ADAPTED_BOS_EVENT")
    if (e.status!="ADAPTED_RESEARCH_CLOSED_BREAK_NOT_AUTHOR_BOS" or
        e.author_bos_approved or e.paper_trade_allowed or e.orders or e.trades or
        e.side not in ("SHORT","LONG") or
        e.raid_fractal_kind!=("BSL" if e.side=="SHORT" else "SSL") or
        e.raid_confirmed_ms>e.break_bar_start_ms or
        e.break_bar_closed_known_ms!=e.break_bar_start_ms+180000):
        raise ValueError("C38_UNTRUSTED_READY_OR_BAD_BOS_EVENT")
    if len(rows)==0 or e.symbol!=rows[0].symbol:
        raise ValueError("C38_WRONG_NATIVE_PRICE_SOURCE_SYMBOL")
    bars=tuple(b for b in rows if
         b.start_ms>=e.raid_confirmed_ms and
         b.known_ms<=e.break_bar_start_ms)
    if any(b.known_ms>e.break_bar_start_ms or
           b.start_ms<e.raid_confirmed_ms for b in bars):
        raise ValueError("C38_LOOKAHEAD_WINDOW_CORRUPTED")
    # Reaction cannot borrow close/open of the actual breaking bar.
    if any(b.raw_id==e.break_original_native3m_row_id for b in bars):
        raise ValueError("C38_REACTION_CONTAINS_BOS_BREAK_CANDLE")
    return bars

def _reacted(e,bars,hypothesis):
    if hypothesis not in REACTION_VARIANTS:
        raise ValueError("C38_UNKNOWN_ADAPTED_REACTION")
    short=e.side=="SHORT"
    if hypothesis=="POST_CONFIRM_DIRECTIONAL_BODY_V1":
        return next((b for b in bars if (
            b.close<b.open if short else b.close>b.open)),None)
    if hypothesis=="POST_CONFIRM_TWO_PROGRESSIVE_CLOSES_V1":
        for a,b in zip(bars,bars[1:]):
            if (b.start_ms!=a.known_ms):continue
            # Both subsequent 3m closes progress in the BOS direction,
            # using the prior fully closed native 3m close.
            prior=bars[bars.index(a)-1] if bars.index(a)>0 else None
            if prior is None or a.start_ms!=prior.known_ms:continue
            if ((prior.close>a.close>b.close) if short else
                (prior.close<a.close<b.close)):
                return b
        return None
    try:
        level=Decimal(e.raid_level)
        extreme=Decimal(e.raid_extreme)
    except (ArithmeticError,ValueError) as exc:
        raise ValueError("C38_INVALID_RAID_SOURCE_PRICE") from exc
    if (not level.is_finite() or not extreme.is_finite() or
        level<=0 or extreme<=0 or
        (short and extreme<=level) or
        (not short and extreme>=level)):
        raise ValueError("C38_INVALID_RAID_SOURCE_PRICE")
    delta=abs(extreme-level)*Decimal("0.5")
    boundary=level-delta if short else level+delta
    return next((b for b in bars if (
        b.close<=boundary if short else b.close>=boundary)),None)

def classify_adapted_reaction(e,rows,hypothesis):
    if hypothesis not in REACTION_VARIANTS:
        raise ValueError("C38_UNKNOWN_ADAPTED_REACTION")
    bars=_eligible_window(e,rows)
    witness=_reacted(e,bars,hypothesis)
    if witness is not None and (witness.known_ms>e.break_bar_start_ms or
            witness.start_ms<e.raid_confirmed_ms):
        raise ValueError("C38_UNCLOSED_FUTURE_REACTION_WITNESS")
    return ReactionWitness(hypothesis,e.hypothesis_id,e.symbol,
        e.raid_fractal_center_ms,e.break_original_native3m_row_id,
        e.break_bar_start_ms,len(bars),witness is not None,
        witness.start_ms if witness else None,
        witness.known_ms if witness else None,
        witness.raw_id if witness else None)

def scan_adapted_reactions(source,*,as_of_ms):
    native=_source(source,as_of_ms)
    bos=scan_original_3m_adapted(source,as_of_ms=as_of_ms)
    if bos.academic_core_sha256!=ACADEMIC_CORE_ID:
        raise ValueError("C38_ACADEMIC_CORE_MUTATION")
    route_results=[]
    for br in bos.routes:
        if br.hypothesis_id not in VARIANTS:
            raise ValueError("C38_UNKNOWN_BOS_ADAPTATION")
        for reaction in REACTION_VARIANTS:
            obs=tuple(classify_adapted_reaction(e,native,reaction)
                      for e in br.events)
            yes=sum(x.condition_satisfied for x in obs)
            if any(x.paper_signal_allowed or x.author_reaction_verified or
                   x.author_bos_verified or x.orders or x.trades
                   for x in obs):
                raise ValueError("C38_FALSE_TRADE_OR_AUTHOR_PROMOTION")
            route_results.append(ReactionRouteReview(
                br.hypothesis_id,reaction,len(br.events),yes,
                len(obs)-yes,obs))
    if len(route_results)!=len(VARIANTS)*len(REACTION_VARIANTS):
        raise ValueError("C38_ROUTE_REACTION_MATRIX_INCOMPLETE")
    return ReactionReview(source.symbol,as_of_ms,len(native),ACADEMIC_CORE_ID,
        REACTION_VARIANTS,VARIANTS,tuple(route_results))

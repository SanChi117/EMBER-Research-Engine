"""C51: an authenticated Drive course image is NOT an author 2023 candle golden.

49 unique PNG sources in seven located academic folders, six visually
inspected. Most are schematics / nested desktop screenshots with no
reliably aligned exchange, ticker, timeframe, raw candle ID and timestamp.
This module prevents inventing positive training labels and stores safe
source candidate metadata only. It cannot approve trades.
"""
from dataclasses import dataclass
from pathlib import Path
import json,re
from c45_recovered_course_text_contract import recovered_text_claims

INVENTORY=Path(__file__).with_name("C51_RECOVERED_COURSE_VISUAL_FOLDER_INVENTORY_20261024.json")
FOLDERS={
    "POI","ENTRY_MODEL_LOGIC","IDM_ENTRY","BOS_ENTRY",
    "STRONG_HIGH_LOW","IDM_ELEMENT","SESSION_LIQUIDITY_CONTEXT"
}
BARRIERS=(
    "AUTHOR_EXAMPLE_CANDLE_CHART_PROVENANCE_UNVERIFIED",
    "SOURCE_SYMBOL_EXCHANGE_TIMEFRAME_NOT_RELIABLY_ALIGNED",
    "ORIGINAL_AUTHOR_2023_RAW_CANDLE_ID_NOT_ALIGNED",
    "SOURCE_TYPED_POI_FIRST_TEST_NOT_AUTHOR_VERIFIED",
    "COURSE_TRIGGER_VC_15M_ROUTE_AND_STRONG_HL_FTA_NOT_VERIFIED",
    "NO_INDEPENDENT_CHART_POSITIVE_NEGATIVE_GOLDEN_REVIEW",
)

@dataclass(frozen=True)
class VisualCandidate:
    id:str
    folder:str
    name:str
    mime_type:str
    url:str
    inspected:bool
    visually_observed_type:str
    candidate_only:bool=True
    positively_author_labelled:bool=False
    negatively_author_labelled:bool=False
    trade_ready:bool=False
    orders:tuple=()
    trades:tuple=()

@dataclass(frozen=True)
class VisualGate:
    total_image_candidates:int
    candidate:VisualCandidate
    source_image_available:bool
    image_seen_in_source_folder:bool
    author_positive_golden:bool
    author_negative_golden:bool
    matched_raw_candle_id:str|None
    blockers:tuple[str,...]=BARRIERS
    orders:tuple=()
    trades:tuple=()
    readiness:str="NOT_TRADE_READY"

def audited_inventory(path=INVENTORY):
    original_course_rules=recovered_text_claims()
    if len(original_course_rules)!=18:
        raise ValueError("C51_NOT_ALL_9_GDRIVE_COURSE_TEXT_SOURCES_PRESENT")
    o=json.loads(Path(path).read_text(encoding="utf8"))
    if (o.get("schema")!="EMBER_C51_RETRIEVED_ACADEMIC_DRIVE_VISUAL_SOURCE_INVENTORY_V1"
        or o.get("folder_count")!=7 or o.get("unique_direct_image_png_count")!=49
        or o.get("inspect_sample_count")!=6
        or o.get("coverage")!="SEVEN_GROUNDED_FOLDERS_ONLY_NOT_PROOF_ENTIRE_COURSE_ARCHIVED"
        or o.get("confirmed_author_candle_goldens")!=0
        or o.get("confirmed_positive_route_entry_goldens")!=0
        or o.get("confirmed_negative_route_entry_goldens")!=0
        or o.get("confirmed_original_market_source_chart_bindings")!=0
        or o.get("image_binary_copied_to_public_repository") is not False
        or o.get("orders") or o.get("trades") or o.get("readiness")!="NOT_TRADE_READY"):
        raise ValueError("C51_UNTRUSTED_VISUAL_AUTHOR_SOURCE_INVENTORY")
    images={}
    groups=set()
    for folder in o["folder_inventories"]:
        f=folder.get("name");fid=folder.get("folder_id")
        if (f not in FOLDERS or f in groups or
            not re.fullmatch(r"[A-Za-z0-9_-]{20,}",fid) or
            folder.get("folder_url")!="https://drive.google.com/drive/folders/"+fid or
            len(folder.get("files",()))>folder.get("total_direct_items",0)):
            raise ValueError("C51_UNTRUSTED_IMAGE_SOURCE_FOLDER")
        groups.add(f)
        for x in folder["files"]:
            ident=x.get("id")
            if (not isinstance(ident,str) or
                not re.fullmatch(r"[A-Za-z0-9_-]{20,}",ident) or
                ident in images or x.get("mime_type")!="image/png"
                or not x.get("name","").endswith(".png") or
                not x.get("drive_url","").startswith("https://drive.google.com/file/d/"+ident+"/view")):
                raise ValueError("C51_INVALID_OR_DUPLICATED_DRIVE_IMAGE_SOURCE")
            images[ident]=(f,x)
    if groups!=FOLDERS or len(images)!=49:
        raise ValueError("C51_IMAGE_COUNT_OR_FOLDER_COVERAGE_DRIFT")
    inspected={}
    for x in o["inspected_samples"]:
        ident=x.get("id")
        if (ident not in images or x.get("folder")!=images[ident][0]
            or ident in inspected or not x.get("inspected")
            or x.get("author_annotated_raw_candle_golden_verified") is not False
            or not x.get("visual_kind")):
            raise ValueError("C51_FORGED_VISUAL_INSPECTION_OR_CHART_GOLDEN")
        inspected[ident]=x["visual_kind"]
    if len(inspected)!=6:
        raise ValueError("C51_INSPECTED_SOURCE_SAMPLE_DRIFT")
    return images,inspected

def observe_visual_candidate(file_id,inventory_path=INVENTORY):
    sources,seen=audited_inventory(inventory_path)
    if file_id not in sources:
        raise ValueError("C51_IMAGE_NOT_IN_VERIFIED_OWNER_COURSE_FOLDERS")
    folder,x=sources[file_id]
    view=VisualCandidate(file_id,folder,x["name"],x["mime_type"],
        x["drive_url"],file_id in seen,
        seen.get(file_id,"FOUND_IN_OWNER_DRIVE_NOT_INDEPENDENTLY_VISUALLY_INSPECTED"))
    return VisualGate(len(sources),view,True,True,False,False,None)

def reject_unverified_golden_promotion(file_id,*,proposed_author_label,
                                     proposed_raw_candle_id=None,
                                     proposed_original_chart_year=None):
    """Block promotion: a claim/metadata alone cannot prove an author label."""
    result=observe_visual_candidate(file_id)
    if (proposed_author_label or proposed_raw_candle_id is not None
        or proposed_original_chart_year is not None):
        raise ValueError("C51_AUTHOR_CHART_GOLDEN_CANNOT_BE_ATTESTED_BY_METADATA_ONLY")
    return result

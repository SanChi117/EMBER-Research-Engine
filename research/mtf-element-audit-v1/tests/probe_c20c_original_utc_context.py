"""C20C independent 45-archive original source UTC diagnostics."""
import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for p in (ROOT/"d05",ROOT/"tools",ROOT/"tests"):sys.path.insert(0,str(p))
from probe_c16_32day_native_htf_sources import load_original,SYMS,DATES,STARTS
from probe_c20_original_5m_monthly_cross_15m import original_5m
from c16_c08_monthly_daily_htf_lineage import extended_32day_prefix,END
from c20_original_32day_native5m_lineage import reconcile_32day_native5m
from c20c_context_observations import review_calendar_context

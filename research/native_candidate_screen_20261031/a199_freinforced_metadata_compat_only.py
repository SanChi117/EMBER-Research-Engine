#!/usr/bin/env python3
"""A199 compat-only FReinforcedStrategy Freqtrade2026.4 metadata shim.
Original strategy is NOT engine-loadable: three IntParameter attributes lack
explicit buy/sell space. Frozen exact original source blob required. Change
only metadata annotations; preserve ALL defaults, indicator rules, exits, fees.
Patch is explicit and NOT an unmodified author source backtest.
"""
from pathlib import Path
import argparse,hashlib,json
PIN='11bfdde9fcecf772a2d223c88b9ee62bfd8737d3'
P={
'    adx_period = IntParameter(4, 24, default=14)':'    adx_period = IntParameter(4, 24, default=14, space="buy")',
'    ema_short_period = IntParameter(4, 24, default=8)':'    ema_short_period = IntParameter(4, 24, default=8, space="buy")',
'    ema_long_period = IntParameter(12, 175, default=21)':'    ema_long_period = IntParameter(12, 175, default=21, space="buy")',
}
def main():
    a=argparse.ArgumentParser();a.add_argument("source");a.add_argument("target")
    a=a.parse_args()
    src=Path(a.source).read_bytes()
    hash=hashlib.sha1(b"blob "+str(len(src)).encode()+b"\0"+src).hexdigest()
    assert hash==PIN,("original source hash mismatch",hash)
    t=src.decode()
    for before,after in P.items():
        assert t.count(before)==1,(before,t.count(before))
        assert t.count(after)==0
        t=t.replace(before,after)
    assert len(P)==3
    dst=Path(a.target);dst.parent.mkdir(parents=True,exist_ok=True)
    dst.write_text(t)
    dest=dst.read_bytes()
    diff=hashlib.sha256(dest).hexdigest()
    print("A199_COMPAT_ONLY_THREE_INT_PARAMETER_SPACE_ANNOTATIONS_PASS",json.dumps(
      {"original_git_blob":PIN,"patched_sha256":diff,"patch_only_metadata":P,
       "trading_logic_source_byte_identical_except_these_3":True}),flush=True)
if __name__=="__main__":main()

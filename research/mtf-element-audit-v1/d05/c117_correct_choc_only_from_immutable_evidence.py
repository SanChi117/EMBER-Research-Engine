#!/usr/bin/env python3
"""C117-A181 correction of a proven accounting error, WITHOUT reselecting events.

Original C117 publication incorrectly counted non-CHoCH C_NO_CHoCH trades
as if they belonged to T policy. Preserve the published evidence and its
original hashes. Recompute exactly the precommitted T-only policy using
its own frozen per-event event ledger and original 8-arm random controls.
No new provider reads and no strategy parameter changes.
"""
import argparse,copy,hashlib,json
from pathlib import Path
import c117_random_clock_4h_parent_canonical1m as c117

class CorrectionError(ValueError):pass
SOURCE="C117_SUMMARY.json"

def check_original_receipt(folder,filename,expected_sha):
    data=(folder/filename).read_bytes()
    if hashlib.sha256(data).hexdigest()!=expected_sha:
        raise CorrectionError("ORIGINAL_LEDGER_HASH_CHANGED")
    return json.loads(data)

def recompute(folder):
    c117.frozen()
    base=(folder/SOURCE).read_bytes()
    base_sha=hashlib.sha256(base).hexdigest()
    manifest=json.loads(base)
    if (manifest["original_1m_zip_total"]!=1344 or
        manifest["original_1m_bar_total"]!=1935360 or
        manifest["derived3m_bars_total"]!=645120 or
        manifest["derived5m_bars_total"]!=387072 or
        set(manifest["window_receipts"])!={"WIN_A","WIN_B"}):
        raise CorrectionError("ORIGINAL_SOURCES_NOT_PRECOMMITTED")
    result={}
    for window in c117.WINDOWS:
        name=window[0]
        receipt=manifest["window_receipts"][name]
        ledger=check_original_receipt(folder,receipt["filename"],receipt["sha256"])
        if (ledger["window"]!=name or
            ledger["original_1m_zip_count"]!=672 or
            len(ledger["original_1m_provider_zip_receipts"])!=672 or
            len(ledger["one_source_derived_15m_parity"])!=12):
            raise CorrectionError("ORIGINAL_PROVIDER_LINEAGE_WRONG")
        if not all(x["provider_checksum_verified"] and x["source_original_interval"]=="1m"
                   for x in ledger["original_1m_provider_zip_receipts"]):
            raise CorrectionError("ORIGINAL_PROVIDER_CHECKSUM_NOT_ATTESTED")
        original_events=ledger["same_4h_parent_all_touches_ITT"]
        if (len(original_events)!=ledger["cohort"]["initial_touch_eligible_events"] or
            len(original_events)!=ledger["C117_precommitted_random_clock_gate"]["all_touch_n"]):
            raise CorrectionError("ORIGINAL_EVENT_DENOMINATOR_CHANGED")
        out=copy.deepcopy(ledger)
        events=out["same_4h_parent_all_touches_ITT"]
        bugged_controls=0
        for e in events:
            if len(e["random"]["choices"])!=8 or len(e["random"]["offsets"])!=8:
                raise CorrectionError("RANDOM_CLOCK_POLICY_INCOMPLETE")
            if e["treatment"]=="C_NO_CHoCH" and e["t_trade"] is not None:
                bugged_controls+=1
            normalized=c117.t_policy_trade({"treatment":e["treatment"],"trade":e["t_trade"]})
            e["t_trade"]=normalized
            e["T_R25"]=c117.engine.net_r(normalized,25)
            e["T_R40"]=c117.engine.net_r(normalized,40)
            e["delta_T_minus_R_25"]=e["T_R25"]-e["R_avg_R25"]
            e["delta_T_minus_R_40"]=e["T_R40"]-e["R_avg_R40"]
        if any(x["t_trade"] is not None for x in events if x["treatment"]!="T_CHoCH"):
            raise CorrectionError("NON_CHOCH_TRADE_NOT_EXCLUDED")
        baseline={
            "scores":ledger["C114_observational_original_scores"],
            "portfolio":ledger["C117_precommitted_random_clock_gate"]["T_portfolio_dd"]}
        before_check=c117.engine.score([{"trade":e["t_trade"]} for e in events],25)
        print(json.dumps({"reconciliation_window":name,
            "corrected_CHoCH_count":sum(e["treatment"]=="T_CHoCH" for e in events),
            "corrected_CHoCH_fills":sum(e["t_trade"] is not None for e in events),
            "prior_non_CHOCH_misclassified":bugged_controls,
            "recomputed_score":before_check,
            "frozen_C114_score":baseline["scores"]["T_ALL"]["25"]},sort_keys=True))
        gate=c117.summary_scores(events,window,baseline)
        if gate["T_policy_25bps"]["fills"]!=baseline["scores"]["T_ALL"]["25"]["fills"]:
            raise CorrectionError("FROZEN_C114_TREATMENT_FILLS_DIFFER")
        out["C117_precommitted_random_clock_gate"]=gate
        out["source_original_economic_ledger_sha256"]=receipt["sha256"]
        out["corrected_included_no_choch_trades"]=bugged_controls
        out["correction_scope"]="CHoCH_POLICY_T_ONLY_ZEROES_C_NO_CHOCH_NO_FUTURE_OUTCOMES_ALTERED"
        payload=(json.dumps(out,indent=2,sort_keys=True,ensure_ascii=False)+"\n").encode()
        newfile=f"C117_{name}_CORRECTED_T_ONLY_VS_UNCHANGED_RANDOM_8.json"
        (folder/newfile).write_bytes(payload)
        result[name]={
            "file":newfile,"sha256":hashlib.sha256(payload).hexdigest(),
            "bytes":len(payload),"frozen_original_sha256":receipt["sha256"],
            "controls_misclassified_in_prior_t_policy":bugged_controls,
            "gate":gate,
            "cohort":ledger["cohort"]}
    summary={
        "schema":"C117_A181_CORRECTED_ORIGINAL_EVIDENCE_T_ONLY_POLICY",
        "original_summary_sha256":base_sha,
        "original_c114_core_sha256":c117.FROZEN_C114,
        "source_original_1m_archives":1344,
        "historical_native1m_original_bars":1935360,
        "derived3m_bars":645120,"derived5m_bars":387072,
        "original_pub_bug":"NON_CHOCH_CONTROL_TRADES_ACCIDENTALLY_COUNTED_IN_CHoCH_T_POLICY",
        "new_provider_download":False,"new_trading_hypothesis":False,
        "new_risk_stop_target_parameters":False,
        "random_8_branch_trades_unchanged":True,
        "original_published_buggy_ledgers_preserved":True,
        "both_windows_historical_screen_pass":all(
            a["gate"]["state"]=="HISTORICAL_SCREEN_PASS_PAPER_ONLY" for a in result.values()),
        "windows":result,"paper_only":True,"live_approved":False}
    path=folder/"C117_A181_CORRECTED_SUMMARY.json"
    b=(json.dumps(summary,indent=2,sort_keys=True,ensure_ascii=False)+"\n").encode()
    path.write_bytes(b)
    print(json.dumps({"corrected_summary_sha256":hashlib.sha256(b).hexdigest(),
                      "original_summary_sha256":base_sha,
                      "windows":{name:{
                           "state":v["gate"]["state"],
                           "original_controls_misclassified":v["controls_misclassified_in_prior_t_policy"],
                           "T_25":v["gate"]["T_policy_25bps"],
                           "R_mean_total_net25":v["gate"]["R_mean_total_net25"],
                           "bootstrap":v["gate"]["cluster"],
                           "dd":v["gate"]["T_portfolio_dd"]["dd_adverse_wick_pct_upper_bound"]}
                       for name,v in result.items()},
                      "paper_only":True,"live_approved":False},ensure_ascii=False,sort_keys=True))
    return summary

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--folder",type=Path,required=True)
    args=p.parse_args()
    recompute(args.folder)

#!/usr/bin/env python3
"""A197 independent final verification of three separate genuine immutable CI artifacts:
original official Freqtrade bias classes, original author 2025 cross-regime 5m,
and ONE-LINE author-callback causal 2026 5m test copy vs A196 original ZIP.
Fail closed if any native ZIP, empirical summary, SHA or source missing.
Generate a factual Russian report, no extrapolation to live.
"""
from __future__ import annotations
import argparse,json,hashlib,zipfile
from pathlib import Path
PAIRS=("BTC","ETH","SOL","LINK")
FEES=("5","12p5")
STRATEGY="VideoDoubleMaFuturesStrategy"
BLOB="22ca6588bbd056e671783f676f1a4010cbfc1bb6"
def load(p):
    assert p.is_file() and zipfile.is_zipfile(p),("missing_real_zip",str(p))
    b=p.read_bytes()
    with zipfile.ZipFile(p) as z:
        names=[n for n in z.namelist() if n.endswith(".json") and "_config" not in n]
        assert len(names)==1,names
        d=json.loads(z.read(names[0]))["strategy"][STRATEGY]
    assert len(d["trades"])==d["total_trades"]
    assert abs(d['profit_total_abs']-sum(t['profit_abs'] for t in d['trades']))<.001
    return d,hashlib.sha256(b).hexdigest()
def f(n):return f"{n:+.2f}%" if n>=0 else f"{n:.2f}%"
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--bias",required=True)
    ap.add_argument("--regime",required=True)
    ap.add_argument("--causal",required=True)
    ap.add_argument("--output-dir",required=True)
    a=ap.parse_args()
    bias=Path(a.bias);regime=Path(a.regime);causal=Path(a.causal)
    q=Path(a.output_dir);q.mkdir(parents=True,exist_ok=True)
    official=json.loads((bias/"A197_FOUR_OFFICIAL_FREQTRADE_METHOD_RESULTS.json").read_text())
    alt=json.loads((regime/"A197_2025_NATIVE_ALTERNATE_MACHINE.json").read_text())
    fix=json.loads((causal/"A197_CAUSAL_FIXED_VS_ORIGINAL_5M_MACHINE.json").read_text())
    assert official["schema"]=="EMBER_A197_ORIGINAL_DOUBLEMA_4_OFFICIAL_BIAS_METHOD_RUNS"
    assert official["freqtrade"]=="2026.4"
    assert official["any_official_entry_or_indicator_bias"] is False
    assert alt["source_original_blob"]==BLOB and fix["original_source_blob"]==BLOB
    assert alt["not_genuine_post_publication_OOS"] is True
    assert alt["pre_registered_gate_pass_2_of_3"]==sum(alt["pre_registered_gate"].values())>=2
    assert set(alt["outcomes"])==set(PAIRS) and set(fix["outcomes"])==set(PAIRS)
    for mode in ('lookahead','recursive'):
        for p in ('ETH','SOL'):
            x=official["lookahead_and_recursive"][f'{mode}-{p}']
            assert x['mode']==mode and x['pair']==f'{p}/USDT:USDT'
            if mode=='lookahead':
                assert x['analyzed_signals']==10 and not x['failed_bias_check']
                assert not x['has_bias'] and not x['biased_indicator_names']
            else:
                assert len(x['startup_candles_tested'])>=4 and x['indicators_with_recursive_variation']>0
    native_shas={}
    for sym in PAIRS:
        assert set(alt['outcomes'][sym])==set(FEES)
        assert set(fix['outcomes'][sym])==set(FEES)
        for fee in FEES:
            stat=alt['outcomes'][sym][fee]
            p=regime/f"2025-{sym}-fee{fee}-5m.zip"
            d,sha=load(p)
            assert sha==stat['sha256_native_zip']
            assert abs(d['profit_total']*100-stat['net_pct'])<.0001
            assert abs(d['profit_factor']-stat['PF'])<.0001
            assert abs(d['profit_total_abs']-stat['PnL_USDT'])<.001
            native_shas[f"2025_{sym}_fee{fee}"]=sha
            updated=fix['outcomes'][sym][fee]
            p=causal/f"causal-{sym}-fee{fee}.zip"
            d,sha=load(p)
            assert sha==updated['sha256_causal_native_zip']
            assert abs(d['profit_total']*100-updated['causal_only_boundary_fix']['return_pct'])<.0001
            assert abs(d['profit_factor']-updated['causal_only_boundary_fix']['pf'])<.0001
            native_shas[f"2026_caused_{sym}_fee{fee}"]=sha
    src=json.loads((regime/"data/A197_2025_AUTHENTIC_SOURCE_SHA_MANIFEST.json").read_text())
    assert len(src['sources'])==4
    for sym in PAIRS:
        data=src["counts"][sym+"USDT"]
        assert data['h1']==8760 and data['5m']==79200 and data['mark1h']==8760
        assert len(src['sources'][sym+"USDT"])>=45
        assert all(len(rec['zip_sha256'])==64 for rec in src['sources'][sym+"USDT"].values())
    risk_gate=bool(alt['pre_registered_gate_pass_2_of_3']
                   and not fix['any_economic_differences']
                   and not official['any_official_entry_or_indicator_bias'])
    # Intentionally NEVER infer readiness from 2025 in-sample author history,
    # nor from prior A196 economic FAILED. Gate to live stays false.
    verified={'schema':'EMBER_A197_INDEPENDENT_THREE_IMMUTABLE_ARTIFACT_FINAL_AUDIT',
      'engine':'freqtrade==2026.4','original_author_git_blob':BLOB,
      'official_lookahead_ETH_SOL_signals':20,
      'official_lookahead_detected_bias':False,
      'recursive_variants_ETH':official['lookahead_and_recursive']['recursive-ETH']['indicators_with_recursive_variation'],
      'recursive_variants_SOL':official['lookahead_and_recursive']['recursive-SOL']['indicators_with_recursive_variation'],
      'alternate_2025_original_PnL':alt['outcomes'],
      'alternate_2025_frozen_gate':alt['pre_registered_gate'],
      'alternate_2025_pass_2_of_3':alt['pre_registered_gate_pass_2_of_3'],
      'causal_2026_corrected_vs_original_5m':fix['outcomes'],
      'causal_boundary_changes_economics':fix['any_economic_differences'],
      'research_narrow_gate':risk_gate,'LIVE_ALLOWED':False,'AUTO_PAPER_ALLOWED':False,
      'original_native_zip_sha256':native_shas,
      'critical_caveats':['Original 2025 history is earlier than author published strategy; cannot be labeled external OOS.',
           'A196 old full-stake economic gate was FAILED; even 2025 2026 earnings do not authorize small deposit use.',
           'One-line patched causal test copy is NOT the original author code and changes only time boundary.',
           'Official 10-trade lookahead tests do NOT guarantee all callbacks are causally safe.',
           'Original 2x near full margin is not 1% account risk; no live or PAPER order placed.']}
    (q/'A197_ALL_THREE_INDEPENDENT_SOURCE_RECEIPTS_MACHINE.json').write_text(json.dumps(verified,indent=2,ensure_ascii=False)+'\n')
    (q/'A197_2025_REAL_DATA_SOURCE_SHA_VERIFIED.json').write_text(json.dumps(src,indent=2)+'\n')
    (q/'A197_NATIVE_16_ZIP_SHA_VERIFIED.json').write_text(json.dumps(native_shas,indent=2)+'\n')
    text=(q/'A197_BIAS_AND_2025_RESULTS_RU.md').read_text().replace('**Статус:** результаты не внесены до завершения исходных тестов и проверки Freqtrade ZIP receipt.', '**Статус:** нативные результаты проверены по всем восьми оригинальным ZIP сделок. Подробности ниже.')
    part=[]
    part.append("\n## A197b — нативный исторический режим 2025: фактические результаты\n")
    part.append("Интервал **01.04.2025—31.12.2025**, 275 календарных дней. Независимые данные Binance USD-M с 5m детализацией, реальными funding и mark; исходные сделки автора не менялись. **Но этот период предшествует публикации стратегии и мог входить в её настройку, поэтому НЕ подлинный вневыборочный период.**\n")
    part.append("| Монета | Сделок, комиссия 0.05%/сторона | 5bps: net / PF / DD | 0.125%/сторона: net / PF / DD | TOP3 как % всех выигрышных сделок (5bps) |")
    part.append("|---|---:|---|---|---:|")
    for s in PAIRS:
        v=alt['outcomes'][s]
        one=v['5'];two=v['12p5']
        part.append(f"| {s} | {one['n']} | **{f(one['net_pct'])}** / {one['PF']:.2f} / {one['DD_pct']:.2f}% | **{f(two['net_pct'])}** / {two['PF']:.2f} / {two['DD_pct']:.2f}% | {100*one['top3_fraction_all_wins']:.1f}% |" if one['top3_fraction_all_wins'] is not None else f"| {s} | {one['n']} | {f(one['net_pct'])} / {one['PF']:.2f} / {one['DD_pct']:.2f}% | {f(two['net_pct'])} / {two['PF']:.2f} / {two['DD_pct']:.2f}% | no winning trades |")
    part.append(f"\nПредварительно замороженный порог 2025: {sum(alt['pre_registered_gate'].values())} из 3 ETH/SOL/LINK; требование 2/3, итог **{'PASS' if alt['pre_registered_gate_pass_2_of_3'] else 'FAIL'}**. Даже PASS не возмещает A196 gate FAIL на 2026 и известные риски.\n")
    part.append("## A197c — исходник против однострочного исправления будущей свечи, настоящие 5m\n")
    part.append("Это **чистый контроль причинности**, не оптимизация. Мы сравнили 8 native-архивов оригинала A196 и 8 native-архивов тестовой копии с единственным изменением: `dates <= candle_time` → `dates < candle_time.floor('h')`. Ни один EMA/SL/TP/порог/фильтр не изменён.\n")
    part.append("| Монета | 5bps исходник | 5bps после каузальной поправки | 12.5bps исходник | 12.5bps после поправки | Изменено общих сделок (5bps) |")
    part.append("|---|---:|---:|---:|---:|---:|")
    for s in PAIRS:
        v=fix['outcomes'][s]
        part.append(f"| {s} | {f(v['5']['original']['return_pct'])} | **{f(v['5']['causal_only_boundary_fix']['return_pct'])}** | {f(v['12p5']['original']['return_pct'])} | **{f(v['12p5']['causal_only_boundary_fix']['return_pct'])}** | {v['5']['changed_trade_receipts']['changed_common_trades']} |")
    part.append(f"\nЭкономический эффект единственной причинной правки: **{'ЕСТЬ' if fix['any_economic_differences'] else 'НЕ ОБНАРУЖЕН на проверенном окне'}**. Если есть, показатели исходного A196 **нельзя** применять к причинно-корректной модели без поправок; при отсутствии эффекта всё равно не доказана generalization.\n")
    part.append("## Итог\n")
    part.append(f"Техническое исследование завершено: 4 официальных нативных Freqtrade анализа, 8 настоящих 5m сделок 2025 и 8 настоящих 5m causality-тестов 2026. Пререгистрированный узкий gate {'PASS' if risk_gate else 'FAIL'}; **решение для живой торговли и автономных PAPER-ордеров — НЕ ДОПУСКАТЬ**. Нужны самостоятельные новые postpublication и live paper доказательства, прозрачная оценка риска 1% на весь счёт, действительное моделирование спреда и очереди лимитов; исходная частота недостаточна для 3–5 сделок ежедневно.\n")
    part.append("Никаких изменений работающей системы, планировщиков или ордеров не было.\n")
    (q/'A197_BIAS_AND_2025_RESULTS_RU.md').write_text(text.rstrip()+'\n\n'+'\n'.join(part))
    print('A197_THREE_ORIGINAL_NATIVE_AUDITS_16_ZIP_RECEIPTS_2025_PLUS_2026_AND_OFFICIAL_BIAS_VERIFIED')
    print(json.dumps({'2025':{s:(alt['outcomes'][s]['5']['net_pct'],alt['outcomes'][s]['12p5']['net_pct']) for s in PAIRS},
         'causal':{s:(fix['outcomes'][s]['5']['causal_only_boundary_fix']['return_pct'],fix['outcomes'][s]['12p5']['causal_only_boundary_fix']['return_pct']) for s in PAIRS},
         '2025_gate':alt['pre_registered_gate'],'causal_econ_changed':fix['any_economic_differences'],'research_gate':risk_gate},ensure_ascii=False,indent=2))
if __name__=="__main__":main()
